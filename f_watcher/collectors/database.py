from __future__ import annotations
import hashlib
import frappe
from frappe.utils import now_datetime

def _sig(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]

def collect(limit: int = 10):
    try:
        rows = frappe.db.sql(
            """
            SELECT DIGEST_TEXT,
                   COUNT_STAR,
                   AVG_TIMER_WAIT/1000000000,
                   MAX_TIMER_WAIT/1000000000
            FROM performance_schema.events_statements_summary_by_digest
            ORDER BY AVG_TIMER_WAIT DESC
            LIMIT %s
            """,
            (int(limit),),
            as_list=True,
        )
    except Exception:
        # performance_schema not enabled → safe skip
        return

    ts = now_datetime()
    for digest_text, count_star, avg_s, max_s in rows:
        frappe.get_doc({
            "doctype": "F Watcher DB Metric",
            "timestamp": ts,
            "site": frappe.local.site,
            "db_name": frappe.conf.db_name,
            "query_signature": _sig(digest_text),
            "executions": int(count_star or 0),
            "avg_time_ms": int((avg_s or 0) * 1000),
            "max_time_ms": int((max_s or 0) * 1000),
        }).insert(ignore_permissions=True)
