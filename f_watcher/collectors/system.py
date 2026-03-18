from __future__ import annotations
import socket
import psutil
import frappe
from frappe.utils import now_datetime

def collect():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    load1, load5, load15 = psutil.getloadavg()

    frappe.get_doc({
        "doctype": "F Watcher System Metric",
        "timestamp": now_datetime(),
        "site": frappe.local.site,
        "hostname": socket.gethostname(),
        "cpu_percent": float(psutil.cpu_percent(interval=0.5)),
        "ram_percent": float(vm.percent),
        "ram_used_mb": int(vm.used / 1024 / 1024),
        "disk_percent": float(disk.percent),
        "load_1": float(load1),
        "load_5": float(load5),
        "load_15": float(load15),
    }).insert(ignore_permissions=True)
