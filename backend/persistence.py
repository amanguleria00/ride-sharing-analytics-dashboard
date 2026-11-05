"""SQLite access and analytics queries for the ride-sharing dashboard."""

import sqlite3
from contextlib import closing
from pathlib import Path


def connect(database_path):
    """Open a row-producing SQLite connection with foreign keys enabled."""
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def fetch_all(database_path, query, parameters=()):
    with closing(connect(database_path)) as connection:
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]


def fetch_one(database_path, query, parameters=()):
    with closing(connect(database_path)) as connection:
        row = connection.execute(query, parameters).fetchone()
        return dict(row) if row is not None else None


def date_conditions(start_date=None, end_date=None, column="r.request_time"):
    conditions = []
    parameters = []
    if start_date:
        conditions.append(f"date({column}) >= date(?)")
        parameters.append(start_date)
    if end_date:
        conditions.append(f"date({column}) <= date(?)")
        parameters.append(end_date)
    return (" AND " + " AND ".join(conditions)) if conditions else "", parameters


def get_summary(database_path, start_date=None, end_date=None):
    date_sql, parameters = date_conditions(start_date, end_date)
    query = f"""
        SELECT
            COUNT(*) AS total_rides,
            COALESCE(SUM(CASE WHEN r.ride_status = 'completed' THEN 1 ELSE 0 END), 0)
                AS completed_rides,
            COALESCE(SUM(CASE WHEN r.ride_status = 'cancelled' THEN 1 ELSE 0 END), 0)
                AS cancelled_rides,
            COALESCE(SUM(CASE WHEN r.ride_status = 'completed' THEN r.fare ELSE 0 END), 0)
                AS completed_fare_total,
            COALESCE(SUM(CASE WHEN r.ride_status = 'cancelled' THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(*), 0), 0) AS cancellation_rate,
            COALESCE((
                SELECT SUM(p.amount)
                FROM payments p
                JOIN rides paid_ride ON paid_ride.ride_id = p.ride_id
                WHERE p.payment_status = 'successful'
                    AND paid_ride.ride_status = 'completed'
                    {date_sql.replace('r.request_time', 'paid_ride.request_time')}
            ), 0) AS total_revenue
        FROM rides r
        WHERE 1 = 1 {date_sql}
    """
    # Parameters are repeated because the revenue subquery and outer query each filter dates.
    values = parameters + parameters
    row = fetch_one(database_path, query, values)
    completed = row["completed_rides"]
    return {
        "total_rides": row["total_rides"],
        "completed_rides": completed,
        "cancelled_rides": row["cancelled_rides"],
        "total_revenue": round(row["total_revenue"], 2),
        "average_fare": round(row["completed_fare_total"] / completed, 2) if completed else 0,
        "cancellation_rate": round(row["cancellation_rate"], 2),
    }


def get_revenue_trend(database_path, start_date=None, end_date=None, granularity="daily"):
    date_sql, parameters = date_conditions(start_date, end_date)
    date_format = "%Y-%m" if granularity == "monthly" else "%Y-%m-%d"
    query = f"""
        SELECT strftime(?, r.request_time) AS period,
            ROUND(SUM(p.amount), 2) AS revenue
        FROM rides r
        JOIN payments p ON p.ride_id = r.ride_id
        WHERE r.ride_status = 'completed' AND p.payment_status = 'successful'
            {date_sql}
        GROUP BY period ORDER BY period
    """
    return fetch_all(database_path, query, [date_format] + parameters)


def get_rides_by_status(database_path, start_date=None, end_date=None):
    date_sql, parameters = date_conditions(start_date, end_date)
    return fetch_all(database_path, f"""
        SELECT r.ride_status AS status, COUNT(*) AS rides
        FROM rides r WHERE 1 = 1 {date_sql}
        GROUP BY r.ride_status ORDER BY rides DESC, status
    """, parameters)


