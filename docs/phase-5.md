# Phase 5 — Reporting & Analytics

> Goal: Turn collected metric data into actionable insights.
> Exportable reports, trend comparisons, uptime tracking, and error pattern analysis
> so decisions are data-driven, not gut-feel.

---

## 5.1 Metric Export (CSV / JSON)

**Problem:** All collected data is locked inside Frappe DocTypes. There is no way to
pull it into Excel, Grafana, a BI tool, or share it with an external team.

**What to do:**

Create `api/export.py`:
```python
import frappe
import csv
import io

@frappe.whitelist()
def system_metrics_csv(hours: int = 24):
    _check_permission()
    since = frappe.utils.add_to_date(None, hours=-int(hours))
    rows = frappe.db.sql("""
        SELECT `timestamp`, hostname, cpu_percent, ram_percent,
               disk_percent, load_1, load_5, load_15
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %(since)s
        ORDER BY `timestamp` ASC
    """, {"since": since}, as_dict=True)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else [])
    writer.writeheader()
    writer.writerows([dict(r) for r in rows])
    frappe.response["content_type"] = "text/csv"
    frappe.response["headers"] = {
        "Content-Disposition": f'attachment; filename="system_metrics_{hours}h.csv"'
    }
    frappe.response["result"] = output.getvalue()
```

Add "Export CSV" buttons in the Control Center for:
- System metrics (last 24h / 7d / 30d)
- Queue metrics
- DB table storage snapshot

---

## 5.2 Uptime Tracker

**Problem:** There is no concept of "uptime" in F Watcher. You can't answer "was the
site up last Tuesday?" or "what % of the last 30 days was healthy?".

**What to do:**

Create a `F Watcher Uptime Record` DocType:
```
Fields: timestamp (Datetime), status (Select: up/degraded/down),
        cpu_percent, ram_percent, disk_percent, queue_failures, reason
```

Create `collectors/uptime.py` (runs every 5 minutes):
```python
def collect():
    sys = frappe.db.get_all("F Watcher System Metric",
                             fields=["cpu_percent","ram_percent","disk_percent"],
                             order_by="timestamp desc", limit=1)
    if not sys:
        return
    s = sys[0]
    q_fails = frappe.db.sql(
        "SELECT SUM(failed_count) FROM `tabF Watcher Queue Metric` "
        "WHERE `timestamp` >= %s", (frappe.utils.add_to_date(None, minutes=-5),)
    )[0][0] or 0

    if s.cpu_percent > 95 or s.ram_percent > 95 or s.disk_percent > 95 or q_fails > 50:
        status = "down"
    elif s.cpu_percent > 80 or s.ram_percent > 80 or q_fails > 10:
        status = "degraded"
    else:
        status = "up"

    frappe.get_doc({
        "doctype": "F Watcher Uptime Record",
        "timestamp": frappe.utils.now_datetime(),
        "status": status,
        "cpu_percent": s.cpu_percent,
        "ram_percent": s.ram_percent,
        "disk_percent": s.disk_percent,
        "queue_failures": int(q_fails),
    }).insert(ignore_permissions=True)
    frappe.db.commit()
```

Add an `uptime_summary()` API endpoint returning 30-day uptime %:
```python
@frappe.whitelist()
def uptime_summary(days: int = 30):
    since = frappe.utils.add_to_date(None, days=-int(days))
    total = frappe.db.count("F Watcher Uptime Record", {"timestamp": [">=", since]})
    up    = frappe.db.count("F Watcher Uptime Record",
                             {"timestamp": [">=", since], "status": "up"})
    degraded = frappe.db.count("F Watcher Uptime Record",
                                {"timestamp": [">=", since], "status": "degraded"})
    pct = round((up + degraded * 0.5) / total * 100, 2) if total else None
    return {"uptime_percent": pct, "up": up, "degraded": degraded,
            "down": total - up - degraded, "total_checks": total}
```

Show as a prominent "Uptime: 99.3%" badge in the Control Center header.

---

## 5.3 Period-over-Period Comparison

**Problem:** "CPU is at 65%" means nothing without context. Is that normal? Is it higher
than last week? F Watcher has the historical data but never compares periods.

**What to do:**

Add a `compare_periods()` endpoint to `dashboards/metrics.py`:
```python
@frappe.whitelist()
def compare_periods(metric: str = "cpu_percent", days: int = 7):
    """Compare average metric value: this period vs same period prior."""
    now = frappe.utils.now_datetime()
    this_start  = frappe.utils.add_to_date(now, days=-int(days))
    prior_start = frappe.utils.add_to_date(now, days=-int(days) * 2)
    prior_end   = this_start

    def avg(start, end):
        r = frappe.db.sql(f"""
            SELECT AVG(`{metric}`) FROM `tabF Watcher System Metric`
            WHERE `timestamp` BETWEEN %(s)s AND %(e)s
        """, {"s": start, "e": end})
        return round(float(r[0][0] or 0), 2)

    this  = avg(this_start, now)
    prior = avg(prior_start, prior_end)
    delta = round(this - prior, 2)
    pct_change = round(delta / prior * 100, 1) if prior else None
    return {"metric": metric, "this_period": this, "prior_period": prior,
            "delta": delta, "pct_change": pct_change, "days": days}
```

