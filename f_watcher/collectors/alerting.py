from __future__ import annotations
import frappe
from frappe.utils import now_datetime, time_diff_in_seconds


def is_maintenance_active():
    now = now_datetime()
    return frappe.db.exists("F Watcher Maintenance Window", {
        "starts_at": ["<=", now],
        "ends_at":   [">=", now],
    })


def _run_remediation(action: str, rule):
    try:
        if action.startswith("retry_failed_jobs_"):
            queue = action.replace("retry_failed_jobs_", "")
            from f_watcher.actions.queue import retry_failed_jobs
            retry_failed_jobs(queue_name=queue)
        elif action == "clear_cache":
            frappe.cache().flushdb()
        _audit_remediation(rule, action, "Success")
    except Exception as e:
        _audit_remediation(rule, action, f"Failed: {e}")


def _audit_remediation(rule, action, result):
    frappe.get_doc({
        "doctype": "F Watcher Action Audit",
        "timestamp": now_datetime(),
        "site": frappe.local.site,
        "user": "Administrator",
        "action": f"auto_remediation:{action}",
        "target": rule.rule_name,
        "reason": "Auto-remediation triggered by alert rule",
        "result": result,
        "details": f"Rule: {rule.name}",
    }).insert(ignore_permissions=True)
    frappe.db.commit()


def evaluate_and_alert():
    if is_maintenance_active():
        return  # silently skip all alerts during maintenance

    rules = frappe.get_all("F Watcher Alert Rule", filters={"is_active": 1}, fields=["*"])

    for rule in rules:
        try:
            latest_metric = get_latest_metric(rule.metric_type)
            if not latest_metric:
                continue

            value = latest_metric.get(rule.property_name)
            if value is None:
                continue

            cooldown_secs = (rule.cooldown_minutes or 15) * 60

            if evaluate_condition(value, rule.condition, rule.threshold_value):
                # 3.8a: use per-rule cooldown_minutes
                if rule.last_triggered:
                    diff = time_diff_in_seconds(now_datetime(), rule.last_triggered)
                    if diff < cooldown_secs:
                        continue

                msg = (
                    f"Alert: {rule.rule_name} — "
                    f"{rule.property_name} is {value} "
                    f"(threshold: {rule.condition} {rule.threshold_value})"
                )
                status = "Triggered"

                if rule.alert_channel == "Webhook" and rule.webhook_url:
                    try:
                        import requests
                        requests.post(rule.webhook_url, json={"text": msg}, timeout=5)
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
                frappe.db.commit()

                # 4.2: auto-remediation
                if getattr(rule, "auto_remediate", 0) and getattr(rule, "remediation_action", None):
                    _run_remediation(rule.remediation_action, rule)

            else:
                # 3.8b: auto-resolve — insert Resolved record if last log was Triggered
                last_log = frappe.db.get_value(
                    "F Watcher Alert Log",
                    {"alert_rule": rule.name},
                    ["status", "name"],
                    order_by="timestamp desc",
                    as_dict=True,
                )
                if last_log and last_log.status == "Triggered":
                    frappe.get_doc({
                        "doctype": "F Watcher Alert Log",
                        "alert_rule": rule.name,
                        "timestamp": now_datetime(),
                        "status": "Resolved",
                        "message": f"Alert resolved: {rule.property_name} is now {value}",
                        "metric_value": str(value),
                    }).insert(ignore_permissions=True)
                    frappe.db.commit()

        except Exception as e:
            frappe.log_error(title="F-Watcher Alerting Engine Failed", message=str(e))


@frappe.whitelist()
def test_rule(rule_name: str):
    rule = frappe.get_doc("F Watcher Alert Rule", rule_name)
    metric = get_latest_metric(rule.metric_type)
    if not metric:
        return {"status": "no_data", "message": "No metric data available yet."}
    value = metric.get(rule.property_name)
    if value is None:
        return {"status": "no_data", "message": f"Property '{rule.property_name}' not found in latest metric."}
    would_fire = evaluate_condition(value, rule.condition, rule.threshold_value)
    return {
        "status": "would_fire" if would_fire else "ok",
        "current_value": value,
        "threshold": rule.threshold_value,
        "condition": rule.condition,
        "message": (
            f"Would fire: {rule.property_name} = {value} {rule.condition} {rule.threshold_value}"
            if would_fire else
            f"Would NOT fire: {rule.property_name} = {value} (threshold: {rule.condition} {rule.threshold_value})"
        ),
    }


def get_latest_metric(metric_type):
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
