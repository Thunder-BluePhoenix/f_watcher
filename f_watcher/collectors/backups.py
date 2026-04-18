import os
import gzip
import glob
import frappe
from frappe.utils import now_datetime, time_diff_in_hours


def _is_valid_gzip(path: str) -> bool:
    try:
        with gzip.open(path, "rb") as f:
            f.read(512)
        return True
    except Exception:
        return False

def collect():
    site_path = frappe.get_site_path()
    backup_path = os.path.join(site_path, "private", "backups")
    
    if not os.path.exists(backup_path):
        record_alert("Critical: Backup directory does not exist at " + backup_path)
        return
        
    # Get all sql.gz files
    files = glob.glob(os.path.join(backup_path, "*.sql.gz"))
    if not files:
        record_alert("Critical: No backup files found in " + backup_path)
        return
        
    # Find newest file
    latest_file = max(files, key=os.path.getmtime)
    mtime = os.path.getmtime(latest_file)
    
    import datetime
    dt_mtime = datetime.datetime.fromtimestamp(mtime)
    
    diff_hours = time_diff_in_hours(now_datetime(), dt_mtime)
    
    if diff_hours > 24:
        record_alert(f"Critical: The most recent backup is {diff_hours:.1f} hours old. Backup process may be failing.")
        return

    if not _is_valid_gzip(latest_file):
        record_alert(f"Critical: Latest backup {os.path.basename(latest_file)} is corrupt or unreadable.")
        return

    if True:  # healthy branch
        # BUG-15: healthy state was never recorded — dashboard had no backup history at all
        import os as _os
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "APM Trace",
            "count": 1,
            "details": f"Backup OK — latest: {_os.path.basename(latest_file)}, {diff_hours:.1f}h old",
        }).insert(ignore_permissions=True)
        frappe.db.commit()

def record_alert(message):
    try:
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": message,
            "metric_value": "Backup Check Failed"
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error("F-Watcher Backup Auditor Failed", str(e))
