# Phase 4 — Operational Control & Automation

> Goal: Turn F Watcher from a passive observer into an active operator.
> Give admins direct control over queues, cache, processes, and maintenance windows
> without needing terminal access.

---

## 4.1 Maintenance Window Support

**Problem:** During deployments, migrations, or planned downtime, collectors keep running
and generate false alerts (backup stale, scheduler down, high error count). There is no
way to say "ignore alerts for the next 30 minutes".

**What to do:**

Create a `F Watcher Maintenance Window` DocType:
```
Fields: title, starts_at (Datetime), ends_at (Datetime), reason, created_by
```

Update `alerting.py` to check for an active window before sending any alert:
```python
def is_maintenance_active():
    now = now_datetime()
    return frappe.db.exists("F Watcher Maintenance Window", {
        "starts_at": ["<=", now],
        "ends_at":   [">=", now],
    })

# In evaluate_and_alert():
if is_maintenance_active():
    return  # silently skip all alerts during maintenance
```

Add a "Start maintenance window" button to the Control Center with a duration picker
(15 min / 30 min / 1 hour / custom). Show a banner on the Control Center while a window
is active.

---

## 4.2 Auto-Remediation Rules

**Problem:** When a known recoverable condition is detected (e.g. failed queue jobs > 10,
Redis memory > 90%), the operator has to manually open the Control Center and take action.
For well-understood conditions, this can be automated.

**What to do:**

Add an `auto_remediate` checkbox and `remediation_action` Select field to `F Watcher Alert Rule`:

```
remediation_action options:
  - retry_failed_jobs_default
  - retry_failed_jobs_short
  - retry_failed_jobs_long
  - clear_cache
  - (extensible)
```

In the alerting engine, after triggering an alert:
```python
if rule.auto_remediate and rule.remediation_action:
    _run_remediation(rule.remediation_action, rule)
```

```python
def _run_remediation(action: str, rule):
    try:
        if action.startswith("retry_failed_jobs_"):
            queue = action.replace("retry_failed_jobs_", "")
            from f_watcher.actions.queue import retry_failed_jobs
            retry_failed_jobs(queue_name=queue)
        elif action == "clear_cache":
            frappe.cache().flushdb()
        _audit_remediation(rule, action, "Success")
    except Exception as e:
        _audit_remediation(rule, action, f"Failed: {e}")
```

Every auto-remediation is recorded in `F Watcher Action Audit`.

---

## 4.3 Queue Job Inspector

**Problem:** The Control Center shows queue *counts* but not what's actually in the queue.
When a job is stuck, the operator has to use the terminal to inspect it.

**What to do:**

Create a `queue_jobs()` API endpoint:
```python
@frappe.whitelist()
def queue_jobs(queue_name="default", status="queued", limit=50):
    from rq import Queue
    from frappe.utils.background_jobs import get_redis_conn
    conn = get_redis_conn()
    q = Queue(queue_name, connection=conn)

    if status == "failed":
        registry = q.failed_job_registry
        job_ids = registry.get_job_ids()[:int(limit)]
    else:
        job_ids = q.job_ids[:int(limit)]

    jobs = []
    for jid in job_ids:
        try:
            job = q.fetch_job(jid)
            if job:
                jobs.append({
                    "id": job.id,
                    "func": job.func_name,
                    "enqueued_at": str(job.enqueued_at),
                    "status": job.get_status(),
                    "description": job.description or "",
                })
        except Exception:
            pass
    return jobs
```

Add a "View jobs" expandable section per queue in the Control Center showing the first 20
jobs with columns: job ID, function name, enqueued at. Include a "Cancel" button per job
and a "Retry all" button per queue.

---

## 4.4 Redis Cache Manager

**Problem:** When Redis memory is high, the operator has no way to understand what's
taking space or selectively clear cache without terminal access.

**What to do:**

Create `api/cache.py`:
```python
@frappe.whitelist()
def stats():
    """Return Redis key pattern breakdown."""
    _check_permission()
    conn = frappe.cache()
    info = conn.info()
    # Sample top key patterns (scan a subset)
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

    return {
        "used_memory_human": info.get("used_memory_human"),
        "maxmemory_human": info.get("maxmemory_human", "no limit"),
        "hit_ratio": _hit_ratio(info),
        "key_patterns": sorted(patterns.items(), key=lambda x: -x[1])[:20],
        "total_keys": info.get("db0", {}).get("keys", 0),
    }

@frappe.whitelist()
def flush_cache():
    _check_permission()
    frappe.cache().flushdb()
    _audit("flush_cache", "redis", "Manual cache flush", "Success", "Full Redis cache flushed.")
    return {"status": "ok"}
```

Add a "Cache" card to the Control Center right column showing memory, hit ratio, top key
patterns, and a "Flush cache" button (with confirmation).

---

## 4.5 Custom Cleanup Rules

**Problem:** `CLEANUP_RULES` in `actions/cleanup.py` is hardcoded to 5 table types.
Admins with custom apps that have their own log/history tables can't add them.

**What to do:**

Create a `F Watcher Cleanup Rule` DocType:
```
Fields: table_name (Data), label (Data), default_days (Int), where_clause (Small Text),
        is_active (Check), notes (Small Text)
```

Update `cleanup.py` to merge built-in rules with DocType records:
```python
def _get_all_rules():
    rules = dict(CLEANUP_RULES)  # built-in defaults
    custom = frappe.get_all("F Watcher Cleanup Rule",
                            filters={"is_active": 1},
                            fields=["table_name", "label", "default_days", "where_clause"])
    for r in custom:
        rules[r.table_name] = {
            "label": r.label,
            "default_days": r.default_days,
            "where": r.where_clause,
        }
    return rules
```

Show all active cleanup rules (built-in + custom) in the Control Center's table section.

---

## Checklist

- [ ] 4.1 — Create `F Watcher Maintenance Window` DocType
- [ ] 4.1 — Add `is_maintenance_active()` check to alerting engine
- [ ] 4.1 — Add "Start maintenance" button + active banner to Control Center
- [ ] 4.2 — Add `auto_remediate` + `remediation_action` fields to Alert Rule
- [ ] 4.2 — Implement `_run_remediation()` in alerting engine
- [ ] 4.3 — Create `queue_jobs()` API endpoint
- [ ] 4.3 — Add queue job inspector panel to Control Center
- [ ] 4.3 — Add per-job cancel + per-queue retry-all buttons
- [ ] 4.4 — Create `api/cache.py` with `stats()` and `flush_cache()`
- [ ] 4.4 — Add Cache card to Control Center right column
- [ ] 4.5 — Create `F Watcher Cleanup Rule` DocType
- [ ] 4.5 — Merge custom rules into `cleanup.py` `_get_all_rules()`
