from unittest.mock import patch, MagicMock, call
import frappe
import unittest
from f_watcher.collectors.alerting import evaluate_condition, get_latest_metric


class TestEvaluateCondition(unittest.TestCase):
    def test_greater_than(self):
        self.assertTrue(evaluate_condition(90, ">", 80))
        self.assertFalse(evaluate_condition(70, ">", 80))

    def test_less_than(self):
        self.assertTrue(evaluate_condition(10, "<", 20))
        self.assertFalse(evaluate_condition(30, "<", 20))

    def test_gte(self):
        self.assertTrue(evaluate_condition(80, ">=", 80))
        self.assertTrue(evaluate_condition(81, ">=", 80))
        self.assertFalse(evaluate_condition(79, ">=", 80))

    def test_lte(self):
        self.assertTrue(evaluate_condition(80, "<=", 80))
        self.assertFalse(evaluate_condition(81, "<=", 80))

    def test_equals(self):
        self.assertTrue(evaluate_condition(5.0, "==", 5.0))
        self.assertFalse(evaluate_condition(5.1, "==", 5.0))

    def test_unknown_condition_returns_false(self):
        self.assertFalse(evaluate_condition(100, "!=", 50))


class TestGetLatestMetric(unittest.TestCase):
    def test_system_metric_type(self):
        fake_row = {"cpu_percent": 30.0, "ram_percent": 50.0}
        with patch("frappe.db.get_all", return_value=[fake_row]):
            result = get_latest_metric("System")
        self.assertEqual(result["cpu_percent"], 30.0)

    def test_unknown_metric_type_returns_none(self):
        result = get_latest_metric("UnknownType")
        self.assertIsNone(result)

    def test_empty_db_returns_none(self):
        with patch("frappe.db.get_all", return_value=[]):
            result = get_latest_metric("System")
        self.assertIsNone(result)


class TestEvaluateAndAlert(unittest.TestCase):
    def _make_rule(self, **overrides):
        base = {
            "name": "RULE-001",
            "rule_name": "High CPU",
            "is_active": 1,
            "metric_type": "System",
            "property_name": "cpu_percent",
            "condition": ">",
            "threshold_value": 80.0,
            "alert_channel": "System Notification",
            "webhook_url": None,
            "email_address": None,
            "last_triggered": None,
            "cooldown_minutes": 15,
        }
        base.update(overrides)
        return MagicMock(**base)

    def test_alert_fires_when_threshold_exceeded(self):
        rule = self._make_rule()
        fake_metric = {"cpu_percent": 95.0}
        inserted_docs = []

        def fake_get_doc(data):
            doc = MagicMock()
            doc.insert = MagicMock(side_effect=lambda **kw: inserted_docs.append(data))
            return doc

        with patch("frappe.get_all", return_value=[rule]), \
             patch("f_watcher.collectors.alerting.get_latest_metric", return_value=fake_metric), \
             patch("frappe.get_doc", side_effect=fake_get_doc), \
             patch("frappe.db.set_value"), \
             patch("frappe.db.commit"), \
             patch("frappe.publish_realtime"):
            from f_watcher.collectors.alerting import evaluate_and_alert
            evaluate_and_alert()

        self.assertTrue(any(d.get("doctype") == "F Watcher Alert Log" for d in inserted_docs))

    def test_alert_skips_when_below_threshold(self):
        rule = self._make_rule()
        fake_metric = {"cpu_percent": 50.0}
        inserted_docs = []

        def fake_get_doc(data):
            doc = MagicMock()
            doc.insert = MagicMock(side_effect=lambda **kw: inserted_docs.append(data))
            return doc

        with patch("frappe.get_all", return_value=[rule]), \
             patch("f_watcher.collectors.alerting.get_latest_metric", return_value=fake_metric), \
             patch("frappe.get_doc", side_effect=fake_get_doc):
            from f_watcher.collectors.alerting import evaluate_and_alert
            evaluate_and_alert()

        self.assertFalse(any(d.get("doctype") == "F Watcher Alert Log" for d in inserted_docs))

    def test_cooldown_prevents_repeat_alert(self):
        from frappe.utils import add_to_date, now_datetime
        rule = self._make_rule(last_triggered=add_to_date(now_datetime(), seconds=-60))
        fake_metric = {"cpu_percent": 95.0}
        inserted_docs = []

        def fake_get_doc(data):
            doc = MagicMock()
            doc.insert = MagicMock(side_effect=lambda **kw: inserted_docs.append(data))
            return doc

        with patch("frappe.get_all", return_value=[rule]), \
             patch("f_watcher.collectors.alerting.get_latest_metric", return_value=fake_metric), \
             patch("frappe.get_doc", side_effect=fake_get_doc):
            from f_watcher.collectors.alerting import evaluate_and_alert
            evaluate_and_alert()

        self.assertFalse(any(d.get("doctype") == "F Watcher Alert Log" for d in inserted_docs))
