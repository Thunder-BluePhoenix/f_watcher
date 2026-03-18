import frappe
from frappe.utils import now_datetime, add_to_date

def collect():
    try:
        collect_error_logs()
        collect_scheduled_jobs()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(title="F-Watcher App Health Collector Failed", message=str(e))

def collect_error_logs():
    # Count Error Logs created in the last 5 minutes, grouped by 'method'
    five_mins_ago = add_to_date(now_datetime(), minutes=-5)
    
    errors = frappe.db.sql("""
        SELECT method, count(name) as err_count
        FROM `tabError Log`
        WHERE creation >= %s
        GROUP BY method
    """, (five_mins_ago,), as_dict=True)
    
    for err in errors:
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "Error Log",
            "count": err.err_count,
            "details": f"Method: {err.method}"
        }).insert(ignore_permissions=True)

def collect_scheduled_jobs():
    if not frappe.db.exists("DocType", "Scheduled Job Type"):
        return
        
    failed_jobs = frappe.get_all("Scheduled Job Type", filters={"status": "Failed"}, fields=["name"])
    if failed_jobs:
        job_names = [j.name for j in failed_jobs]
        details = "Failed Jobs: " + ", ".join(job_names[:5])
        if len(job_names) > 5:
            details += f" ... and {len(job_names) - 5} more."
            
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "Scheduled Job",
            "count": len(failed_jobs),
            "details": details
        }).insert(ignore_permissions=True)
