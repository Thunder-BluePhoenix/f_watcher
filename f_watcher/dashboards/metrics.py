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
    big_tables = frappe.db.get_all(
        "F Watcher DB Table Storage",
        fields=["timestamp","table_name","total_mb","rows_est","importance","importance_note","cleanup_allowed","cleanup_hint"],
        order_by="total_mb desc",
        limit=10,
    )

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
