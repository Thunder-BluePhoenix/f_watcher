import frappe
from frappe.utils import now_datetime


def _check_permission():
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
    ):
        frappe.throw("Not permitted.", frappe.PermissionError)


@frappe.whitelist()
def list_sessions():
    _check_permission()
    return frappe.db.sql("""
        SELECT sid, user, ipaddress, lastupdate, status
        FROM `tabSessions`
        WHERE user != 'Guest'
          AND user IS NOT NULL
        ORDER BY lastupdate DESC
        LIMIT 50
    """, as_dict=True)


@frappe.whitelist()
def force_logout(session_id: str):
    _check_permission()
    if not session_id:
        frappe.throw("session_id is required.")

    row = frappe.db.sql(
        "SELECT sid, user FROM `tabSessions` WHERE sid = %s",
        (session_id,), as_dict=True
    )
    if not row:
        frappe.throw("Session not found.")
    session_user = row[0].user

    frappe.db.sql("DELETE FROM `tabSessions` WHERE sid = %s", (session_id,))
    frappe.db.commit()

    frappe.get_doc({
        "doctype": "F Watcher Action Audit",
        "timestamp": now_datetime(),
        "site": frappe.local.site,
        "user": frappe.session.user,
        "action": "force_logout",
        "target": session_user,
        "reason": f"Session {session_id[:12]}… terminated via Control Center",
        "result": "Success",
        "details": f"Forced logout for user: {session_user}",
    }).insert(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "ok", "user": session_user}