Display as delta arrows (↑ +3.2% vs last week) next to each KPI in the Control Center.

---

## 5.4 Top Error Patterns Report

**Problem:** The app health collector groups errors by method but there is no aggregated
view showing which errors are most frequent over time, growing, or newly appearing.

**What to do:**

Add an `error_patterns()` API endpoint:
```python
@frappe.whitelist()
def error_patterns(days: int = 7):
    since = frappe.utils.add_to_date(None, days=-int(days))
    return frappe.db.sql("""
        SELECT
            method,
            COUNT(name)       AS total,
            MAX(creation)     AS last_seen,
            MIN(creation)     AS first_seen
        FROM `tabError Log`
        WHERE creation >= %(since)s
          AND method IS NOT NULL
        GROUP BY method
        ORDER BY total DESC
        LIMIT 20
    """, {"since": since}, as_dict=True)
```

Render as a table on the Control Center (or a new "Error Patterns" section) showing:
method name | occurrence count | first seen | last seen | trend (↑ ↓ →).

---

## 5.5 Scheduled PDF / Email Report

**Problem:** The daily digest email (Phase 2.5) sends plain-text HTML. There is no
structured weekly report with charts, trends, and a full health summary that a manager
or stakeholder could read.

**What to do:**

Create `collectors/weekly_report.py`:
- Runs every Monday at 08:00
- Queries 7-day averages for CPU, RAM, Disk, queue failures, alert count, uptime %
- Renders a structured HTML email with a summary table, period-over-period deltas,
  top 5 error methods, and top 3 biggest tables
- Sends to all users with `F Watcher Operator` or `F Watcher Viewer` role

```python
def send_weekly_report():
    from f_watcher.dashboards.metrics import compare_periods, error_patterns, uptime_summary
    uptime = uptime_summary(days=7)
    cpu_cmp = compare_periods("cpu_percent", days=7)
    ram_cmp = compare_periods("ram_percent", days=7)
    errors  = error_patterns(days=7)
    # ... build HTML table and send via frappe.sendmail
```

Register in `hooks.py`:
```python
"0 8 * * 1": ["f_watcher.collectors.weekly_report.send_weekly_report"],
```

---

## 5.6 Disk Growth Rate Forecast

**Problem:** The DB storage section shows current size but not trajectory. "We have 200GB
free" is less useful than "at current growth rate we have 23 days before disk is full".

**What to do:**

Add a `disk_forecast()` endpoint:
```python
@frappe.whitelist()
def disk_forecast():
    rows = frappe.db.sql("""
        SELECT `timestamp`, disk_percent
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %s
        ORDER BY `timestamp` ASC
    """, (frappe.utils.add_to_date(None, days=-30),), as_dict=True)

    if len(rows) < 2:
        return {"status": "insufficient_data"}

    # Simple linear regression on disk_percent over time
    import statistics
    n = len(rows)
    x = list(range(n))
    y = [float(r.disk_percent) for r in rows]
    x_mean, y_mean = statistics.mean(x), statistics.mean(y)
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / \
            sum((xi - x_mean) ** 2 for xi in x)

    # slope is % per data point. Convert to % per day
    # data points are ~1/min so n points ≈ n minutes
    slope_per_day = slope * 60 * 24
    current = y[-1]
    days_to_full = (100 - current) / slope_per_day if slope_per_day > 0 else None

    return {
        "current_disk_percent": current,
        "growth_per_day_pct": round(slope_per_day, 3),
        "days_to_full": round(days_to_full) if days_to_full else None,
    }
```

Show in the Control Center disk KPI card as: "At this rate: full in ~42 days".

---

## Checklist

- [ ] 5.1 — Create `api/export.py` with `system_metrics_csv()`
- [ ] 5.1 — Add Export CSV buttons to Control Center (system, queue, DB tables)
- [ ] 5.2 — Create `F Watcher Uptime Record` DocType
- [ ] 5.2 — Create `collectors/uptime.py` (every 5 min)
- [ ] 5.2 — Add `uptime_summary()` API + uptime % badge in Control Center header
- [ ] 5.3 — Add `compare_periods()` to `dashboards/metrics.py`
- [ ] 5.3 — Show delta arrows (↑/↓) next to KPI values in Control Center
- [ ] 5.4 — Add `error_patterns()` API + Error Patterns table in Control Center
- [ ] 5.5 — Create `collectors/weekly_report.py`
- [ ] 5.5 — Register weekly report at 08:00 Monday in `hooks.py`
- [ ] 5.6 — Add `disk_forecast()` API + "full in ~N days" note in disk KPI card
