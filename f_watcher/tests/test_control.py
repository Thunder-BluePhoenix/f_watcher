from unittest.mock import patch, MagicMock
import frappe
import unittest
from f_watcher.actions import control


class TestControlRun(unittest.TestCase):
    def _mock_audit(self):
        return patch("f_watcher.actions.control._audit", return_value=None)

    def test_run_success(self):
        with self._mock_audit(), \
             patch("subprocess.check_output", return_value=b"ok"):
            result = control._run("restart_workers", "workers", "test")
        self.assertEqual(result, "Success")

    def test_run_failure_returns_failed(self):
        with self._mock_audit(), \
             patch("subprocess.check_output", side_effect=Exception("permission denied")):
            result = control._run("restart_workers", "workers", "test")
        self.assertEqual(result, "Failed")

    def test_run_calls_audit(self):
        with patch("f_watcher.actions.control._audit") as mock_audit, \
             patch("subprocess.check_output", return_value=b"ok"):
            control._run("restart_scheduler", "scheduler", "reason text")

        mock_audit.assert_called_once()
        args = mock_audit.call_args[0]
        self.assertEqual(args[0], "restart_scheduler")
        self.assertEqual(args[2], "reason text")
        self.assertEqual(args[3], "Success")


class TestControlPermission(unittest.TestCase):
    def test_restart_workers_requires_operator(self):
        with patch("frappe.only_for") as mock_only_for, \
             patch("f_watcher.actions.control._run", return_value="Success"):
            control.restart_workers("test reason")
        mock_only_for.assert_called_once_with("F Watcher Operator")

    def test_restart_scheduler_requires_operator(self):
        with patch("frappe.only_for") as mock_only_for, \
             patch("f_watcher.actions.control._run", return_value="Success"):
            control.restart_scheduler("test reason")
        mock_only_for.assert_called_once_with("F Watcher Operator")