def get_rides_by_vehicle(database_path, start_date=None, end_date=None):
    date_sql, parameters = date_conditions(start_date, end_date)
    return fetch_all(database_path, f"""
        SELECT v.vehicle_type, COUNT(*) AS rides
        FROM rides r JOIN vehicles v ON v.vehicle_id = r.vehicle_id
        WHERE 1 = 1 {date_sql}
        GROUP BY v.vehicle_type ORDER BY rides DESC, v.vehicle_type
    """, parameters)


def get_top_drivers(database_path, start_date=None, end_date=None, limit=10):
    date_sql, parameters = date_conditions(start_date, end_date)
    return fetch_all(database_path, f"""
        SELECT d.driver_id, d.name, d.rating,
            COUNT(r.ride_id) AS completed_rides,
            ROUND(COALESCE(SUM(CASE WHEN p.payment_status = 'successful'
                THEN p.amount ELSE 0 END), 0), 2) AS revenue
        FROM drivers d
        LEFT JOIN rides r ON r.driver_id = d.driver_id
            AND r.ride_status = 'completed' {date_sql}
        LEFT JOIN payments p ON p.ride_id = r.ride_id
        GROUP BY d.driver_id, d.name, d.rating
        ORDER BY completed_rides DESC, revenue DESC, d.name
        LIMIT ?
    """, parameters + [limit])


def get_peak_hours(database_path, start_date=None, end_date=None):
    date_sql, parameters = date_conditions(start_date, end_date)
    return fetch_all(database_path, f"""
        SELECT CAST(strftime('%H', r.request_time) AS INTEGER) AS hour,
            COUNT(*) AS rides
        FROM rides r WHERE 1 = 1 {date_sql}
        GROUP BY hour ORDER BY hour
    """, parameters)


def get_payment_methods(database_path, start_date=None, end_date=None):
    date_sql, parameters = date_conditions(start_date, end_date, "r.request_time")
    return fetch_all(database_path, f"""
        SELECT p.payment_method, COUNT(*) AS payments,
            ROUND(SUM(p.amount), 2) AS amount
        FROM payments p JOIN rides r ON r.ride_id = p.ride_id
        WHERE p.payment_status = 'successful' {date_sql}
        GROUP BY p.payment_method ORDER BY payments DESC, p.payment_method
    """, parameters)


def get_rides(database_path, start_date=None, end_date=None, status=None,
              vehicle_type=None, page=1, per_page=10):
    date_sql, parameters = date_conditions(start_date, end_date)
    conditions = ["1 = 1" + date_sql]
    values = list(parameters)
    if status:
        conditions.append("r.ride_status = ?")
        values.append(status)
    if vehicle_type:
        conditions.append("v.vehicle_type = ?")
        values.append(vehicle_type)
    where_sql = " AND ".join(conditions)
    count = fetch_one(database_path, f"""
        SELECT COUNT(*) AS total FROM rides r
        JOIN vehicles v ON v.vehicle_id = r.vehicle_id WHERE {where_sql}
    """, values)["total"]
    rows = fetch_all(database_path, f"""
        SELECT r.ride_id, r.pickup_location, r.dropoff_location, r.request_time,
            r.distance_km, r.fare, r.ride_status AS status,
            d.name AS driver_name, v.vehicle_type,
            p.payment_method, p.payment_status
        FROM rides r
        JOIN drivers d ON d.driver_id = r.driver_id
        JOIN vehicles v ON v.vehicle_id = r.vehicle_id
        LEFT JOIN payments p ON p.ride_id = r.ride_id
        WHERE {where_sql}
        ORDER BY r.request_time DESC, r.ride_id DESC
        LIMIT ? OFFSET ?
    """, values + [per_page, (page - 1) * per_page])
    return {"items": rows, "page": page, "per_page": per_page, "total": count,
            "total_pages": (count + per_page - 1) // per_page}


def database_exists(database_path):
    return Path(database_path).is_file()
