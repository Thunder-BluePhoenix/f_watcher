# Phase 3 — Intelligence & Advanced Monitoring

> Goal: Add anomaly detection, DB query explorer, backup validation, multi-site support,
> threshold recommendations, and API rate limiting.
> This phase makes F Watcher proactive and self-improving rather than just reactive.

---

## 3.1 Anomaly Detection (Baseline Deviation Alerts)

**Problem:** Alert rules require the user to manually set thresholds like "CPU > 80%".
New sites have no historical baseline to reference. The first week of usage produces zero alerts.
Meanwhile, a subtle memory leak (RAM drifting from 30% to 65% over 48h) goes unnoticed.

**What to do:**

Create `f_watcher/collectors/anomaly.py`:

```python
from __future__ import annotations
import frappe
from frappe.utils import add_to_date

CHECKS = [
    {
        "label": "CPU spike",
        "doctype": "F Watcher System Metric",
        "field": "cpu_percent",
        "window_hours": 24,
        "sigma_threshold": 2.5,
    },
    {
        "label": "RAM spike",
        "doctype": "F Watcher System Metric",
        "field": "ram_percent",
        "window_hours": 48,
        "sigma_threshold": 2.0,
    },
    {
        "label": "Queue depth spike",
        "doctype": "F Watcher Queue Metric",
        "field": "job_count",
        "window_hours": 24,
        "sigma_threshold": 3.0,
    },
]

def collect():
    for check in CHECKS:
        _evaluate(check)

def _evaluate(check: dict):
    since = add_to_date(None, hours=-(check["window_hours"]))

    stats = frappe.db.sql(f"""
        SELECT AVG(`{check['field']}`) AS mean,
               STDDEV(`{check['field']}`) AS stddev,
               MAX(`{check['field']}`) AS latest_max
        FROM `tab{check['doctype']}`
        WHERE timestamp >= %(since)s
    """, {"since": since}, as_dict=True)

    if not stats or stats[0].stddev is None or float(stats[0].stddev) == 0:
        return

    row = stats[0]
    mean, stddev, latest_max = float(row.mean), float(row.stddev), float(row.latest_max)
    z_score = (latest_max - mean) / stddev

    if z_score >= check["sigma_threshold"]:
        _log_anomaly(check, mean, stddev, latest_max, z_score)

def _log_anomaly(check, mean, stddev, latest_max, z_score):
    msg = (
        f"Anomaly detected: {check['label']} reached {latest_max:.1f} "
        f"(mean={mean:.1f}, σ={stddev:.1f}, z={z_score:.2f})"
    )
    frappe.get_doc({
        "doctype": "F Watcher Alert Log",
        "alert_rule": None,
        "timestamp": frappe.utils.now_datetime(),
        "status": "Triggered",
        "message": msg,
        "metric_value": latest_max,
    }).insert(ignore_permissions=True)
    frappe.db.commit()
```

Register in `hooks.py` — every 15 minutes:

```python
"*/15 * * * *": [
    # ... existing
    "f_watcher.collectors.anomaly.collect",
],
```

---

## 3.2 DB Query Explorer Page

**Problem:** The `F Watcher DB Metric` DocType stores slow query signatures but there is no
UI to search, filter, or group them. Operators have to go into the list view and manually browse.

**What to do:**

Create a new page `f_watcher/f_watcher/page/f-watcher-query-explorer/`:

```
f-watcher-query-explorer/
  f_watcher_query_explorer.json   (page definition)
  f_watcher_query_explorer.py     (Python controller — empty, data via API)
  f_watcher_query_explorer.js     (UI logic)
```

Add a `query_stats()` API endpoint in `dashboards/metrics.py`:

```python
@frappe.whitelist()
def query_stats(hours: int = 24, min_executions: int = 1, limit: int = 50):
    since = frappe.utils.add_to_date(None, hours=-int(hours))
    return frappe.db.sql("""
        SELECT
            query_signature,
            SUM(executions)   AS total_executions,
            MAX(max_time_ms)  AS worst_ms,
            AVG(avg_time_ms)  AS avg_ms,
            MAX(timestamp)    AS last_seen
        FROM `tabF Watcher DB Metric`
        WHERE timestamp >= %(since)s
        GROUP BY query_signature
        HAVING total_executions >= %(min_exec)s
        ORDER BY worst_ms DESC
        LIMIT %(limit)s
    """, {"since": since, "min_exec": int(min_executions), "limit": int(limit)},
    as_dict=True)
```

**Page features:**
- Filter bar: time range (1h/6h/24h/7d), min executions, sort by (worst/avg/count)
- Table with columns: query hash, total executions, worst ms, avg ms, last seen
- Click a row to expand full query details stored in the record

---

## 3.3 Backup File Integrity Validation

**Problem:** `collectors/backups.py` checks that a `.sql.gz` file exists and is recent
(`< 24h`). It does not verify the file is a valid gzip archive. A truncated or corrupt
backup would pass the check and no alert would fire.

**What to do:**

Update `collectors/backups.py` — add a gzip header check after the existence check:

