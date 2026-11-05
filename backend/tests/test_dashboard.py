import tempfile
import unittest
from pathlib import Path

from app import create_app
from init_db import initialize_database
import persistence


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database)
        self.client = create_app(self.database).test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_seed_is_repeatable_and_relationships_are_valid(self):
        initialize_database(self.database)
        connection = persistence.connect(self.database)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM rides").fetchone()[0], 150)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM riders").fetchone()[0], 20)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            connection.close()

    def test_summary_matches_underlying_queries(self):
        response = self.client.get("/api/dashboard/summary")
        summary = response.get_json()["data"]
        connection = persistence.connect(self.database)
        try:
            completed = connection.execute(
                "SELECT COUNT(*) FROM rides WHERE ride_status = 'completed'").fetchone()[0]
            revenue = connection.execute("""
                SELECT COALESCE(SUM(p.amount), 0) FROM payments p
                JOIN rides r ON r.ride_id = p.ride_id
                WHERE r.ride_status = 'completed' AND p.payment_status = 'successful'
            """).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(summary["completed_rides"], completed)
        self.assertEqual(summary["total_revenue"], round(revenue, 2))
        self.assertIsInstance(summary["cancellation_rate"], float)

    def test_date_and_pagination_filters(self):
        response = self.client.get("/api/rides?status=completed&page=1&per_page=5")
        payload = response.get_json()["data"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["per_page"], 5)
        self.assertLessEqual(len(payload["items"]), 5)
        self.assertTrue(all(item["status"] == "completed" for item in payload["items"]))
        filtered = self.client.get("/api/rides?start_date=2025-01-01&end_date=2025-01-02")
        self.assertTrue(all(item["request_time"][:10] <= "2025-01-02"
                            for item in filtered.get_json()["data"]["items"]))

    def test_invalid_parameters_and_empty_date_range(self):
        self.assertEqual(self.client.get("/api/rides?page=0").status_code, 400)
        self.assertEqual(self.client.get("/api/rides?status=bogus").status_code, 400)
        self.assertEqual(self.client.get("/api/dashboard/summary?start_date=2025-02-30").status_code, 400)
        empty = self.client.get("/api/dashboard/summary?start_date=2030-01-01")
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.get_json()["data"]["total_rides"], 0)

    def test_analytics_endpoints_and_health(self):
        paths = ["/api/health", "/api/dashboard/revenue-trend",
                 "/api/dashboard/rides-by-status", "/api/dashboard/rides-by-vehicle",
                 "/api/dashboard/top-drivers", "/api/dashboard/peak-hours",
                 "/api/dashboard/payment-methods"]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("data", response.get_json())


if __name__ == "__main__":
    unittest.main()
