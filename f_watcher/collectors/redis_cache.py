import frappe
from frappe.utils import now_datetime

def collect():
    try:
        info = frappe.cache().info()
        keyspace_hits = info.get("keyspace_hits", 0)
        keyspace_misses = info.get("keyspace_misses", 0)
        
        total_lookups = keyspace_hits + keyspace_misses
        hit_ratio = (keyspace_hits / total_lookups * 100) if total_lookups > 0 else 0.0

        frappe.get_doc({
            "doctype": "F Watcher Redis Metric",
            "timestamp": now_datetime(),
            "redis_type": "Cache",
            "used_memory_human": info.get("used_memory_human", "0B"),
            "hit_ratio": hit_ratio,
            "keyspace_hits": keyspace_hits,
            "keyspace_misses": keyspace_misses
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error("F-Watcher Redis Collector Failed", str(e))
