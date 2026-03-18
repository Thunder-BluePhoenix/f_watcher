from __future__ import annotations
import subprocess
import frappe
from frappe.utils import now_datetime

# Choose ONE based on your setup:
SYSTEMD = True  # set False if using supervisor

ALLOWED = {
    "restart_workers": ["sudo", "/usr/local/bin/f_watcher-restart", "workers"],
    "restart_scheduler": ["sudo", "/usr/local/bin/f_watcher-restart", "scheduler"],
}

if not SYSTEMD:
    ALLOWED = {
        "restart_workers": ["sudo", "/usr/local/bin/f_watcher-supervisor-restart", "workers"],
        "restart_scheduler": ["sudo", "/usr/local/bin/f_watcher-supervisor-restart", "scheduler"],
    }

@frappe.whitelist()
def restart_workers(reason: str):
    frappe.only_for("F Watcher Operator")
    return _run("restart_workers", "workers", reason)

@frappe.whitelist()
def restart_scheduler(reason: str):
    frappe.only_for("F Watcher Operator")
    return _run("restart_scheduler", "scheduler", reason)

def _run(action: str, target: str, reason: str):
    try:
        subprocess.check_output(ALLOWED[action], stderr=subprocess.STDOUT)
        result = "Success"
        details = f"{target} restarted"
    except Exception as e:
        result = "Failed"
        details = str(e)

    _audit(action, target, reason, result, details)
    return result

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
