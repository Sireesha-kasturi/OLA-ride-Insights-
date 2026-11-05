"""Generates sql/ola_queries.sql (MySQL) from queries.py so both stay in sync."""
from pathlib import Path
from queries import QUERIES

HEADER = """-- =============================================================
-- OLA RIDE INSIGHTS  |  SQL Queries (MySQL 8)
-- Table is loaded from data/ola_rides_clean.csv (output of data_prep.py)
-- =============================================================
CREATE DATABASE IF NOT EXISTS ola;
USE ola;

DROP TABLE IF EXISTS ola_rides;
CREATE TABLE ola_rides (
    Booking_ID                 VARCHAR(20) PRIMARY KEY,
    Booking_DateTime           DATETIME,
    Ride_Date                  DATE,
    Ride_Time                  TIME,
    Ride_Hour                  TINYINT,
    Day_of_Month               TINYINT,
    Day_Name                   VARCHAR(12),
    Week_No                    TINYINT,
    Is_Weekend                 TINYINT,
    Time_Slot                  VARCHAR(20),
    Booking_Status             VARCHAR(30),
    Is_Success                 TINYINT,
    Is_Completed               TINYINT,
    Customer_ID                VARCHAR(20),
    Vehicle_Type               VARCHAR(20),
    Pickup_Location            VARCHAR(60),
    Drop_Location              VARCHAR(60),
    Route                      VARCHAR(130),
    V_TAT                      DECIMAL(8,1) NULL,
    C_TAT                      DECIMAL(8,1) NULL,
    Canceled_Rides_by_Customer VARCHAR(80) NULL,
    Canceled_Rides_by_Driver   VARCHAR(80) NULL,
    Cancelled_By               VARCHAR(20),
    Cancellation_Reason        VARCHAR(80) NULL,
    Incomplete_Rides           VARCHAR(20),
    Incomplete_Rides_Reason    VARCHAR(40) NULL,
    Booking_Value              INT,
    Revenue                    INT,
    Payment_Method             VARCHAR(20) NULL,
    Ride_Distance              INT,
    Distance_Band              VARCHAR(20),
    Fare_per_KM                DECIMAL(10,2) NULL,
    Driver_Ratings             DECIMAL(3,1) NULL,
    Customer_Rating            DECIMAL(3,1) NULL,
    Is_Fare_Anomaly            TINYINT,
    Is_Same_Pickup_Drop        TINYINT,
    Vehicle_Image_URL          VARCHAR(200),
    INDEX idx_status (Booking_Status),
    INDEX idx_vehicle (Vehicle_Type),
    INDEX idx_customer (Customer_ID),
    INDEX idx_date (Ride_Date)
);

-- Unzip data/ola_rides_clean.csv.gz first, then:
-- (enable local_infile on server & client, or use MySQL Workbench Import Wizard)
LOAD DATA LOCAL INFILE 'data/ola_rides_clean.csv'
INTO TABLE ola_rides
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\\n'
IGNORE 1 ROWS
(Booking_ID, Booking_DateTime, Ride_Date, Ride_Time, Ride_Hour, Day_of_Month,
 Day_Name, Week_No, Is_Weekend, Time_Slot, Booking_Status, Is_Success,
 Is_Completed, Customer_ID, Vehicle_Type, Pickup_Location, Drop_Location, Route,
 @V_TAT, @C_TAT, @cc, @cd, Cancelled_By, @cr, Incomplete_Rides, @ir,
 Booking_Value, Revenue, @pm, Ride_Distance, Distance_Band, @fpk, @dr, @cr2,
 Is_Fare_Anomaly, Is_Same_Pickup_Drop, Vehicle_Image_URL)
SET V_TAT = NULLIF(@V_TAT,''), C_TAT = NULLIF(@C_TAT,''),
    Canceled_Rides_by_Customer = NULLIF(@cc,''), Canceled_Rides_by_Driver = NULLIF(@cd,''),
    Cancellation_Reason = NULLIF(@cr,''), Incomplete_Rides_Reason = NULLIF(@ir,''),
    Payment_Method = NULLIF(@pm,''), Fare_per_KM = NULLIF(@fpk,''),
    Driver_Ratings = NULLIF(@dr,''), Customer_Rating = NULLIF(@cr2,'');

-- =============================================================
-- 10 PROJECT QUESTIONS  (each saved as a VIEW for Power BI / Streamlit)
-- =============================================================
"""

out = [HEADER]
for title, q in QUERIES.items():
    body = q["sql"].strip().rstrip(";")
    out.append(f"-- {title}\nCREATE OR REPLACE VIEW {q['view']} AS\n{body};\n"
               f"SELECT * FROM {q['view']};\n")

Path("sql").mkdir(exist_ok=True)
Path("sql/ola_queries.sql").write_text("\n".join(out))
print("written sql/ola_queries.sql")
