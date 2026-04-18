from __future__ import annotations
import frappe
from frappe.utils import add_to_date, now_datetime


@frappe.whitelist()
def history(hours: int = 6, site: str = None):
    hours = min(int(hours), 168)
    since = frappe.utils.add_to_date(None, hours=-hours)
    site_clause = "AND site = %(site)s" if site else ""
    params = {"since": since, "site": site}

    system = frappe.db.sql(f"""
        SELECT
            DATE_FORMAT(`timestamp`, '%%Y-%%m-%%d %%H:%%i:00') AS bucket,
            AVG(cpu_percent)  AS cpu,
            AVG(ram_percent)  AS ram,
            AVG(disk_percent) AS disk
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %(since)s {site_clause}
        GROUP BY bucket
        ORDER BY bucket ASC
        LIMIT 500
    """, params, as_dict=True)

    queues = frappe.db.sql(f"""
        SELECT
            DATE_FORMAT(`timestamp`, '%%Y-%%m-%%d %%H:%%i:00') AS bucket,
            queue_name,
            AVG(job_count)    AS job_count,
            SUM(failed_count) AS failed_count
        FROM `tabF Watcher Queue Metric`
        WHERE `timestamp` >= %(since)s {site_clause}
        GROUP BY bucket, queue_name
        ORDER BY bucket ASC
        LIMIT 1000
    """, params, as_dict=True)

    db_size = frappe.db.sql(f"""
        SELECT
            DATE_FORMAT(`timestamp`, '%%Y-%%m-%%d %%H:00:00') AS bucket,
            AVG(total_mb) AS total_mb
        FROM `tabF Watcher DB Storage Snapshot`
        WHERE `timestamp` >= %(since)s {site_clause}
        GROUP BY bucket
        ORDER BY bucket ASC
        LIMIT 500
    """, params, as_dict=True)

    return {"system": system, "queues": queues, "db_size": db_size}


@frappe.whitelist()
def collector_status():
    collectors = [
        ("System",      "F Watcher System Metric",       5),
        ("Queue",       "F Watcher Queue Metric",         5),
        ("DB Storage",  "F Watcher DB Storage Snapshot", 10),
        ("DB Queries",  "F Watcher DB Metric",           10),
        ("Redis",       "F Watcher Redis Metric",        10),
        ("App Health",  "F Watcher App Metric",          10),
    ]
    result = []
    now = frappe.utils.now_datetime()
    for label, doctype, max_minutes in collectors:
        last = frappe.db.get_value(doctype, {}, "creation", order_by="creation desc")
        if not last:
            status = "never"
            minutes_ago = None
        else:
            diff = (now - frappe.utils.get_datetime(last)).total_seconds() / 60
            minutes_ago = int(diff)
            status = "ok" if diff <= max_minutes else "stale"
        result.append({"label": label, "status": status, "last": str(last or ""), "minutes_ago": minutes_ago})
    return result


@frappe.whitelist()
def latest(site: str = None):
    filters = {"site": site} if site else {}

    system = frappe.db.get_all(
        "F Watcher System Metric",
        filters=filters,
        fields=["timestamp","hostname","cpu_percent","ram_percent","disk_percent","load_1","load_5","load_15"],
        order_by="timestamp desc",
        limit=1,
    )
    db_snap = frappe.db.get_all(
        "F Watcher DB Storage Snapshot",
        filters=filters,
        fields=["timestamp","db_name","total_mb","data_mb","index_mb","tables_count","hostname"],
        order_by="timestamp desc",
        limit=1,
    )
    queues = frappe.db.get_all(
        "F Watcher Queue Metric",
        filters=filters,
        fields=["timestamp","queue_name","job_count","failed_count","active_workers"],
        order_by="timestamp desc",
        limit=10,
    )
    site_clause = "AND t.site = %(site)s" if site else ""
    big_tables = frappe.db.sql(f"""
        SELECT t.table_name, t.total_mb, t.rows_est,
               t.importance, t.importance_note,
               t.cleanup_allowed, t.cleanup_hint, t.`timestamp`
        FROM `tabF Watcher DB Table Storage` t
        INNER JOIN (
            SELECT table_name, MAX(`timestamp`) AS latest_ts
            FROM `tabF Watcher DB Table Storage`
            GROUP BY table_name
        ) latest ON t.table_name = latest.table_name
               AND t.`timestamp` = latest.latest_ts
        WHERE 1=1 {site_clause}
        ORDER BY t.total_mb DESC
        LIMIT 10
    """, {"site": site}, as_dict=True)

    return {
        "system": system[0] if system else None,
        "db_snapshot": db_snap[0] if db_snap else None,
        "queues": queues,
        "big_tables": big_tables,
    }


