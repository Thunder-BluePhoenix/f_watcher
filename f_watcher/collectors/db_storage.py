from __future__ import annotations
import socket
import frappe
from frappe.utils import now_datetime

IMPORTANCE_MAP = [
    ("tabGL Entry", "Ledger/Accounting", "Accounting ledger; large size can slow financial reports."),
    ("tabStock Ledger Entry", "Stock/Inventory", "Inventory movements; large size slows stock reports/valuation."),
    ("tabError Log", "Logs/Audit", "Error logs; safe to clear old entries to reduce DB bloat."),
    ("tabActivity Log", "Logs/Audit", "User activity logs; can grow fast in busy systems."),
    ("tabVersion", "Logs/Audit", "Document version history; can grow large over time."),
    ("tabIntegration Request", "Integration/Sync", "Integration logs; failures/retries can bloat DB."),
    ("tabWebhook Request Log", "Integration/Sync", "Webhook logs; common bloat source with integrations."),
    ("tabFile", "Attachments/Files", "File metadata; hints attachment activity and storage pressure."),
]

CLEANUP_ALLOWED = {
    "tabError Log": "Safe to clear old error logs (does not affect business transactions).",
    "tabActivity Log": "Safe to clear old activity logs (audit/history).",
    "tabIntegration Request": "Safe to clear old integration logs (keep recent for troubleshooting).",
    "tabWebhook Request Log": "Safe to clear old webhook logs (keep recent for troubleshooting).",
    "tabVersion": "Safe to reduce old version history if needed (keep enough for audit).",
}

def _classify(table_name: str):
    for t, cat, note in IMPORTANCE_MAP:
        if table_name == t:
            return cat, note
    if table_name.startswith("tab"):
        return "System/Core", "Core ERPNext/Frappe table; monitor growth trend and indexing."
    return "Custom/Unknown", "Custom table; review purpose and retention needs."

def collect(top_n: int = 25):
    ts = now_datetime()
    site = frappe.local.site
    host = socket.gethostname()
    db_name = frappe.conf.db_name

    db_row = frappe.db.sql(
        """
        SELECT
          IFNULL(SUM(data_length + index_length), 0) / 1024 / 1024 AS total_mb,
          IFNULL(SUM(data_length), 0) / 1024 / 1024 AS data_mb,
          IFNULL(SUM(index_length), 0) / 1024 / 1024 AS index_mb,
          COUNT(*) AS tables_count
        FROM information_schema.tables
        WHERE table_schema = %s
        """,
        (db_name,),
        as_dict=True,
    )[0]

    frappe.get_doc({
        "doctype": "F Watcher DB Storage Snapshot",
        "timestamp": ts,
        "site": site,
        "hostname": host,
        "db_name": db_name,
        "total_mb": float(db_row.total_mb),
        "data_mb": float(db_row.data_mb),
        "index_mb": float(db_row.index_mb),
        "tables_count": int(db_row.tables_count),
    }).insert(ignore_permissions=True)

    tables = frappe.db.sql(
        """
        SELECT table_name, engine, table_rows,
               (data_length / 1024 / 1024) AS data_mb,
               (index_length / 1024 / 1024) AS index_mb,
               ((data_length + index_length) / 1024 / 1024) AS total_mb
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY (data_length + index_length) DESC
        LIMIT %s
        """,
        (db_name, int(top_n)),
        as_dict=True,
    )

    for r in tables:
        importance, note = _classify(r.table_name)
        cleanup_allowed = 1 if r.table_name in CLEANUP_ALLOWED else 0
        cleanup_hint = CLEANUP_ALLOWED.get(r.table_name, "")

        frappe.get_doc({
            "doctype": "F Watcher DB Table Storage",
            "timestamp": ts,
            "site": site,
            "hostname": host,
            "db_name": db_name,
            "table_name": r.table_name,
            "engine": r.engine,
            "rows_est": int(r.table_rows or 0),
            "data_mb": float(r.data_mb or 0),
            "index_mb": float(r.index_mb or 0),
            "total_mb": float(r.total_mb or 0),
            "importance": importance,
            "importance_note": note,
            "cleanup_allowed": cleanup_allowed,
            "cleanup_hint": cleanup_hint,
        }).insert(ignore_permissions=True)
