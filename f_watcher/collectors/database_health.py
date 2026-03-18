import frappe
from frappe.utils import now_datetime

def collect():
    try:
        check_fragmentation()
        check_deadlocks()
    except Exception as e:
        frappe.log_error("F-Watcher DB Health Collector", str(e))

def check_fragmentation():
    tables = frappe.db.sql("SHOW TABLE STATUS", as_dict=True)
    fragmented_storage = 0
    for tbl in tables:
        data_free = tbl.get('Data_free')
        if data_free:
            fragmented_storage += int(data_free)
    
    if fragmented_storage > 100 * 1024 * 1024:  # > 100MB
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": f"High Table Fragmentation detected: {fragmented_storage / 1024 / 1024:.2f} MB of Data_free space. Run OPTIMIZE TABLE.",
            "metric_value": f"{fragmented_storage} bytes"
        }).insert(ignore_permissions=True)
        frappe.db.commit()

def check_deadlocks():
    status = frappe.db.sql("SHOW ENGINE INNODB STATUS", as_dict=True)
    if status and len(status) > 0:
        innodb_status = status[0].get('Status')
        if innodb_status and 'LATEST DETECTED DEADLOCK' in innodb_status:
            deadlock_info = innodb_status.split('LATEST DETECTED DEADLOCK')[1].split('WE ROLL BACK TRANSACTION')[0]
            
            # Use App Metric to track deadlocks historically
            frappe.get_doc({
                "doctype": "F Watcher App Metric",
                "timestamp": now_datetime(),
                "metric_type": "Deadlock",
                "count": 1,
                "details": f"Deadlock Detected: {deadlock_info[:140]}..."
            }).insert(ignore_permissions=True)
            frappe.db.commit()
