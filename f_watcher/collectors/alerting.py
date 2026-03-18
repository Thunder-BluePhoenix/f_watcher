import frappe
from frappe.utils import now_datetime, time_diff_in_seconds
import json

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
                # Check cooldown (avoid spamming every minute, e.g. 15 min cooldown)
                if rule.last_triggered:
                    diff = time_diff_in_seconds(now_datetime(), rule.last_triggered)
                    if diff < 900:  # 15 minutes cooldown
                        continue
                        
                # Trigger alert!
                msg = f"Alert triggered for {rule.rule_name}: {rule.property_name} is {value} (Threshold: {rule.condition} {rule.threshold_value})"
                status = "Triggered"
                
                if rule.alert_channel == "Webhook" and rule.webhook_url:
                    try:
                        frappe.make_post_request(url=rule.webhook_url, data=json.dumps({"text": msg}))
                    except Exception as e:
                        status = "Failed to Send"
                        msg += f" [Webhook failed: {e}]"
                        
                elif rule.alert_channel == "Email" and rule.email_address:
                    frappe.sendmail(recipients=[rule.email_address], subject=f"F-Watcher Alert: {rule.rule_name}", content=msg)
                
                # Log it
                frappe.get_doc({
                    "doctype": "F Watcher Alert Log",
                    "alert_rule": rule.name,
                    "timestamp": now_datetime(),
                    "status": status,
                    "message": msg,
                    "metric_value": str(value)
                }).insert(ignore_permissions=True)
                
                # Update last triggered
                frappe.db.set_value("F Watcher Alert Rule", rule.name, "last_triggered", now_datetime())
                
        except Exception as e:
            frappe.log_error(title="F-Watcher Alerting Engine Failed", message=str(e))

def get_latest_metric(metric_type):
    # Map Metric Type to Doctype Name
    mapping = {
        "System": "F Watcher System Metric",
        "Database": "F Watcher DB Metric",
        "Queue": "F Watcher Queue Metric"
    }
    doctype = mapping.get(metric_type)
    if not doctype:
        return None
        
    res = frappe.get_all(doctype, fields=["*"], order_by="creation desc", limit=1)
    return res[0] if res else None

def evaluate_condition(current, condition, threshold):
    current = float(current)
    threshold = float(threshold)
    
    if condition == ">": return current > threshold
    if condition == "<": return current < threshold
    if condition == ">=": return current >= threshold
    if condition == "<=": return current <= threshold
    if condition == "==": return current == threshold
    return False
