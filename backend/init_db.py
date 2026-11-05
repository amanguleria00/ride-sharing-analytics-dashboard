"""Create the dashboard schema and insert deterministic sample data."""

import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from persistence import connect


DEFAULT_DATABASE = Path(__file__).with_name("ride_sharing.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS riders (
    rider_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    registration_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drivers (
    driver_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    rating REAL NOT NULL CHECK (rating BETWEEN 0 AND 5),
    license_number TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive'))
);
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    driver_id INTEGER NOT NULL UNIQUE REFERENCES drivers(driver_id),
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('Sedan', 'SUV', 'Hatchback', 'Premium')),
    registration_number TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);
CREATE TABLE IF NOT EXISTS rides (
    ride_id INTEGER PRIMARY KEY,
    rider_id INTEGER NOT NULL REFERENCES riders(rider_id),
    driver_id INTEGER NOT NULL REFERENCES drivers(driver_id),
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
    pickup_location TEXT NOT NULL,
    dropoff_location TEXT NOT NULL,
    request_time TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    distance_km REAL NOT NULL CHECK (distance_km >= 0),
    fare REAL NOT NULL CHECK (fare >= 0),
    ride_status TEXT NOT NULL CHECK (ride_status IN ('requested', 'ongoing', 'completed', 'cancelled')),
    CHECK (end_time IS NULL OR start_time IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL UNIQUE REFERENCES rides(ride_id),
    payment_method TEXT NOT NULL CHECK (payment_method IN ('Card', 'Cash', 'Wallet', 'UPI')),
    amount REAL NOT NULL CHECK (amount >= 0),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('successful', 'failed', 'refunded')),
    payment_time TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rides_request_time ON rides(request_time);
CREATE INDEX IF NOT EXISTS idx_rides_status_time ON rides(ride_status, request_time);
CREATE INDEX IF NOT EXISTS idx_rides_driver_status ON rides(driver_id, ride_status);
CREATE INDEX IF NOT EXISTS idx_rides_vehicle ON rides(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status);
"""

RIDER_NAMES = ["Aarav Mehta", "Diya Sharma", "Kabir Singh", "Anaya Patel",
               "Arjun Kumar", "Isha Gupta", "Vivaan Shah", "Mira Joshi",
               "Reyansh Rao", "Saanvi Verma", "Advik Nair", "Kiara Das",
               "Ayaan Kapoor", "Myra Jain", "Krishna Reddy", "Aadhya Bose",
               "Rohan Malhotra", "Tara Iyer", "Dev Khanna", "Nisha Roy"]
DRIVER_NAMES = ["Raj Malhotra", "Priya Nair", "Sanjay Rao", "Neha Kapoor",
                "Amit Verma", "Pooja Shah", "Vikram Das", "Anjali Mehta",
                "Rahul Joshi", "Simran Kaur", "Karan Patel", "Meera Iyer"]
VEHICLES = ["Sedan", "SUV", "Hatchback", "Premium"]
LOCATIONS = ["Connaught Place", "Indiranagar", "Bandra West", "Salt Lake",
             "Koramangala", "Hitech City", "Civil Lines", "Park Street",
             "Airport Terminal", "MG Road"]
METHODS = ["Card", "Cash", "Wallet", "UPI"]
STATUSES = ["completed"] * 7 + ["cancelled"] * 2 + ["ongoing", "requested"]


def initialize_database(database_path=DEFAULT_DATABASE):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(database_path)
    try:
        connection.executescript(SCHEMA)
        for index, name in enumerate(RIDER_NAMES, 1):
            connection.execute(
                "INSERT OR IGNORE INTO riders VALUES (?, ?, ?, ?, ?)",
                (index, name, f"rider{index}@example.com", f"+91-90000-{index:05d}",
                 f"2023-{(index - 1) % 12 + 1:02d}-{(index - 1) % 27 + 1:02d}"))
        for index, name in enumerate(DRIVER_NAMES, 1):
            connection.execute(
                "INSERT OR IGNORE INTO drivers VALUES (?, ?, ?, ?, ?, ?)",
                (index, name, f"+91-80000-{index:05d}", round(4.1 + (index % 9) * 0.1, 1),
                 f"DL-2024-{index:05d}", "active" if index < 11 else "inactive"))
            connection.execute(
                "INSERT OR IGNORE INTO vehicles VALUES (?, ?, ?, ?, ?)",
                (index, index, VEHICLES[(index - 1) % len(VEHICLES)],
                 f"DL-{index:02d}-AB-{1000 + index}", 4 if index % 3 else 6))

        base = datetime(2025, 1, 1, 6, 0)
        for ride_id in range(1, 151):
            request_time = base + timedelta(days=(ride_id - 1) % 90,
                                            hours=(ride_id * 7) % 17,
                                            minutes=(ride_id * 13) % 60)
            status = STATUSES[(ride_id - 1) % len(STATUSES)]
            driver_id = (ride_id - 1) % len(DRIVER_NAMES) + 1
            distance = round(2.2 + (ride_id * 1.37) % 28, 1)
            fare = round(45 + distance * (12 + driver_id % 5), 2)
            start_time = request_time + timedelta(minutes=5) if status in ("completed", "ongoing") else None
            end_time = start_time + timedelta(minutes=12 + ride_id % 38) if status == "completed" else None
            connection.execute(
                """INSERT OR IGNORE INTO rides
                   (ride_id, rider_id, driver_id, vehicle_id, pickup_location, dropoff_location,
                    request_time, start_time, end_time, distance_km, fare, ride_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ride_id, (ride_id - 1) % len(RIDER_NAMES) + 1, driver_id, driver_id,
                 LOCATIONS[(ride_id - 1) % len(LOCATIONS)],
                 LOCATIONS[(ride_id + 3) % len(LOCATIONS)],
                 request_time.isoformat(timespec="minutes"),
                 start_time.isoformat(timespec="minutes") if start_time else None,
                 end_time.isoformat(timespec="minutes") if end_time else None,
                 distance, fare, status))
            payment_status = ("successful" if status == "completed" and ride_id % 13 != 0
                              else "refunded" if status == "completed"
                              else "failed")
            connection.execute(
                """INSERT OR IGNORE INTO payments
                   (payment_id, ride_id, payment_method, amount, payment_status, payment_time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ride_id, ride_id, METHODS[(ride_id - 1) % len(METHODS)], fare,
                 payment_status, (request_time + timedelta(minutes=50)).isoformat(timespec="minutes")))
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE,
                        help="SQLite file path (default: backend/ride_sharing.db)")
    args = parser.parse_args()
    initialize_database(args.database)
    print(f"Database initialized at {args.database.resolve()}")
