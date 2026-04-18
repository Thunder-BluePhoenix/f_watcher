import time
import frappe
from frappe.utils import now_datetime


def collect():
    site = frappe.local.site
    start = time.time()
    status = "up"
    details = ""

    try:
        frappe.db.sql("SELECT 1")
        frappe.cache().ping()
    except Exception as e:
        status = "down"
        details = str(e)[:500]

    elapsed_ms = round((time.time() - start) * 1000, 2)
    if status == "up" and elapsed_ms > 2000:
        status = "degraded"
        details = f"Slow response: {elapsed_ms:.0f}ms"

    frappe.get_doc({
        "doctype": "F Watcher Uptime Record",
        "site": site,
        "timestamp": now_datetime(),
        "status": status,
        "response_ms": elapsed_ms,
        "details": details,
    }).insert(ignore_permissions=True)
    frappe.db.commit()
