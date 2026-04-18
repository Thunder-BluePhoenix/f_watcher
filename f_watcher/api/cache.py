import frappe
from frappe.utils import now_datetime


def _check_permission():
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
    ):
        frappe.throw("Not permitted.", frappe.PermissionError)


def _audit(action, target, reason, result, details):
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
    frappe.db.commit()


@frappe.whitelist()
def stats():
    _check_permission()
    conn = frappe.cache()
    info = conn.info()

    patterns = {}
    cursor = 0
    sampled = 0
    while sampled < 500:
        cursor, keys = conn.scan(cursor, count=100)
        for k in keys:
            k_str = k.decode() if isinstance(k, bytes) else k
            prefix = k_str.split("|")[0] if "|" in k_str else k_str.split(":")[0]
            patterns[prefix] = patterns.get(prefix, 0) + 1
            sampled += 1
        if cursor == 0:
            break

    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses
    hit_ratio = round(hits / total * 100, 1) if total else None

    return {
        "used_memory_human": info.get("used_memory_human"),
        "maxmemory_human": info.get("maxmemory_human") or "no limit",
        "hit_ratio": hit_ratio,
        "key_patterns": sorted(patterns.items(), key=lambda x: -x[1])[:20],
        "total_keys": (info.get("db0") or {}).get("keys", 0),
    }


@frappe.whitelist()
def flush_cache():
    _check_permission()
    frappe.cache().flushdb()
    _audit("flush_cache", "redis", "Manual cache flush via Control Center", "Success", "Full Redis cache flushed.")
    return {"status": "ok"}
