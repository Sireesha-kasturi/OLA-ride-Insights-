# 🚖 OLA Ride Insights

Ride-sharing analytics on **103,024 OLA bookings (Bengaluru, July 2024)**:
data cleaning → EDA → SQL → Power BI → Streamlit web app.

## Project structure
```
ola_ride_insights/
├── app.py                      # Streamlit app (entry point for deployment)
├── data_prep.py                # Cleaning + feature engineering -> CSV + SQLite
├── queries.py                  # The 10 SQL questions (single source of truth)
├── build_sql_file.py           # Regenerates sql/ola_queries.sql from queries.py
├── sql/ola_queries.sql         # MySQL script: table, load, 10 queries as VIEWs
├── notebooks/01_cleaning_eda_sql.ipynb   # EDA with Matplotlib/Seaborn (executed)
├── data/OLA_DataSet.xlsx       # Raw data
├── data/ola_rides_clean.csv.gz # Cleaned data (used by app & Power BI)
├── .streamlit/config.toml      # Theme
├── .streamlit/secrets.toml.example
└── requirements.txt
```

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python data_prep.py          # re-creates data/ola_rides_clean.csv.gz and data/ola.db
streamlit run app.py         # opens http://localhost:8501
```

## Deploy on Streamlit Community Cloud (free)
1. Create a GitHub repo and push this folder:
   ```bash
   git init && git add . && git commit -m "OLA Ride Insights"
   git branch -M main
   git remote add origin https://github.com/<your-user>/ola-ride-insights.git
   git push -u origin main
   ```
2. Go to **share.streamlit.io** → *Create app* → pick the repo, branch `main`, main file `app.py` → **Deploy**.
3. (Optional) *App settings → Secrets* → paste
   `POWERBI_EMBED_URL = "https://app.powerbi.com/view?r=..."` so the Power BI page loads automatically.

The app reads `data/ola_rides_clean.csv.gz` (4.5 MB) and builds an in-memory SQLite DB at start-up,
so no external database is needed in the cloud.

## App pages
| Page | What it shows |
|---|---|
| Overview | 8 KPIs + daily volume + status donut |
| Overall | Ride volume over time (daily / hourly / weekday), booking status breakdown |
| Vehicle Type | Top 5 vehicle types by ride distance, avg distance, revenue, ratings |
| Revenue | Revenue by payment method, top 5 customers by value, ride distance per day |
| Cancellation | Customer & driver cancellation reasons, incomplete reasons, cancel-rate by hour |
| Ratings | Driver / customer rating distributions, customer vs driver ratings |
| SQL Queries | All 10 questions run live, search, CSV download, custom read-only SQL box |
| Power BI Dashboard | Embeds your published report via iframe |
| Insights & Anomalies | Hour×weekday heatmap, fare-per-km anomaly detection, business takeaways |
| Data Explorer | Search by Booking/Customer ID or location, choose columns, download |

Sidebar filters (date, vehicle, status, payment, pickup location) apply to every dashboard page.

## SQL in MySQL (for Power BI)
1. `gunzip -k data/ola_rides_clean.csv.gz`
2. Run `sql/ola_queries.sql` in MySQL Workbench (creates DB `ola`, table, loads CSV, creates 10 views).
3. Power BI Desktop → *Get Data → MySQL database* → server `localhost`, DB `ola` → select `ola_rides` (+ views).

## Power BI build guide (5 pages, as per the brief)
**Measures (DAX)**
```DAX
Total Bookings      = COUNTROWS(ola_rides)
Successful Rides    = CALCULATE([Total Bookings], ola_rides[Booking_Status] = "Success")
Success Rate        = DIVIDE([Successful Rides], [Total Bookings])
Revenue             = CALCULATE(SUM(ola_rides[Booking_Value]), ola_rides[Booking_Status] = "Success")
Cancelled Rides     = CALCULATE([Total Bookings], ola_rides[Cancelled_By] <> "Not Cancelled")
Cancellation Rate   = DIVIDE([Cancelled Rides], [Total Bookings])
Avg Driver Rating   = AVERAGE(ola_rides[Driver_Ratings])
Avg Customer Rating = AVERAGE(ola_rides[Customer_Rating])
Total Distance      = SUM(ola_rides[Ride_Distance])
```
| Page | Visuals |
|---|---|
| 1 Overall | KPI cards; Line: Ride_Date × Total Bookings; Donut: Booking_Status |
| 2 Vehicle Type | Bar: Vehicle_Type × Total Distance (Top N = 5) |
| 3 Revenue | Bar: Payment_Method × Revenue; Bar: Customer_ID × Revenue (Top N = 5); Column: Ride_Date × Total Distance |
| 4 Cancellation | Bar: Canceled_Rides_by_Customer × count; Bar: Canceled_Rides_by_Driver × count |
| 5 Ratings | Column: Driver_Ratings × count; Column: Vehicle_Type × Avg Customer Rating; Clustered bar: customer vs driver avg by vehicle |

Slicers on every page: Ride_Date (between), Vehicle_Type, Booking_Status, Payment_Method.
Publish → *File → Embed report → Publish to web* → paste the link into the Streamlit app.

## Key insights
1. **62.1% success rate** — 37.9% of bookings (≈ ₹2.15 Cr of booking value) never become rides.
2. **Drivers cancel 1.8× more than customers** (17.9% vs 10.2%). Top driver reason: *Personal & Car related issue* (6,542). Top customer reason: *Driver is not moving towards pickup location* (3,175).
3. **Revenue ₹3.51 Cr** from 63,967 rides; **Cash 55%**, UPI 40%, cards < 5%.
4. **Demand is flat**: ~3,300 bookings/day, no hour or weekday dominates, so driver supply should be spread evenly.
5. **Auto** averages ~10 km per ride; every other category averages ~25 km.
6. Ratings cluster around **4.0** for every vehicle type.
7. **4,460 rides (7%)** have an extreme fare per km — candidates for a fraud / pricing audit.

## SQL answers (validated)
| # | Question | Answer |
|---|---|---|
| 1 | Successful bookings | 63,967 rows |
| 2 | Avg distance by vehicle | ~15.5 km all bookings (Auto 6.2); ~25 km successful (Auto 10.0) |
| 3 | Cancelled by customers | 10,499 |
| 4 | Top 5 customers by rides | CID954071 (5), then four customers with 4 rides each (ties broken alphabetically) |
| 5 | Driver cancels: personal & car issue | 6,542 |
| 6 | Prime Sedan driver rating | Max 5.0, Min 3.0 |
| 7 | UPI rides | 25,881 rows |
| 8 | Avg customer rating by vehicle | 3.99 – 4.01 |
| 9 | Total value of successful rides | ₹3,50,80,467 (₹3,28,29,985 excluding incomplete) |
| 10 | Incomplete rides with reason | 3,926 rows (Customer Demand 1,601, Vehicle Breakdown 1,591, Other 734) |
