"""
Single source of truth for the 10 project SQL questions.
Written in ANSI-style SQL that runs on SQLite (used by the app) and MySQL.
Each entry: title, sql, and a short business note shown in the app.
"""

QUERIES = {
    "Q1. Retrieve all successful bookings": {
        "view": "successful_bookings",
        "sql": """
SELECT *
FROM ola_rides
WHERE Booking_Status = 'Success';""",
        "note": "Base set for revenue, ratings and payment analysis.",
    },
    "Q2. Average ride distance for each vehicle type": {
        "view": "avg_ride_distance_by_vehicle",
        "sql": """
SELECT Vehicle_Type,
       ROUND(AVG(Ride_Distance), 2) AS Avg_Distance_All_Bookings,
       ROUND(AVG(CASE WHEN Booking_Status = 'Success'
                      THEN Ride_Distance END), 2) AS Avg_Distance_Successful
FROM ola_rides
GROUP BY Vehicle_Type
ORDER BY Avg_Distance_All_Bookings DESC;""",
        "note": "Cancelled rides carry 0 km, so the 'successful only' column is the true trip length.",
    },
    "Q3. Total number of rides cancelled by customers": {
        "view": "cancelled_by_customers",
        "sql": """
SELECT COUNT(*) AS Total_Cancelled_By_Customers
FROM ola_rides
WHERE Booking_Status = 'Canceled by Customer';""",
        "note": "Compare with driver cancellations - drivers cancel ~1.8x more often.",
    },
    "Q4. Top 5 customers by number of rides booked": {
        "view": "top_5_customers",
        "sql": """
SELECT Customer_ID,
       COUNT(Booking_ID) AS Total_Rides
FROM ola_rides
GROUP BY Customer_ID
ORDER BY Total_Rides DESC, Customer_ID
LIMIT 5;""",
        "note": "Candidates for a loyalty / subscription programme.",
    },
    "Q5. Rides cancelled by drivers due to personal & car-related issues": {
        "view": "driver_cancel_personal_car",
        "sql": """
SELECT COUNT(*) AS Rides_Cancelled_Personal_Car_Issue
FROM ola_rides
WHERE Canceled_Rides_by_Driver = 'Personal & Car related issue';""",
        "note": "Largest single driver-side reason - a fleet-maintenance and driver-welfare lever.",
    },
    "Q6. Max & min driver ratings for Prime Sedan bookings": {
        "view": "prime_sedan_driver_rating",
        "sql": """
SELECT MAX(Driver_Ratings) AS Max_Driver_Rating,
       MIN(Driver_Ratings) AS Min_Driver_Rating
FROM ola_rides
WHERE Vehicle_Type = 'Prime Sedan'
  AND Driver_Ratings IS NOT NULL;""",
        "note": "Ratings exist only for successful rides.",
    },
    "Q7. Retrieve all rides paid using UPI": {
        "view": "upi_payments",
        "sql": """
SELECT *
FROM ola_rides
WHERE Payment_Method = 'UPI';""",
        "note": "UPI is the #2 payment method after Cash.",
    },
    "Q8. Average customer rating per vehicle type": {
        "view": "avg_customer_rating",
        "sql": """
SELECT Vehicle_Type,
       ROUND(AVG(Customer_Rating), 2) AS Avg_Customer_Rating
FROM ola_rides
WHERE Customer_Rating IS NOT NULL
GROUP BY Vehicle_Type
ORDER BY Avg_Customer_Rating DESC;""",
        "note": "Ratings are tightly clustered across vehicle types.",
    },
    "Q9. Total booking value of successfully completed rides": {
        "view": "total_successful_ride_value",
        "sql": """
SELECT SUM(Booking_Value) AS Total_Successful_Booking_Value,
       SUM(CASE WHEN Incomplete_Rides = 'No'
                THEN Booking_Value ELSE 0 END) AS Value_Fully_Completed_Rides
FROM ola_rides
WHERE Booking_Status = 'Success';""",
        "note": "Second column excludes 'Success' bookings that were flagged incomplete mid-trip.",
    },
    "Q10. All incomplete rides with reason": {
        "view": "incomplete_rides_reason",
        "sql": """
SELECT Booking_ID, Ride_Date, Customer_ID, Vehicle_Type,
       Pickup_Location, Drop_Location, Incomplete_Rides_Reason
FROM ola_rides
WHERE Incomplete_Rides = 'Yes';""",
        "note": "Summary by reason is in the Cancellation tab.",
    },
}
