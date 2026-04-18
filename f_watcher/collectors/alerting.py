from __future__ import annotations
import frappe
from frappe.utils import now_datetime, time_diff_in_seconds

def evaluate_and_alert():
    rules = frappe.get_all("F Watcher Alert Rule", filters={"is_active": 1}, fields=["*"])

    for rule in rules:
        try:
            latest_metric = get_latest_metric(rule.metric_type)
            if not latest_metric:
                continue

            value = latest_metric.get(rule.property_name)
            if value is None:
                continue

            if evaluate_condition(value, rule.condition, rule.threshold_value):
                # BUG-09 fix: check cooldown before doing anything else
                if rule.last_triggered:
                    diff = time_diff_in_seconds(now_datetime(), rule.last_triggered)
                    if diff < 900:
                        continue

                msg = (
                    f"Alert: {rule.rule_name} — "
                    f"{rule.property_name} is {value} "
                    f"(threshold: {rule.condition} {rule.threshold_value})"
                )
                status = "Triggered"

                # BUG-07 fix: use requests instead of frappe.make_post_request (doesn't exist)
                if rule.alert_channel == "Webhook" and rule.webhook_url:
                    try:
                        import requests
                        requests.post(
                            rule.webhook_url,
                            json={"text": msg},
                            timeout=5,
                        )
                    except Exception as e:
                        status = "Failed to Send"
                        msg += f" [Webhook error: {e}]"

                elif rule.alert_channel == "Email" and rule.email_address:
                    try:
                        frappe.sendmail(
                            recipients=[rule.email_address],
                            subject=f"F-Watcher Alert: {rule.rule_name}",
                            message=msg,
                        )
                    except Exception as e:
                        status = "Failed to Send"
                        msg += f" [Email error: {e}]"

                # BUG-08 fix: implement System Notification channel
                elif rule.alert_channel == "System Notification":
                    frappe.publish_realtime(
                        event="fw_alert",
                        message={"title": rule.rule_name, "message": msg, "indicator": "red"},
                        after_commit=True,
                    )

                frappe.get_doc({
                    "doctype": "F Watcher Alert Log",
                    "alert_rule": rule.name,
                    "timestamp": now_datetime(),
                    "status": status,
                    "message": msg,
                    "metric_value": str(value),
                }).insert(ignore_permissions=True)

                frappe.db.set_value("F Watcher Alert Rule", rule.name, "last_triggered", now_datetime())
                frappe.db.commit()  # BUG-09 fix: commit after every alert

        except Exception as e:
            frappe.log_error(title="F-Watcher Alerting Engine Failed", message=str(e))


def get_latest_metric(metric_type):
    # BUG-10 fix: added Redis; Backup and Security are alert-only, no metric doctype
    mapping = {
        "System":   "F Watcher System Metric",
        "Database": "F Watcher DB Metric",
        "Queue":    "F Watcher Queue Metric",
        "Redis":    "F Watcher Redis Metric",
    }
    doctype = mapping.get(metric_type)
    if not doctype:
        return None

    res = frappe.get_all(doctype, fields=["*"], order_by="creation desc", limit=1)
    return res[0] if res else None


def evaluate_condition(current, condition, threshold):
    try:
        current   = float(current)
        threshold = float(threshold)
    except (TypeError, ValueError):
        return False

    if condition == ">":  return current > threshold
    if condition == "<":  return current < threshold
    if condition == ">=": return current >= threshold
    if condition == "<=": return current <= threshold
    if condition == "==": return current == threshold
    return False