@frappe.whitelist()
def audit(limit: int = 20):
    return frappe.db.get_all(
        "F Watcher Action Audit",
        fields=["creation", "user", "action", "target", "result", "reason"],
        order_by="creation desc",
        limit=int(limit),
    )


@frappe.whitelist()
def query_stats(hours: int = 24, min_executions: int = 1, limit: int = 50):
    since = frappe.utils.add_to_date(None, hours=-int(hours))
    return frappe.db.sql("""
        SELECT
            query_signature,
            SUM(executions)  AS total_executions,
            MAX(max_time_ms) AS worst_ms,
            AVG(avg_time_ms) AS avg_ms,
            MAX(`timestamp`) AS last_seen
        FROM `tabF Watcher DB Metric`
        WHERE `timestamp` >= %(since)s
        GROUP BY query_signature
        HAVING total_executions >= %(min_exec)s
        ORDER BY worst_ms DESC
        LIMIT %(limit)s
    """, {"since": since, "min_exec": int(min_executions), "limit": int(limit)}, as_dict=True)


@frappe.whitelist()
def recommend_thresholds():
    since = frappe.utils.add_to_date(None, days=-7)
    rows = frappe.db.sql("""
        SELECT cpu_percent, ram_percent, disk_percent
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %(since)s
        ORDER BY `timestamp` ASC
    """, {"since": since})

    if len(rows) < 200:
        return {
            "status": "insufficient_data",
            "message": f"Need at least 200 data points (roughly 3 days). Have {len(rows)} so far.",
        }

    def p95(values):
        s = sorted(v for v in values if v is not None)
        return round(s[int(len(s) * 0.95)], 1) if s else None

    return {
        "status": "ok",
        "recommendations": [
            {"metric": "cpu_percent",  "suggested_threshold": p95([r[0] for r in rows]),
             "note": "P95 of observed CPU over last 7 days"},
            {"metric": "ram_percent",  "suggested_threshold": p95([r[1] for r in rows]),
             "note": "P95 of observed RAM over last 7 days"},
            {"metric": "disk_percent", "suggested_threshold": p95([r[2] for r in rows]),
             "note": "P95 of observed Disk over last 7 days"},
        ],
    }


@frappe.whitelist()
def compare():
    sites = frappe.db.sql(
        "SELECT DISTINCT site FROM `tabF Watcher System Metric` ORDER BY site",
        pluck="site",
    )
    result = {}
    for s in sites:
        row = frappe.db.get_all(
            "F Watcher System Metric",
            filters={"site": s},
            fields=["cpu_percent", "ram_percent", "disk_percent", "timestamp"],
            order_by="timestamp desc",
            limit=1,
        )
        result[s] = row[0] if row else None
    return result


@frappe.whitelist()
def uptime_summary(hours: int = 24, site: str = None):
    since = add_to_date(None, hours=-int(hours))
    filters = {"timestamp": [">=", since]}
    if site:
        filters["site"] = site
    rows = frappe.db.get_all(
        "F Watcher Uptime Record",
        filters=filters,
        fields=["status"],
    )
    total = len(rows)
    if not total:
        return {"uptime_pct": None, "total_checks": 0, "status": "no_data"}
    up_count = sum(1 for r in rows if r.status == "up")
    return {
        "uptime_pct": round(up_count / total * 100, 2),
        "total_checks": total,
        "status": "ok",
    }


