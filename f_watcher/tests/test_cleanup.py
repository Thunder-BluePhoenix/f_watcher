from unittest.mock import patch, MagicMock
import frappe
import unittest
from f_watcher.actions.cleanup import preview, execute, _check_permission, CLEANUP_RULES


class TestCleanupPermission(unittest.TestCase):
    def test_administrator_passes(self):
        with patch.object(frappe, "session", MagicMock(user="Administrator")):
            # Should not raise
            _check_permission()

    def test_system_manager_passes(self):
        with patch("frappe.get_roles", return_value=["System Manager", "All"]):
            with patch.object(frappe, "session", MagicMock(user="john@example.com")):
                _check_permission()

    def test_operator_passes(self):
        with patch("frappe.get_roles", return_value=["F Watcher Operator", "All"]):
            with patch.object(frappe, "session", MagicMock(user="john@example.com")):
                _check_permission()

    def test_guest_blocked(self):
        with patch("frappe.get_roles", return_value=["Guest"]):
            with patch.object(frappe, "session", MagicMock(user="Guest")):
                with self.assertRaises(frappe.PermissionError):
                    _check_permission()


class TestCleanupPreview(unittest.TestCase):
    def _mock_permission(self):
        return patch("f_watcher.actions.cleanup._check_permission", return_value=None)

    def test_preview_known_table(self):
        with self._mock_permission():
            with patch("frappe.db.sql", return_value=[[42]]):
                result = preview("tabError Log", days=30)
        self.assertEqual(result["records_to_delete"], 42)
        self.assertEqual(result["table"], "tabError Log")
        self.assertEqual(result["days"], 30)

    def test_preview_uses_default_days(self):
        default = CLEANUP_RULES["tabActivity Log"]["default_days"]
        with self._mock_permission():
            with patch("frappe.db.sql", return_value=[[0]]):
                result = preview("tabActivity Log")
        self.assertEqual(result["days"], default)

    def test_preview_unknown_table_raises(self):
        with self._mock_permission():
            with self.assertRaises(frappe.ValidationError):
                preview("tabSomeRandomTable", days=30)


class TestCleanupExecute(unittest.TestCase):
    def _mock_permission(self):
        return patch("f_watcher.actions.cleanup._check_permission", return_value=None)

    def _mock_audit(self):
        return patch("f_watcher.actions.cleanup._audit", return_value=None)

    def test_execute_returns_deleted_count(self):
        with self._mock_permission(), self._mock_audit():
            with patch("frappe.db.sql", return_value=[[5]]):
                with patch("frappe.db.commit"):
                    result = execute("tabError Log", days=30, reason="test run")
        self.assertEqual(result["deleted"], 5)

    def test_execute_rollback_on_error(self):
        def boom(*a, **kw):
            raise Exception("DB fail")

        with self._mock_permission(), self._mock_audit():
            with patch("frappe.db.sql", side_effect=boom):
                with patch("frappe.db.rollback") as mock_rollback:
                    with self.assertRaises(Exception):
                        execute("tabError Log", days=30, reason="fail test")
                mock_rollback.assert_called_once()
