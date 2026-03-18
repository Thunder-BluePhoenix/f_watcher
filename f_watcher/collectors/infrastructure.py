import ssl
import socket
import datetime
import frappe
import psutil
from frappe.utils import now_datetime, get_url

def collect():
    try:
        check_ssl()
        check_node_memory()
    except Exception as e:
        frappe.log_error("F-Watcher Infrastructure Collector", str(e))

def check_ssl():
    site_url = get_url()
    domain = site_url.replace("https://", "").replace("http://", "").split(":")[0]
    
    if not domain or domain == 'localhost' or domain == '127.0.0.1':
        return
        
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry_str = cert.get('notAfter')
                expiry_date = datetime.datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry_date - datetime.datetime.utcnow()).days
                
                if days_left < 14:
                    frappe.get_doc({
                        "doctype": "F Watcher Alert Log",
                        "timestamp": now_datetime(),
                        "status": "Triggered",
                        "message": f"SSL Certificate for {domain} will expire in {days_left} days!",
                        "metric_value": f"{days_left} days left"
                    }).insert(ignore_permissions=True)
                    frappe.db.commit()
    except Exception:
        pass  # E.g., not configured with HTTPS locally

def check_node_memory():
    total_node_mem_mb = 0
    node_instances = 0
    
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            if 'node' in proc.info['name'].lower():
                total_node_mem_mb += proc.info['memory_info'].rss / 1024 / 1024
                node_instances += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    if node_instances > 0:
        frappe.get_doc({
            "doctype": "F Watcher System Metric",
            "timestamp": now_datetime(),
            "site": frappe.local.site,
            "hostname": socket.gethostname() + f" (Node.js x{node_instances})",
            "ram_used_mb": int(total_node_mem_mb),
        }).insert(ignore_permissions=True)
        frappe.db.commit()
