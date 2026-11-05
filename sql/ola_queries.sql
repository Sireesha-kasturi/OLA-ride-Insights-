-- =============================================================
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
LINES TERMINATED BY '\n'
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

-- Q1. Retrieve all successful bookings
CREATE OR REPLACE VIEW successful_bookings AS
SELECT *
FROM ola_rides
WHERE Booking_Status = 'Success';
SELECT * FROM successful_bookings;

-- Q2. Average ride distance for each vehicle type
CREATE OR REPLACE VIEW avg_ride_distance_by_vehicle AS
SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Distance_All_Bookings,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success'
                      THEN Ride_Distance END), 2) AS Avg_Distance_Successful
FROM ola_rides
GROUP BY Vehicle_Type
ORDER BY Avg_Distance_All_Bookings DESC;
SELECT * FROM avg_ride_distance_by_vehicle;

-- Q3. Total number of rides cancelled by customers
CREATE OR REPLACE VIEW cancelled_by_customers AS
SELECT COUNT(*) AS Total_Cancelled_By_Customers
FROM ola_rides
WHERE Booking_Status = 'Canceled by Customer';
SELECT * FROM cancelled_by_customers;

-- Q4. Top 5 customers by number of rides booked
CREATE OR REPLACE VIEW top_5_customers AS
SELECT Customer_ID,
       COUNT(Booking_ID) AS Total_Rides
FROM ola_rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;
SELECT * FROM top_5_customers;

-- Q5. Rides cancelled by drivers due to personal & car-related issues
CREATE OR REPLACE VIEW driver_cancel_personal_car AS
SELECT COUNT(*) AS Rides_Cancelled_Personal_Car_Issue
FROM ola_rides
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue';
SELECT * FROM driver_cancel_personal_car;

-- Q6. Max & min driver ratings for Prime Sedan bookings
CREATE OR REPLACE VIEW prime_sedan_driver_rating AS
SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM ola_rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Driver_Ratings IS NOT NULL;
SELECT * FROM prime_sedan_driver_rating;

-- Q7. Retrieve all rides paid using UPI
CREATE OR REPLACE VIEW upi_payments AS
SELECT *
FROM ola_rides
WHERE Payment_Method = 'UPI';
SELECT * FROM upi_payments;

-- Q8. Average customer rating per vehicle type
CREATE OR REPLACE VIEW avg_customer_rating AS
SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM ola_rides
WHERE Customer_Rating IS NOT NULL
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC;
SELECT * FROM avg_customer_rating;

-- Q9. Total booking value of successfully completed rides
CREATE OR REPLACE VIEW total_successful_ride_value AS
SELECT SUM(Booking_Value) AS Total_Successful_Booking_Value,
       SUM(CASE WHEN Incomplete_Rides = 'No'
                THEN Booking_Value ELSE 0 END) AS Value_Fully_Completed_Rides
FROM ola_rides
WHERE Booking_Status = 'Success';
SELECT * FROM total_successful_ride_value;

-- Q10. All incomplete rides with reason
CREATE OR REPLACE VIEW incomplete_rides_reason AS
SELECT Booking_ID, Ride_Date, Customer_ID, Vehicle_Type,
       Pickup_Location, Drop_Location, Incomplete_Rides_Reason
FROM ola_rides
WHERE Incomplete_Rides = 'Yes';
SELECT * FROM incomplete_rides_reason;
