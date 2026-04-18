import os
import frappe
from frappe.utils import get_bench_path

ALLOWED = [
    "frappe.log",
    "web.error.log",
    "worker.error.log",
    "schedule.error.log",
    "node-socketio.error.log",
]


@frappe.whitelist()
def start_stream(filename: str):
    if not frappe.has_permission("F Watcher System Metric", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    if filename not in ALLOWED:
        frappe.throw("Invalid log file")

    frappe.enqueue(
        "f_watcher.api.log_stream._tail_and_emit",
        filename=filename,
        user=frappe.session.user,
        queue="short",
        timeout=300,
    )
    return {"status": "streaming"}


def _tail_and_emit(filename: str, user: str):
    import subprocess
    import time

    log_path = os.path.join(get_bench_path(), "logs", filename)
    if not os.path.exists(log_path):
        frappe.publish_realtime(
            event="fw_log_line",
            message={"line": f"[F Watcher] Log file not found: {log_path}"},
            user=user,
        )
        return

    proc = subprocess.Popen(
        ["tail", "-n", "50", "-f", log_path],
        stdout=subprocess.PIPE,
        text=True,
    )
    start = time.time()
    try:
        for line in proc.stdout:
            frappe.publish_realtime(
                event="fw_log_line",
                message={"line": line.rstrip()},
                user=user,
            )
            if time.time() - start > 280:
                break
    finally:
        proc.terminate()
