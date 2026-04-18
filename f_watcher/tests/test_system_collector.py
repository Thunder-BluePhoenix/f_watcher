from unittest.mock import patch, MagicMock
import frappe
import unittest
from f_watcher.collectors import system


class TestSystemCollector(unittest.TestCase):
    def _fake_vm(self):
        vm = MagicMock()
        vm.percent = 55.0
        vm.used = 4 * 1024 * 1024 * 1024  # 4 GB
        return vm

    def _fake_disk(self):
        disk = MagicMock()
        disk.percent = 40.0
        return disk

    def test_collect_inserts_one_doc(self):
        inserted = []

        def fake_get_doc(data):
            doc = MagicMock()
            doc.insert = MagicMock(side_effect=lambda **kw: inserted.append(data))
            return doc

        with patch("psutil.virtual_memory", return_value=self._fake_vm()), \
             patch("psutil.disk_usage", return_value=self._fake_disk()), \
             patch("psutil.getloadavg", return_value=(0.5, 0.4, 0.3)), \
             patch("psutil.cpu_percent", return_value=20.0), \
             patch("socket.gethostname", return_value="test-host"), \
             patch("frappe.get_doc", side_effect=fake_get_doc), \
             patch("frappe.local", MagicMock(site="test.localhost")):
            system.collect()

        self.assertEqual(len(inserted), 1)
        doc = inserted[0]
        self.assertEqual(doc["doctype"], "F Watcher System Metric")
        self.assertEqual(doc["hostname"], "test-host")
        self.assertAlmostEqual(doc["ram_percent"], 55.0)
        self.assertEqual(doc["ram_used_mb"], 4096)

    def test_collect_cpu_percent_is_float(self):
        inserted = []

        def fake_get_doc(data):
            doc = MagicMock()
            doc.insert = MagicMock(side_effect=lambda **kw: inserted.append(data))
            return doc

        with patch("psutil.virtual_memory", return_value=self._fake_vm()), \
             patch("psutil.disk_usage", return_value=self._fake_disk()), \
             patch("psutil.getloadavg", return_value=(1.0, 0.9, 0.8)), \
             patch("psutil.cpu_percent", return_value=75), \
             patch("socket.gethostname", return_value="h"), \
             patch("frappe.get_doc", side_effect=fake_get_doc), \
             patch("frappe.local", MagicMock(site="x")):
            system.collect()

        self.assertIsInstance(inserted[0]["cpu_percent"], float)