@frappe.whitelist()
def compare_periods(hours: int = 24, site: str = None):
    hours = int(hours)
    now_dt = now_datetime()
    current_start = add_to_date(now_dt, hours=-hours)
    prior_start = add_to_date(now_dt, hours=-(hours * 2))
    site_clause = "AND site = %(site)s" if site else ""

    def period_avg(start, end):
        row = frappe.db.sql(f"""
            SELECT AVG(cpu_percent) AS cpu,
                   AVG(ram_percent) AS ram,
                   AVG(disk_percent) AS disk
            FROM `tabF Watcher System Metric`
            WHERE `timestamp` BETWEEN %(start)s AND %(end)s {site_clause}
        """, {"start": start, "end": end, "site": site}, as_dict=True)
        return row[0] if row else {}

    current = period_avg(current_start, now_dt)
    prior = period_avg(prior_start, current_start)

    def delta(cur, prv):
        if cur is None or prv is None:
            return None
        return round(float(cur) - float(prv), 1)

    return {
        "current": current,
        "prior": prior,
        "delta": {
            "cpu":  delta(current.get("cpu"),  prior.get("cpu")),
            "ram":  delta(current.get("ram"),  prior.get("ram")),
            "disk": delta(current.get("disk"), prior.get("disk")),
        },
    }


@frappe.whitelist()
def error_patterns(hours: int = 24, limit: int = 20):
    since = add_to_date(None, hours=-int(hours))
    return frappe.db.sql("""
        SELECT
            SUBSTRING(error, 1, 120) AS snippet,
            COUNT(*)                 AS count,
            MAX(creation)            AS last_seen,
            method
        FROM `tabError Log`
        WHERE creation >= %(since)s
        GROUP BY SUBSTRING(error, 1, 120), method
        ORDER BY count DESC
        LIMIT %(limit)s
    """, {"since": since, "limit": int(limit)}, as_dict=True)


@frappe.whitelist()
def disk_forecast(days: int = 7):
    since = add_to_date(None, days=-int(days))
    rows = frappe.db.sql("""
        SELECT UNIX_TIMESTAMP(`timestamp`) AS ts, total_mb
        FROM `tabF Watcher DB Storage Snapshot`
        WHERE `timestamp` >= %(since)s
        ORDER BY `timestamp` ASC
    """, {"since": since})

    if len(rows) < 5:
        return {"status": "insufficient_data", "days_until_full": None, "current_mb": None}

    xs = [float(r[0]) for r in rows]
    ys = [float(r[1]) for r in rows]
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    slope_num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    slope_den = sum((x - x_mean) ** 2 for x in xs)

    if slope_den == 0 or slope_num <= 0:
        return {"status": "no_growth", "days_until_full": None, "current_mb": round(ys[-1], 0)}

    slope_per_day = (slope_num / slope_den) * 86400
    current_mb = ys[-1]

    sys_row = frappe.db.get_all(
        "F Watcher System Metric",
        fields=["disk_percent"],
        order_by="timestamp desc",
        limit=1,
    )
    days_until_full = None
    if sys_row and sys_row[0].disk_percent:
        disk_pct = float(sys_row[0].disk_percent)
        if disk_pct > 0 and slope_per_day > 0:
            total_disk_mb = current_mb / (disk_pct / 100)
            free_mb = total_disk_mb - current_mb
            raw = free_mb / slope_per_day
            if 0 < raw < 9999:
                days_until_full = int(raw)

    return {
        "status": "ok",
        "current_mb": round(current_mb, 0),
        "growth_mb_per_day": round(slope_per_day, 1),
        "days_until_full": days_until_full,
    }