```python
import gzip, os

def _is_valid_gzip(path: str) -> bool:
    try:
        with gzip.open(path, "rb") as f:
            f.read(512)  # read first 512 bytes to verify header
        return True
    except Exception:
        return False
```

Call it after the age check:

```python
if not _is_valid_gzip(latest_backup):
    _alert(f"Latest backup {os.path.basename(latest_backup)} is corrupt or unreadable.")
    return
```

---

## 3.4 Threshold Recommendation Engine

**Problem:** New users don't know what alert thresholds to set. After a few days of data
collection, F Watcher has enough history to suggest sensible defaults.

**What to do:**

Add a `recommend_thresholds()` API endpoint:

```python
@frappe.whitelist()
def recommend_thresholds():
    """
    After >= 3 days of data, suggest alert thresholds as P95 of observed values.
    """
    since = frappe.utils.add_to_date(None, days=-7)

    rows = frappe.db.sql("""
        SELECT
            cpu_percent, ram_percent, disk_percent
        FROM `tabF Watcher System Metric`
        WHERE timestamp >= %(since)s
        ORDER BY timestamp ASC
    """, {"since": since})

    if len(rows) < 200:
        return {"status": "insufficient_data",
                "message": "Need at least 200 data points (roughly 3 days)."}

    def p95(values):
        s = sorted(v for v in values if v is not None)
        return s[int(len(s) * 0.95)] if s else None

    cpu_vals  = [r[0] for r in rows]
    ram_vals  = [r[1] for r in rows]
    disk_vals = [r[2] for r in rows]

    return {
        "status": "ok",
        "recommendations": [
            {"metric": "cpu_percent",  "suggested_threshold": p95(cpu_vals),
             "note": "P95 of observed CPU over last 7 days"},
            {"metric": "ram_percent",  "suggested_threshold": p95(ram_vals),
             "note": "P95 of observed RAM over last 7 days"},
            {"metric": "disk_percent", "suggested_threshold": p95(disk_vals),
             "note": "P95 of observed Disk over last 7 days"},
        ]
    }
```

Surface in the Alert Rule form as a "Get Recommendations" button via a client script.

---

## 3.5 Multi-Site Isolation & Comparison

**Problem:** All metric DocTypes capture `site` as a field, but the dashboard and queries
don't filter by site. In a multi-site bench, all sites' metrics are mixed in the same view.

**What to do:**

1. Add `site` filter to `dashboards/metrics.py` — `latest()` and `history()` should accept
   an optional `site` parameter and filter accordingly.

2. Add a site-selector dropdown to the Control Center page header.
   Default: `frappe.boot.sitename`.

3. Create a `compare()` endpoint that returns latest metrics for all known sites:

```python
@frappe.whitelist()
def compare():
    sites = frappe.db.sql(
        "SELECT DISTINCT site FROM `tabF Watcher System Metric` ORDER BY site",
        pluck="site"
    )
    result = {}
    for site in sites:
        row = frappe.db.get_all(
            "F Watcher System Metric",
            filters={"site": site},
            fields=["cpu_percent", "ram_percent", "disk_percent", "timestamp"],
            order_by="timestamp desc",
            limit=1,
        )
        result[site] = row[0] if row else None
    return result
```

---

## 3.6 API Rate Limiting on Log Viewer

**Problem:** `api/logs.py` `tail_log()` is whitelisted with no rate limit.
A user (or browser tab) can call it in a tight loop, putting constant I/O pressure on
the bench server by spawning repeated `tail` subprocesses.

**What to do:**

Add a simple last-call timestamp check using Redis:

```python
@frappe.whitelist()
def tail_log(filename="frappe.log", lines=100):
    # ... existing permission + allowlist check ...

    # Rate limit: max 1 call per 3 seconds per user
    cache_key = f"fw_tail_ratelimit_{frappe.session.user}"
    if frappe.cache().get(cache_key):
        frappe.throw("Too many requests. Wait a moment.", frappe.RateLimitExceededError)
    frappe.cache().set(cache_key, 1, expires_in_sec=3)

    # ... existing tail logic ...
```

Also cap `lines` at a safe maximum:

```python
lines = min(int(lines), 500)
```

---

## 3.7 Alert Rule: Webhook Validation

**Problem:** `actions/alerting.py` POSTs to whatever URL is stored in `webhook_url` with
no validation. A malformed or internal URL (e.g. `http://localhost:8000/...`) could be used
to trigger internal requests from the bench server.

**What to do:**

Add URL validation in the Alert Rule's `validate` hook (Python controller):

```python
import re
from urllib.parse import urlparse

def validate(self):
    if self.alert_channel == "Webhook" and self.webhook_url:
        parsed = urlparse(self.webhook_url)
        if parsed.scheme not in ("http", "https"):
            frappe.throw("Webhook URL must use http or https.")
        if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
            frappe.throw("Webhook URL cannot point to localhost.")
```

---

---

## 3.8 Alerting Intelligence

### 3.8a — Configurable Alert Cooldown per Rule

