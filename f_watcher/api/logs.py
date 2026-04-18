import os
import frappe
from frappe.utils import get_bench_path

ALLOWED_LOGS = [
    "frappe.log",
    "web.error.log",
    "worker.error.log",
    "schedule.error.log",
    "node-socketio.error.log",
]

@frappe.whitelist()
def tail_log(filename="frappe.log", lines=100):
    if not frappe.has_permission("F Watcher System Metric", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)

    if filename not in ALLOWED_LOGS:
        frappe.throw(f"Invalid log file. Allowed: {', '.join(ALLOWED_LOGS)}")

    # 3.6: rate limit — max 1 call per 3 seconds per user
    cache_key = f"fw_tail_ratelimit_{frappe.session.user}"
    if frappe.cache().get(cache_key):
        frappe.throw("Too many requests. Wait a moment.", frappe.RateLimitExceededError)
    frappe.cache().set(cache_key, 1, ex=3)

    log_path = os.path.join(get_bench_path(), "logs", filename)
    if not os.path.exists(log_path):
        return f"File not found: {log_path}"

    try:
        import subprocess
        safe_lines = min(int(lines), 500)
        result = subprocess.run(
            ["tail", "-n", str(safe_lines), log_path],
            capture_output=True,
            text=True,
        )
        return result.stdout
    except Exception as e:
        return f"Error reading log: {e}"
