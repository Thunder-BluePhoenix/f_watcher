import frappe
from frappe.utils import now_datetime, add_to_date

def collect():
    try:
        process_apm_traces()
    except Exception as e:
        frappe.log_error("F-Watcher APM Collector Failed", str(e))

def process_apm_traces():
    if not frappe.db.exists("DocType", "Monitor"):
        return
        
    time_limit = add_to_date(now_datetime(), minutes=-15)
    
    # 1,000,000 microseconds = 1 second threshold
    slow_queries = frappe.db.sql("""
        SELECT transaction_type, request_method, path, max(duration) as max_duration, count(name) as count
        FROM `tabMonitor`
        WHERE creation >= %s AND duration > 1000000
        GROUP BY path
        ORDER BY max_duration DESC
        LIMIT 5
    """, (time_limit,), as_dict=True)
    
    for q in slow_queries:
        path = q.path or "Unknown Path"
        elapsed_ms = int(q.max_duration / 1000)
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "APM Trace",
            "count": q.count,
            "details": f"Path: {path} | Max Time: {elapsed_ms}ms",
        }).insert(ignore_permissions=True)

    frappe.db.commit()  # BUG-14: commit once after loop, not once per iteration