**Problem:** The 15-minute cooldown is hardcoded in `alerting.py`. Some rules (disk > 95%)
need immediate re-alerting; others (CPU > 70%) should wait an hour.

**What to do:** Add a `cooldown_minutes` Int field to the `F Watcher Alert Rule` DocType
with a default of 15. Use `rule.cooldown_minutes or 15` in the evaluator.

---

### 3.8b — Alert Auto-Resolve Detection

**Problem:** When a metric drops below threshold after an alert, nothing happens. There is
no "Resolved" entry — the alert stays in the log forever as "Triggered".

**What to do:**

Track which rules were last fired. On subsequent evaluations, if the condition is no longer
true and the last log entry for that rule was "Triggered", insert a "Resolved" record:

```python
if not evaluate_condition(value, rule.condition, rule.threshold_value):
    last_log = frappe.db.get_value(
        "F Watcher Alert Log",
        {"alert_rule": rule.name},
        ["status", "name"],
        order_by="timestamp desc",
        as_dict=True,
    )
    if last_log and last_log.status == "Triggered":
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "alert_rule": rule.name,
            "timestamp": now_datetime(),
            "status": "Resolved",
            "message": f"Alert resolved: {rule.property_name} is now {value}",
            "metric_value": str(value),
        }).insert(ignore_permissions=True)
```

**Files:** `f_watcher/collectors/alerting.py`

---

### 3.8c — Test Alert Button on Alert Rule Form

**Problem:** After creating an Alert Rule the user has no way to verify it works without
waiting for the next collector run.

**What to do:**

Add a `test_rule()` whitelisted function:

```python
@frappe.whitelist()
def test_rule(rule_name: str):
    rule = frappe.get_doc("F Watcher Alert Rule", rule_name)
    metric = get_latest_metric(rule.metric_type)
    if not metric:
        return {"status": "no_data", "message": "No metric data available yet."}
    value = metric.get(rule.property_name)
    would_fire = evaluate_condition(value, rule.condition, rule.threshold_value)
    return {
        "status": "would_fire" if would_fire else "ok",
        "current_value": value,
        "threshold": rule.threshold_value,
        "condition": rule.condition,
    }
```

Wire to a "Test now" button via a Client Script on the Alert Rule form.

---

## 3.9 Collector Improvements

### 3.9a — Queue Collector: Use Dynamic Queue Names

**Problem:** `collectors/queue.py` has the queue names `["short", "default", "long"]`
hardcoded. In Frappe bench the actual queue names are prefixed with the bench path
(e.g. `Users-bluephoenix-frappe-bench:default`). The collector may be reading wrong queues.

**What to do:**
```python
from frappe.utils.background_jobs import get_queue_names
queues = get_queue_names()  # returns the actual site-prefixed queue names
```

**Files:** `f_watcher/collectors/queue.py`

---

### 3.9b — DB Storage: Flag Index Bloat

**Problem:** `db_storage.py` already collects `data_mb` and `index_mb` per table but
never raises an alert when indexes are larger than the actual data — a known performance
smell indicating stale or duplicate indexes.

**What to do:** In `db_storage.py`, after inserting the table record, check if
`index_mb > data_mb * 1.5` and write to `F Watcher Alert Log`:

```python
if r.index_mb > (r.data_mb or 0) * 1.5 and r.total_mb > 50:
    frappe.get_doc({
        "doctype": "F Watcher Alert Log",
        "timestamp": ts,
        "status": "Triggered",
        "message": f"Index bloat: {r.table_name} indexes ({r.index_mb:.0f} MB) > data ({r.data_mb:.0f} MB). Consider ANALYZE TABLE.",
        "metric_value": f"{r.index_mb:.1f} MB indexes",
    }).insert(ignore_permissions=True)
```

**Files:** `f_watcher/collectors/db_storage.py`

---

## Checklist

**Original items**
- [ ] Create `collectors/anomaly.py` with Z-score detection
- [ ] Register anomaly collector in `hooks.py` (every 15 min)
- [ ] Create `f-watcher-query-explorer` page + `query_stats()` API
- [ ] Add gzip integrity check to `collectors/backups.py`
- [ ] Create `recommend_thresholds()` API + Alert Rule "Get Recommendations" button
- [ ] Add `site` filter param to `latest()` + `history()` in `dashboards/metrics.py`
- [ ] Add site-selector dropdown to Control Center
- [ ] Create `compare()` multi-site endpoint
- [ ] Add Redis-based rate limiting to `api/logs.py`
- [ ] Cap `lines` parameter at 500 in `api/logs.py`
- [ ] Add `validate()` webhook URL check to F Watcher Alert Rule controller

**Alerting intelligence**
- [ ] 3.8a — `cooldown_minutes` field on Alert Rule (configurable per rule)
- [ ] 3.8b — Auto-resolve detection in alerting engine
- [ ] 3.8c — `test_rule()` API + "Test now" button on Alert Rule form

**Collector improvements**
- [ ] 3.9a — Queue collector: use `get_queue_names()` instead of hardcoded strings
- [ ] 3.9b — DB storage: flag index bloat when `index_mb > data_mb * 1.5`
