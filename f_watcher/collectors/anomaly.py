from __future__ import annotations
import frappe
from frappe.utils import add_to_date, now_datetime

CHECKS = [
    {
        "label": "CPU spike",
        "doctype": "F Watcher System Metric",
        "field": "cpu_percent",
        "window_hours": 24,
        "sigma_threshold": 2.5,
    },
    {
        "label": "RAM spike",
        "doctype": "F Watcher System Metric",
        "field": "ram_percent",
        "window_hours": 48,
        "sigma_threshold": 2.0,
    },
    {
        "label": "Queue depth spike",
        "doctype": "F Watcher Queue Metric",
        "field": "job_count",
        "window_hours": 24,
        "sigma_threshold": 3.0,
    },
]


def collect():
    try:
        for check in CHECKS:
            _evaluate(check)
    except Exception as e:
        frappe.log_error("F-Watcher Anomaly Collector Failed", str(e))


def _evaluate(check: dict):
    since = add_to_date(None, hours=-(check["window_hours"]))

    stats = frappe.db.sql(f"""
        SELECT
            AVG(`{check['field']}`)    AS mean,
            STDDEV(`{check['field']}`) AS stddev,
            MAX(`{check['field']}`)    AS latest_max
        FROM `tab{check['doctype']}`
        WHERE `timestamp` >= %(since)s
    """, {"since": since}, as_dict=True)

    if not stats:
        return
    row = stats[0]
    if row.stddev is None or float(row.stddev) == 0:
        return

    mean       = float(row.mean)
    stddev     = float(row.stddev)
    latest_max = float(row.latest_max)
    z_score    = (latest_max - mean) / stddev

    if z_score >= check["sigma_threshold"]:
        _log_anomaly(check, mean, stddev, latest_max, z_score)


def _log_anomaly(check, mean, stddev, latest_max, z_score):
    msg = (
        f"Anomaly detected: {check['label']} reached {latest_max:.1f} "
        f"(mean={mean:.1f}, σ={stddev:.1f}, z={z_score:.2f})"
    )
    frappe.get_doc({
        "doctype": "F Watcher Alert Log",
        "timestamp": now_datetime(),
        "status": "Triggered",
        "message": msg,
        "metric_value": str(latest_max),
    }).insert(ignore_permissions=True)
    frappe.db.commit()
