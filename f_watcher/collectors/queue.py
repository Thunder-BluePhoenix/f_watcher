from __future__ import annotations
import frappe
from rq import Queue
from frappe.utils import now_datetime
from frappe.utils.background_jobs import get_redis_conn

def collect():
    redis = get_redis_conn()

    for qname in ["short", "default", "long"]:
        q = Queue(qname, connection=redis)
        frappe.get_doc({
            "doctype": "F Watcher Queue Metric",
            "timestamp": now_datetime(),
            "site": frappe.local.site,
            "queue_name": qname,
            "job_count": int(q.count),
            "failed_count": int(q.failed_job_registry.count),
            "active_workers": int(len(q.workers)),
        }).insert(ignore_permissions=True)
