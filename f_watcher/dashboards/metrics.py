from __future__ import annotations
import frappe

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
