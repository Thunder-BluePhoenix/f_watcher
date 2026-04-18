from __future__ import annotations
import frappe

@frappe.whitelist()
def history(hours: int = 6):
    hours = min(int(hours), 168)  # cap at 7 days
    since = frappe.utils.add_to_date(None, hours=-hours)

    system = frappe.db.sql("""
        SELECT
            DATE_FORMAT(`timestamp`, '%%Y-%%m-%%d %%H:%%i:00') AS bucket,
            AVG(cpu_percent)  AS cpu,
            AVG(ram_percent)  AS ram,
            AVG(disk_percent) AS disk
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %(since)s
        GROUP BY bucket
        ORDER BY bucket ASC
        LIMIT 500
    """, {"since": since}, as_dict=True)

    queues = frappe.db.sql("""
        SELECT
            DATE_FORMAT(`timestamp`, '%%Y-%%m-%%d %%H:%%i:00') AS bucket,
            queue_name,
            AVG(job_count)    AS job_count,
            SUM(failed_count) AS failed_count
        FROM `tabF Watcher Queue Metric`
        WHERE `timestamp` >= %(since)s
        GROUP BY bucket, queue_name
        ORDER BY bucket ASC
        LIMIT 1000
    """, {"since": since}, as_dict=True)

    db_size = frappe.db.sql("""
        SELECT
            DATE_FORMAT(`timestamp`, '%%Y-%%m-%%d %%H:00:00') AS bucket,
            AVG(total_mb) AS total_mb
        FROM `tabF Watcher DB Storage Snapshot`
        WHERE `timestamp` >= %(since)s
        GROUP BY bucket
        ORDER BY bucket ASC
        LIMIT 500
    """, {"since": since}, as_dict=True)

    return {"system": system, "queues": queues, "db_size": db_size}


@frappe.whitelist()
def collector_status():
    collectors = [
        ("System",      "F Watcher System Metric",       5),
        ("Queue",       "F Watcher Queue Metric",         5),
        ("DB Storage",  "F Watcher DB Storage Snapshot", 10),
        ("DB Queries",  "F Watcher DB Metric",           10),
        ("Redis",       "F Watcher Redis Metric",        10),
        ("App Health",  "F Watcher App Metric",          10),
    ]
    result = []
    now = frappe.utils.now_datetime()
    for label, doctype, max_minutes in collectors:
        last = frappe.db.get_value(doctype, {}, "creation", order_by="creation desc")
        if not last:
            status = "never"
            minutes_ago = None
        else:
            diff = (now - frappe.utils.get_datetime(last)).total_seconds() / 60
            minutes_ago = int(diff)
            status = "ok" if diff <= max_minutes else "stale"
        result.append({"label": label, "status": status, "last": str(last or ""), "minutes_ago": minutes_ago})
    return result


@frappe.whitelist()
def latest():
    system = frappe.db.get_all(
        "F Watcher System Metric",
        fields=["timestamp","hostname","cpu_percent","ram_percent","disk_percent","load_1","load_5","load_15"],
        order_by="timestamp desc",
        limit=1,
    )
    db_snap = frappe.db.get_all(
        "F Watcher DB Storage Snapshot",
        fields=["timestamp","db_name","total_mb","data_mb","index_mb","tables_count","hostname"],
        order_by="timestamp desc",
        limit=1,
    )
    queues = frappe.db.get_all(
        "F Watcher Queue Metric",
        fields=["timestamp","queue_name","job_count","failed_count","active_workers"],
        order_by="timestamp desc",
        limit=10,
    )
    big_tables = frappe.db.sql("""
        SELECT t.table_name, t.total_mb, t.rows_est,
               t.importance, t.importance_note,
               t.cleanup_allowed, t.cleanup_hint, t.`timestamp`
        FROM `tabF Watcher DB Table Storage` t
        INNER JOIN (
            SELECT table_name, MAX(`timestamp`) AS latest_ts
            FROM `tabF Watcher DB Table Storage`
            GROUP BY table_name
        ) latest ON t.table_name = latest.table_name
               AND t.`timestamp` = latest.latest_ts
        ORDER BY t.total_mb DESC
        LIMIT 10
    """, as_dict=True)

    return {
        "system": system[0] if system else None,
        "db_snapshot": db_snap[0] if db_snap else None,
        "queues": queues,
        "big_tables": big_tables,
    }

@frappe.whitelist()
def audit(limit: int = 20):
    return frappe.db.get_all(
        "F Watcher Action Audit",
        fields=["creation", "user", "action", "target", "result", "reason"],
        order_by="creation desc",
        limit=int(limit),
    )
