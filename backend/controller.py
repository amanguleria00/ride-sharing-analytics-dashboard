"""HTTP routes and request validation for the dashboard API."""

import re
import sqlite3
from datetime import date

from flask import Blueprint, current_app, jsonify, request

import persistence

api = Blueprint("api", __name__, url_prefix="/api")
VALID_STATUSES = {"requested", "ongoing", "completed", "cancelled"}
VALID_VEHICLES = {"Sedan", "SUV", "Hatchback", "Premium"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InvalidParameter(ValueError):
    pass


def _dates():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    for label, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None:
            if not DATE_PATTERN.fullmatch(value):
                raise InvalidParameter(f"{label} must use YYYY-MM-DD format")
            try:
                date.fromisoformat(value)
            except ValueError as error:
                raise InvalidParameter(f"{label} is not a valid date") from error
    if start_date and end_date and start_date > end_date:
        raise InvalidParameter("start_date must be on or before end_date")
    return start_date, end_date


def _database_path():
    return current_app.config["DATABASE"]


def _result(operation):
    try:
        return jsonify({"data": operation()}), 200
    except InvalidParameter as error:
        return jsonify({"error": {"message": str(error)}}), 400
    except sqlite3.Error:
        current_app.logger.exception("Dashboard database query failed")
        return jsonify({"error": {"message": "A database error occurred"}}), 500


def _date_call(function, **extra):
    start_date, end_date = _dates()
    return function(_database_path(), start_date, end_date, **extra)


@api.get("/health")
def health():
    return jsonify({"data": {"status": "ok"}}), 200


@api.get("/dashboard/summary")
def summary():
    return _result(lambda: _date_call(persistence.get_summary))


@api.get("/dashboard/revenue-trend")
def revenue_trend():
    def query():
        granularity = request.args.get("granularity", "daily")
        if granularity not in {"daily", "monthly"}:
            raise InvalidParameter("granularity must be daily or monthly")
        return _date_call(persistence.get_revenue_trend, granularity=granularity)
    return _result(query)


@api.get("/dashboard/rides-by-status")
def rides_by_status():
    return _result(lambda: _date_call(persistence.get_rides_by_status))


@api.get("/dashboard/rides-by-vehicle")
def rides_by_vehicle():
    return _result(lambda: _date_call(persistence.get_rides_by_vehicle))


@api.get("/dashboard/top-drivers")
def top_drivers():
    def query():
        limit = _integer_parameter("limit", 10, 1, 50)
        return _date_call(persistence.get_top_drivers, limit=limit)
    return _result(query)


@api.get("/dashboard/peak-hours")
def peak_hours():
    return _result(lambda: _date_call(persistence.get_peak_hours))


@api.get("/dashboard/payment-methods")
def payment_methods():
    return _result(lambda: _date_call(persistence.get_payment_methods))


def _integer_parameter(name, default, minimum, maximum):
    value = request.args.get(name, str(default))
    try:
        parsed = int(value)
    except ValueError as error:
        raise InvalidParameter(f"{name} must be an integer") from error
    if parsed < minimum or parsed > maximum:
        raise InvalidParameter(f"{name} must be between {minimum} and {maximum}")
    return parsed


@api.get("/rides")
def rides():
    def query():
        start_date, end_date = _dates()
        page = _integer_parameter("page", 1, 1, 1_000_000)
        per_page = _integer_parameter("per_page", 10, 1, 100)
        status = request.args.get("status")
        vehicle_type = request.args.get("vehicle_type")
        if status and status not in VALID_STATUSES:
            raise InvalidParameter("status must be requested, ongoing, completed, or cancelled")
        if vehicle_type and vehicle_type not in VALID_VEHICLES:
            raise InvalidParameter("vehicle_type must be Sedan, SUV, Hatchback, or Premium")
        return persistence.get_rides(_database_path(), start_date, end_date, status,
                                     vehicle_type, page, per_page)
    return _result(query)
