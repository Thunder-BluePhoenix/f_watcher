import csv
import io
import frappe
from frappe.utils import add_to_date


def _check_permission():
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
        or "F Watcher Viewer" in frappe.get_roles()
    ):
        frappe.throw("Not permitted.", frappe.PermissionError)


@frappe.whitelist()
def system_metrics_csv(hours: int = 24):
    _check_permission()
    hours = min(int(hours), 168)
    since = add_to_date(None, hours=-hours)
    rows = frappe.db.sql("""
        SELECT `timestamp`, hostname, cpu_percent, ram_percent,
               disk_percent, load_1, load_5, load_15
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %(since)s
        ORDER BY `timestamp` ASC
        LIMIT 10000
    """, {"since": since}, as_dict=True)

    fields = ["timestamp", "hostname", "cpu_percent", "ram_percent",
              "disk_percent", "load_1", "load_5", "load_15"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fields})

    return out.getvalue()


@frappe.whitelist()
def queue_metrics_csv(hours: int = 24):
    _check_permission()
    hours = min(int(hours), 168)
    since = add_to_date(None, hours=-hours)
    rows = frappe.db.sql("""
        SELECT `timestamp`, queue_name, job_count, failed_count, active_workers
        FROM `tabF Watcher Queue Metric`
        WHERE `timestamp` >= %(since)s
        ORDER BY `timestamp` ASC
        LIMIT 10000
    """, {"since": since}, as_dict=True)

    fields = ["timestamp", "queue_name", "job_count", "failed_count", "active_workers"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fields})

    return out.getvalue()
