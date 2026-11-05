"""
OLA Ride Insights - Data Cleaning & Preprocessing
--------------------------------------------------
Reads the raw OLA_DataSet.xlsx ("July" sheet), cleans it, engineers features,
and writes:
    data/ola_rides_clean.csv.gz   -> used by the Streamlit app & Power BI
    data/ola.db                   -> SQLite database (table: ola_rides)

Run:  python data_prep.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
RAW_XLSX = BASE_DIR / "data" / "OLA_DataSet.xlsx"
CLEAN_CSV = BASE_DIR / "data" / "ola_rides_clean.csv.gz"
SQLITE_DB = BASE_DIR / "data" / "ola.db"
TABLE = "ola_rides"

TEXT_COLS = [
    "Booking_ID", "Booking_Status", "Customer_ID", "Vehicle_Type",
    "Pickup_Location", "Drop_Location", "Canceled_Rides_by_Customer",
    "Canceled_Rides_by_Driver", "Incomplete_Rides", "Incomplete_Rides_Reason",
    "Payment_Method", "Vehicle_Image_URL",
]


def time_slot(hour: int) -> str:
    if 5 <= hour < 12:
        return "Morning (5-12)"
    if 12 <= hour < 17:
        return "Afternoon (12-17)"
    if 17 <= hour < 21:
        return "Evening (17-21)"
    return "Night (21-5)"


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()

    # 1. Standardise column names ------------------------------------------
    df = df.rename(columns={"Vehicle Images": "Vehicle_Image_URL"})

    # 2. Trim whitespace & turn empty strings into proper nulls --------------
    for c in TEXT_COLS:
        df[c] = df[c].astype("string").str.strip().replace({"": pd.NA})

    # 3. Remove exact duplicates / duplicate booking IDs ---------------------
    df = df.drop_duplicates().drop_duplicates(subset="Booking_ID", keep="first")

    # 4. Date-time handling (the 'Date' column already carries the time) -----
    df["Booking_DateTime"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Booking_DateTime"])
    df["Ride_Date"] = df["Booking_DateTime"].dt.date.astype(str)
    df["Ride_Time"] = df["Booking_DateTime"].dt.strftime("%H:%M:%S")
    df["Ride_Hour"] = df["Booking_DateTime"].dt.hour
    df["Day_of_Month"] = df["Booking_DateTime"].dt.day
    df["Day_Name"] = df["Booking_DateTime"].dt.day_name()
    df["Week_No"] = df["Booking_DateTime"].dt.isocalendar().week.astype(int)
    df["Is_Weekend"] = df["Day_Name"].isin(["Saturday", "Sunday"]).astype(int)
    df["Time_Slot"] = df["Ride_Hour"].apply(time_slot)
    df = df.drop(columns=["Date", "Time"])

    # 5. Numeric types --------------------------------------------------------
    for c in ["V_TAT", "C_TAT", "Driver_Ratings", "Customer_Rating"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["Booking_Value", "Ride_Distance"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # Ratings must sit in 1-5; anything else is treated as missing
    for c in ["Driver_Ratings", "Customer_Rating"]:
        df.loc[~df[c].between(1, 5), c] = np.nan

    # 6. Business-logic consistency ------------------------------------------
    # Non-successful bookings have no payment / ratings / TAT -> keep NULL,
    # but give categorical blanks an explicit label for dashboards.
    is_success = df["Booking_Status"].eq("Success")
    df["Payment_Method"] = df["Payment_Method"].where(is_success, pd.NA)
    df["Incomplete_Rides"] = df["Incomplete_Rides"].fillna("Not Applicable")

    # 7. Derived features -----------------------------------------------------
    df["Is_Success"] = is_success.astype(int)
    df["Is_Completed"] = (is_success & df["Incomplete_Rides"].eq("No")).astype(int)
    df["Cancelled_By"] = np.select(
        [df["Booking_Status"].eq("Canceled by Customer"),
         df["Booking_Status"].eq("Canceled by Driver")],
        ["Customer", "Driver"], default="Not Cancelled")
    df["Cancellation_Reason"] = (
        df["Canceled_Rides_by_Customer"].fillna(df["Canceled_Rides_by_Driver"])
    )
    # Realised revenue = only rides that actually happened
    df["Revenue"] = np.where(is_success, df["Booking_Value"], 0)
    df["Fare_per_KM"] = np.where(
        is_success & (df["Ride_Distance"] > 0),
        (df["Booking_Value"] / df["Ride_Distance"].replace(0, np.nan)).round(2),
        np.nan)
    df["Distance_Band"] = pd.cut(
        df["Ride_Distance"], bins=[-1, 0, 5, 15, 30, 50],
        labels=["0 km (no ride)", "1-5 km", "6-15 km", "16-30 km", "31-50 km"]
    ).astype(str)
    df["Route"] = df["Pickup_Location"] + " -> " + df["Drop_Location"]

    # 8. Anomaly flag (fraud / data-quality use case) -------------------------
    #    Successful rides whose fare-per-km is extreme (IQR rule, k=3)
    fpk = df["Fare_per_KM"].dropna()
    q1, q3 = fpk.quantile([0.25, 0.75])
    upper = q3 + 3 * (q3 - q1)
    df["Is_Fare_Anomaly"] = (df["Fare_per_KM"] > upper).astype(int)
    df["Is_Same_Pickup_Drop"] = (df["Pickup_Location"] == df["Drop_Location"]).astype(int)

    order = [
        "Booking_ID", "Booking_DateTime", "Ride_Date", "Ride_Time", "Ride_Hour",
        "Day_of_Month", "Day_Name", "Week_No", "Is_Weekend", "Time_Slot",
        "Booking_Status", "Is_Success", "Is_Completed", "Customer_ID",
        "Vehicle_Type", "Pickup_Location", "Drop_Location", "Route",
        "V_TAT", "C_TAT", "Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver",
        "Cancelled_By", "Cancellation_Reason", "Incomplete_Rides",
        "Incomplete_Rides_Reason", "Booking_Value", "Revenue", "Payment_Method",
        "Ride_Distance", "Distance_Band", "Fare_per_KM", "Driver_Ratings",
        "Customer_Rating", "Is_Fare_Anomaly", "Is_Same_Pickup_Drop",
        "Vehicle_Image_URL",
    ]
    return df[order].sort_values("Booking_DateTime").reset_index(drop=True)


def quality_report(raw: pd.DataFrame, df: pd.DataFrame) -> None:
    print(f"Raw rows: {len(raw):,} | Clean rows: {len(df):,}")
    print(f"Date range: {df['Ride_Date'].min()} -> {df['Ride_Date'].max()}")
    print("\nNull counts (clean):")
    print(df.isna().sum()[lambda s: s > 0].to_string())
    print("\nBooking status mix:")
    print(df["Booking_Status"].value_counts().to_string())


def to_sqlite(df: pd.DataFrame, db_path: Path = SQLITE_DB) -> None:
    out = df.copy()
    out["Booking_DateTime"] = out["Booking_DateTime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(db_path) as con:
        out.to_sql(TABLE, con, if_exists="replace", index=False)
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_status ON {TABLE}(Booking_Status)")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_vehicle ON {TABLE}(Vehicle_Type)")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_customer ON {TABLE}(Customer_ID)")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_date ON {TABLE}(Ride_Date)")


def main() -> None:
    raw = pd.read_excel(RAW_XLSX, sheet_name="July")
    df = clean(raw)
    quality_report(raw, df)
    df.to_csv(CLEAN_CSV, index=False, compression="gzip")
    to_sqlite(df)
    print(f"\nSaved -> {CLEAN_CSV.name} and {SQLITE_DB.name} (table '{TABLE}')")


if __name__ == "__main__":
    main()
