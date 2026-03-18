import frappe
from frappe.utils import now_datetime, add_to_date

def collect():
    try:
        track_failed_logins()
        track_active_sessions()
    except Exception as e:
        frappe.log_error("F-Watcher Security Collector Failed", str(e))

def track_failed_logins():
    # Look for Failed Login attempts in the last 15 minutes
    if not frappe.db.exists("DocType", "Activity Log"):
        return
        
    fifteen_mins_ago = add_to_date(now_datetime(), minutes=-15)
    
    # In Activity Log, communication_medium is sometimes used to store IP, or it might be in subject/user.
    # Frappe logs 'Failed Login' with user, but we will just count global failed logins if IP is hard to parse.
    anomalies = frappe.db.sql("""
        SELECT user, count(name) as attempts
        FROM `tabActivity Log`
        WHERE subject='Failed Login' and creation >= %s
        GROUP BY user
        HAVING attempts > 5
    """, (fifteen_mins_ago,), as_dict=True)
    
    for anom in anomalies:
        user = anom.user or 'Unknown User'
        msg = f"Security Warning: {anom.attempts} failed login attempts for user {user} in the last 15 minutes."
        
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": msg,
            "metric_value": "Security Anomaly"
        }).insert(ignore_permissions=True)
        frappe.db.commit()

def track_active_sessions():
    # Only authenticated users
    active_sessions = frappe.db.sql("SELECT count(user) FROM tabSessions WHERE user != 'Guest'")[0][0]
    
    frappe.get_doc({
        "doctype": "F Watcher App Metric",
        "timestamp": now_datetime(),
        "metric_type": "Active Sessions",
        "count": active_sessions,
        "details": "Active concurrent users"
    }).insert(ignore_permissions=True)
    frappe.db.commit()

