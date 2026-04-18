import frappe
from frappe.utils import add_to_date, now_datetime

RETENTION_DAYS = {
    "F Watcher System Metric": 30,
    "F Watcher Redis Metric": 30,
    "F Watcher Queue Metric": 30,
    "F Watcher App Metric": 30,
    "F Watcher DB Metric": 30,
    "F Watcher DB Storage Snapshot": 90,
    "F Watcher DB Table Storage": 90,
    "F Watcher Alert Log": 90,
    "F Watcher Action Audit": 180,
    "F Watcher Uptime Record": 90,
}

def purge():
    total = 0
    for doctype, days in RETENTION_DAYS.items():
        try:
            cutoff = add_to_date(now_datetime(), days=-days)
            count = frappe.db.count(doctype, {"creation": ("<", cutoff)})
            if count:
                frappe.db.delete(doctype, {"creation": ("<", cutoff)})
                frappe.db.commit()
                total += count
        except Exception as e:
            frappe.log_error(f"F-Watcher Retention: failed on {doctype}", str(e))

    if total:
        frappe.logger().info(f"F-Watcher retention purged {total} rows")
