import frappe
from frappe.utils import now_datetime, add_to_date

def collect():
    try:
        check_integration_failures()
    except Exception as e:
        frappe.log_error("F-Watcher Integration Collector Failed", str(e))

def check_integration_failures():
    if not frappe.db.exists("DocType", "Integration Request"):
        return
        
    # Check failures in the last 15 minutes
    time_limit = add_to_date(now_datetime(), minutes=-15)
    
    fails = frappe.db.count("Integration Request", {"status": "Failed", "creation": [">=", time_limit]})
    if fails > 0:
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "Integration Request",
            "count": fails,
            "details": f"{fails} failed integration/webhook requests in the last 15 minutes."
        }).insert(ignore_permissions=True)
        frappe.db.commit()
