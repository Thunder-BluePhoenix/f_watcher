from __future__ import annotations
import frappe
from frappe.utils import now_datetime

CLEANUP_RULES = {
    "tabError Log": {
        "label": "System error logs",
        "default_days": 30,
        "where": "creation < DATE_SUB(NOW(), INTERVAL %(days)s DAY)",
    },
    "tabActivity Log": {
        "label": "User activity logs",
        "default_days": 90,
        "where": "creation < DATE_SUB(NOW(), INTERVAL %(days)s DAY)",
    },
    "tabIntegration Request": {
        "label": "Integration API logs",
        "default_days": 14,
        "where": "creation < DATE_SUB(NOW(), INTERVAL %(days)s DAY)",
    },
    "tabWebhook Request Log": {
        "label": "Webhook logs",
        "default_days": 14,
        "where": "creation < DATE_SUB(NOW(), INTERVAL %(days)s DAY)",
    },
    "tabVersion": {
        "label": "Document version history",
        "default_days": 180,
        "where": "creation < DATE_SUB(NOW(), INTERVAL %(days)s DAY)",
    },
}

def _check_permission():
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
    ):
        frappe.throw("Not permitted. Requires System Manager or F Watcher Operator role.",
                     frappe.PermissionError)

@frappe.whitelist()
def preview(table: str, days: int | None = None):
    _check_permission()
    rule = _rule(table)
    days = int(days or rule["default_days"])

    count = frappe.db.sql(
        f"SELECT COUNT(*) FROM `{table}` WHERE {rule['where']}",
        {"days": days},
    )[0][0]

    return {
        "table": table,
        "days": days,
        "records_to_delete": int(count),
        "description": rule["label"],
        "warning": "This cannot be undone. If unsure, take a backup first.",
    }

@frappe.whitelist()
def execute(table: str, days: int, reason: str):
    _check_permission()
    rule = _rule(table)
    days = int(days)

    try:
        deleted = frappe.db.sql(
            f"SELECT COUNT(*) FROM `{table}` WHERE {rule['where']}",
            {"days": days},
        )[0][0]
        frappe.db.sql(
            f"DELETE FROM `{table}` WHERE {rule['where']}",
            {"days": days},
        )
        frappe.db.commit()

        _audit("cleanup", table, reason, "Success", f"Deleted {deleted} rows older than {days} days.")
        return {"deleted": int(deleted)}
    except Exception as e:
        frappe.db.rollback()
        _audit("cleanup", table, reason, "Failed", str(e))
        raise

def _get_all_rules():
    rules = dict(CLEANUP_RULES)
    try:
        custom = frappe.get_all(
            "F Watcher Cleanup Rule",
            filters={"is_active": 1},
            fields=["table_name", "label", "default_days", "where_clause"],
        )
        for r in custom:
            rules[r.table_name] = {
                "label": r.label,
                "default_days": r.default_days,
                "where": r.where_clause,
            }
    except Exception:
        pass
    return rules


def _rule(table: str):
    all_rules = _get_all_rules()
    if table not in all_rules:
        frappe.throw("Cleanup not allowed for this table.")
    return all_rules[table]

def _audit(action: str, target: str, reason: str, result: str, details: str):
    frappe.get_doc({
        "doctype": "F Watcher Action Audit",
        "timestamp": now_datetime(),
        "site": frappe.local.site,
        "user": frappe.session.user,
        "action": action,
        "target": target,
        "reason": reason or "",
        "result": result,
        "details": details or "",
    }).insert(ignore_permissions=True)
