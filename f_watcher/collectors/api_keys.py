import frappe
from frappe.utils import now_datetime, add_to_date


def collect():
    try:
        _check_stale_keys()
        _check_new_keys()
    except Exception as e:
        frappe.log_error("F-Watcher API Key Collector Failed", str(e))


def _check_stale_keys():
    ninety_days_ago = add_to_date(now_datetime(), days=-90)
    stale = frappe.db.sql("""
        SELECT u.name AS user, ak.api_key
        FROM `tabUser` u
        JOIN `tabUser` ak ON ak.name = u.name
        WHERE u.api_key IS NOT NULL
          AND u.api_key != ''
          AND (u.api_secret_expiry IS NULL OR u.api_secret_expiry < %(cutoff)s)
          AND u.enabled = 1
        LIMIT 20
    """, {"cutoff": ninety_days_ago}, as_dict=True)

    if stale:
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "Stale API Keys",
            "count": len(stale),
            "details": f"{len(stale)} API key(s) with no recent expiry reset (>90 days old).",
        }).insert(ignore_permissions=True)
        frappe.db.commit()


def _check_new_keys():
    one_day_ago = add_to_date(now_datetime(), days=-1)
    new_keys = frappe.db.sql("""
        SELECT COUNT(*) AS cnt
        FROM `tabUser`
        WHERE api_key IS NOT NULL
          AND api_key != ''
          AND creation >= %(since)s
    """, {"since": one_day_ago})[0][0] or 0

    if new_keys > 0:
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "New API Keys",
            "count": int(new_keys),
            "details": f"{new_keys} API key(s) created or reset in the last 24 hours.",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
