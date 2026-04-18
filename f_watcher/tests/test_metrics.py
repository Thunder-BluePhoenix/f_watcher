from unittest.mock import patch, MagicMock
import unittest
from f_watcher.dashboards import metrics


FAKE_SYSTEM = [{
    "timestamp": "2026-04-18 10:00:00",
    "hostname": "bench-host",
    "cpu_percent": 25.0,
    "ram_percent": 60.0,
    "disk_percent": 45.0,
    "load_1": 0.5,
    "load_5": 0.4,
    "load_15": 0.3,
}]

FAKE_DB_SNAP = [{"timestamp": "2026-04-18 10:00:00", "db_name": "testdb", "total_mb": 512}]
FAKE_QUEUES = [{"queue_name": "default", "job_count": 2, "failed_count": 0, "active_workers": 1}]
FAKE_BIG_TABLES = [{"table_name": "tabError Log", "total_mb": 200, "rows_est": 50000}]


class TestMetricsLatest(unittest.TestCase):
    def test_latest_returns_expected_keys(self):
        with patch("frappe.db.get_all") as mock_get_all, \
             patch("frappe.db.sql", return_value=FAKE_BIG_TABLES):

            def side_effect(doctype, **kw):
                if doctype == "F Watcher System Metric":
                    return FAKE_SYSTEM
                if doctype == "F Watcher DB Storage Snapshot":
                    return FAKE_DB_SNAP
                if doctype == "F Watcher Queue Metric":
                    return FAKE_QUEUES
                return []

            mock_get_all.side_effect = side_effect
            result = metrics.latest()

        self.assertIn("system", result)
        self.assertIn("db_snapshot", result)
        self.assertIn("queues", result)
        self.assertIn("big_tables", result)

    def test_latest_handles_empty_tables(self):
        with patch("frappe.db.get_all", return_value=[]), \
             patch("frappe.db.sql", return_value=[]):
            result = metrics.latest()

        self.assertIsNone(result["system"])
        self.assertIsNone(result["db_snapshot"])
        self.assertEqual(result["queues"], [])
        self.assertEqual(result["big_tables"], [])


class TestMetricsAudit(unittest.TestCase):
    def test_audit_default_limit(self):
        with patch("frappe.db.get_all", return_value=[]) as mock:
            metrics.audit()
            _, kwargs = mock.call_args
            self.assertEqual(kwargs.get("limit"), 20)

    def test_audit_custom_limit(self):
        with patch("frappe.db.get_all", return_value=[]) as mock:
            metrics.audit(limit=5)
            _, kwargs = mock.call_args
            self.assertEqual(kwargs.get("limit"), 5)
