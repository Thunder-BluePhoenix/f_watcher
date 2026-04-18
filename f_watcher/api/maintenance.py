import frappe
from frappe.utils import now_datetime, add_to_date


@frappe.whitelist()
def create_window(title: str, duration_minutes: int, reason: str = ""):
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
    ):
        frappe.throw("Not permitted.", frappe.PermissionError)

    duration_minutes = int(duration_minutes)
    now = now_datetime()
    doc = frappe.get_doc({
        "doctype": "F Watcher Maintenance Window",
        "title": title,
        "starts_at": now,
        "ends_at": add_to_date(now, minutes=duration_minutes),
        "reason": reason,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": doc.name, "ends_at": str(doc.ends_at)}


@frappe.whitelist()
def active_window():
    now = now_datetime()
    rows = frappe.db.get_all(
        "F Watcher Maintenance Window",
        filters={"starts_at": ["<=", now], "ends_at": [">=", now]},
        fields=["name", "title", "ends_at", "reason"],
        order_by="ends_at desc",
        limit=1,
    )
    return rows[0] if rows else None
