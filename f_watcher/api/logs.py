import os
import frappe
from frappe.utils import get_bench_path

@frappe.whitelist()
def tail_log(filename="frappe.log", lines=100):
    if not frappe.has_permission("F Watcher System Metric", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
        
    allowed_logs = ["frappe.log", "web.error.log", "worker.error.log", "schedule.error.log", "node-socketio.error.log"]
    if filename not in allowed_logs:
        frappe.throw(f"Invalid log file requested. Allowed: {', '.join(allowed_logs)}")
        
    log_path = os.path.join(get_bench_path(), "logs", filename)
    if not os.path.exists(log_path):
        return f"File not found: {log_path}"
        
    try:
        import subprocess
        safe_lines = min(int(lines), 500)  # hard cap — prevents unbounded reads
        result = subprocess.run(["tail", "-n", str(safe_lines), log_path], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error reading log: {e}"
