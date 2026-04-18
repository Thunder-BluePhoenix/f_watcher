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

    if not domain or domain in ("localhost", "127.0.0.1", "::1"):
        return

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expiry_str = cert.get("notAfter")
                expiry_date = datetime.datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")

                # BUG-12: datetime.utcnow() deprecated in Python 3.12+
                now_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                days_left = (expiry_date - now_utc).days

                # Always record SSL days remaining as a metric (not only when alerting)
                frappe.get_doc({
                    "doctype": "F Watcher App Metric",
                    "timestamp": now_datetime(),
                    "metric_type": "APM Trace",
                    "count": days_left,
                    "details": f"SSL certificate for {domain} expires in {days_left} days",
                }).insert(ignore_permissions=True)

                if days_left < 14:
                    frappe.get_doc({
                        "doctype": "F Watcher Alert Log",
                        "timestamp": now_datetime(),
                        "status": "Triggered",
                        "message": f"SSL Certificate for {domain} expires in {days_left} days!",
                        "metric_value": f"{days_left} days left",
                    }).insert(ignore_permissions=True)

                frappe.db.commit()
    except Exception:
        pass  # not HTTPS locally — safe to skip

def check_node_memory():
    total_node_mem_mb = 0
    node_instances = 0

    for proc in psutil.process_iter(["name", "memory_info"]):
        try:
            if "node" in proc.info["name"].lower():
                total_node_mem_mb += proc.info["memory_info"].rss / 1024 / 1024
                node_instances += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if node_instances > 0:
        # BUG-11: was writing to F Watcher System Metric with only ram_used_mb filled,
        # leaving cpu_percent/disk_percent/loads as NULL and distorting dashboard averages.
        # Node.js memory belongs in F Watcher App Metric.
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "APM Trace",
            "count": int(total_node_mem_mb),
            "details": f"Node.js total RSS: {total_node_mem_mb:.1f} MB across {node_instances} process(es)",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
