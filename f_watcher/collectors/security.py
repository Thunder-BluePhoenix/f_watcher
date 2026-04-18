import frappe
from frappe.utils import now_datetime, add_to_date


def collect():
    try:
        track_failed_logins()
        track_active_sessions()
        track_brute_force_by_ip()
        track_suspicious_activity()
    except Exception as e:
        frappe.log_error("F-Watcher Security Collector Failed", str(e))


def track_failed_logins():
    if not frappe.db.exists("DocType", "Activity Log"):
        return
    fifteen_mins_ago = add_to_date(now_datetime(), minutes=-15)
    anomalies = frappe.db.sql("""
        SELECT user, COUNT(name) AS attempts
        FROM `tabActivity Log`
        WHERE subject = 'Failed Login' AND creation >= %s
        GROUP BY user
        HAVING attempts > 5
    """, (fifteen_mins_ago,), as_dict=True)

    for anom in anomalies:
        user = anom.user or "Unknown User"
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": (
                f"Security: {anom.attempts} failed login attempts for "
                f"user {user} in the last 15 minutes."
            ),
            "metric_value": "Security Anomaly",
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def track_brute_force_by_ip():
    if not frappe.db.exists("DocType", "Activity Log"):
        return
    fifteen_mins_ago = add_to_date(now_datetime(), minutes=-15)
    # Detect IPs hammering multiple accounts
    rows = frappe.db.sql("""
        SELECT ip_address, COUNT(DISTINCT user) AS users_hit, COUNT(name) AS attempts
        FROM `tabActivity Log`
        WHERE subject = 'Failed Login'
          AND creation >= %s
          AND ip_address IS NOT NULL
          AND ip_address != ''
        GROUP BY ip_address
        HAVING attempts > 10
    """, (fifteen_mins_ago,), as_dict=True)

    for row in rows:
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": (
                f"Brute-force attempt from IP {row.ip_address}: "
                f"{row.attempts} failed logins against {row.users_hit} account(s)."
            ),
            "metric_value": "Brute Force",
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def track_suspicious_activity():
    if not frappe.db.exists("DocType", "Activity Log"):
        return
    one_hour_ago = add_to_date(now_datetime(), hours=-1)

    # Bulk deletes: any user who deleted > 20 records in the last hour
    bulk_deletes = frappe.db.sql("""
        SELECT user, COUNT(name) AS cnt
        FROM `tabActivity Log`
        WHERE operation = 'Deleted'
          AND creation >= %s
          AND user != 'Administrator'
        GROUP BY user
        HAVING cnt > 20
    """, (one_hour_ago,), as_dict=True)

    for row in bulk_deletes:
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": (
                f"Suspicious bulk delete: user {row.user} deleted "
                f"{row.cnt} records in the last hour."
            ),
            "metric_value": "Suspicious Activity",
        }).insert(ignore_permissions=True)
        frappe.db.commit()

    # Permission changes: any writes to permission-related DocTypes
    perm_changes = frappe.db.sql("""
        SELECT COUNT(name) AS cnt
        FROM `tabActivity Log`
        WHERE creation >= %s
          AND reference_doctype IN (
            'Has Role', 'User Permission', 'Role', 'Custom DocPerm', 'System Settings'
          )
    """, (one_hour_ago,))[0][0] or 0

    if perm_changes > 0:
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "Permission Changes",
            "count": int(perm_changes),
            "details": f"{perm_changes} permission-related change(s) in the last hour.",
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def track_active_sessions():
    active_sessions = frappe.db.sql(
        "SELECT COUNT(user) FROM `tabSessions` WHERE user != 'Guest'"
    )[0][0] or 0

    if active_sessions > 0:
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "Active Sessions",
            "count": active_sessions,
            "details": f"{active_sessions} active authenticated user session(s)",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
