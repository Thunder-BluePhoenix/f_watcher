# Phase 1 — Stability & Correctness

> Goal: Fix known bugs, define missing roles/permissions, add metric data retention, and write basic tests.
> Without this phase, the app has runtime errors, silently growing DB tables, and unusable admin actions.

---

## 1.1 Bug Fixes

### BUG-01 — `affected_rows` AttributeError — `actions/cleanup.py` ✅ Fixed 2026-04-13

**Root cause:** `frappe.db.affected_rows()` does not exist on `MariaDBDatabase`.

**Fix:** Run `SELECT COUNT(*)` before the `DELETE` using the same `WHERE` clause.

```python
# Before (broken)
frappe.db.sql("DELETE FROM `{table}` WHERE ...")
deleted = frappe.db.affected_rows()   # AttributeError

# After (fixed)
deleted = frappe.db.sql("SELECT COUNT(*) FROM `{table}` WHERE ...")[0][0]
frappe.db.sql("DELETE FROM `{table}` WHERE ...")
frappe.db.commit()
```

**Files changed:** `f_watcher/actions/cleanup.py`

---

### BUG-02 — Duplicate table rows in "Biggest tables" dashboard — `dashboards/metrics.py` ✅ Fixed 2026-04-13

**Root cause:** `big_tables` query used `ORDER BY total_mb DESC LIMIT 10` with no grouping.
Every collector run inserts one row per table, so the same table appeared multiple times
(one per snapshot) — all with identical sizes but different row counts.

**Fix:** Subquery to join only the latest snapshot per unique `table_name`.

```sql
SELECT t.* FROM `tabF Watcher DB Table Storage` t
INNER JOIN (
    SELECT table_name, MAX(`timestamp`) AS latest_ts
    FROM `tabF Watcher DB Table Storage`
    GROUP BY table_name
) latest ON t.table_name = latest.table_name
       AND t.`timestamp` = latest.latest_ts
ORDER BY t.total_mb DESC LIMIT 10
```

**Files changed:** `f_watcher/dashboards/metrics.py`

---

### BUG-03 — MariaDB reserved keyword `timestamp` unquoted in raw SQL — `dashboards/metrics.py` ✅ Fixed 2026-04-13

**Root cause:** `timestamp` is a reserved keyword in MariaDB. Using it unquoted in raw
`frappe.db.sql()` causes a syntax error, silently returning empty `big_tables` data.
`frappe.db.get_all()` handles quoting automatically — raw SQL does not.

**Fix:** Backtick all three occurrences: `` `timestamp` `` in the subquery and join condition.

**Files changed:** `f_watcher/dashboards/metrics.py`

---

### BUG-04 — `frappe.only_for("F Watcher Operator")` blocks all users — `actions/cleanup.py` ✅ Fixed 2026-04-13

**Root cause:** `F Watcher Operator` role is referenced in `frappe.only_for()` but never
defined in fixtures. On a fresh install the role does not exist, so both `preview()` and
`execute()` throw `PermissionError` for every user including System Manager and Administrator.
The dialog showed "0 records" or the execute button silently did nothing.

**Fix:** Replaced `frappe.only_for()` with a `_check_permission()` helper that allows
Administrator, System Manager, or F Watcher Operator.

```python
def _check_permission():
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
    ):
        frappe.throw("Not permitted.", frappe.PermissionError)
```

**Files changed:** `f_watcher/actions/cleanup.py`

---

### BUG-05 — Six cleanup dialog bugs — Control Center page JS ✅ Fixed 2026-04-13

All six bugs caused "Execute cleanup does nothing" symptoms in different ways.

| # | Bug | Fix |
|---|-----|-----|
| 5a | `values` captured at Preview-click time — stale days/reason sent to execute | Use `d.get_values()` at both Preview and Execute time |
| 5b | `#upeo-exec-cleanup` global ID selector — binds to detached elements on re-open | Changed to class `.upeo-exec-cleanup`, scoped with `$previewWrap.find(...)` |
| 5c | Execute button shown even on 0 records — misleads user | Replace button with green "Nothing to delete" message when count = 0 |
| 5d | Preview `error()` used page-level `showToast` — hidden behind dialog backdrop | Switched to `frappe.msgprint` which renders above all dialogs |
| 5e | No freeze on "Preview impact" — double-click fires two concurrent API calls | `$primaryBtn.prop("disabled", true)` before call, restored in callback and error |
| 5f | No button lock on Execute — `frappe.confirm` stacked on rapid clicks | Disable button inside confirm callback before `frappe.call` fires |

**Files changed:** `f_watcher/f_watcher/page/f_watcher_control/f_watcher_control.js`

---

### BUG-06 — `app_health.py` queries wrong DocType for scheduled job status ✅ Fixed 2026-04-13

**Root cause:** `collect_scheduled_jobs()` queried `Scheduled Job Type` with
`filters={"status": "Failed"}`. That DocType has no `status` column — it only stores job
definitions with a `stopped` flag. The `status` field lives in `Scheduled Job Log`
(execution history). This produced `(1054, "Unknown column 'status' in 'WHERE'")` every
5 minutes, flooding `tabError Log` and breaking the whole `collect()` call.

**Fix:** Query `Scheduled Job Log` instead, scoped to the last 5 minutes for consistency
with `collect_error_logs()`.

```python
# Before (broken)
frappe.get_all("Scheduled Job Type", filters={"status": "Failed"}, ...)

# After (fixed)
five_mins_ago = add_to_date(now_datetime(), minutes=-5)
frappe.get_all(
    "Scheduled Job Log",
    filters={"status": "Failed", "creation": [">=", five_mins_ago]},
    fields=["name", "scheduled_job_type"],
)
```

**Files changed:** `f_watcher/collectors/app_health.py`

---

## 1.2 Role & Permission Definitions

**Problem:** `F Watcher Operator` role is referenced in `frappe.only_for()` calls across
`actions/cleanup.py`, `actions/control.py`, and `actions/queue.py` but is never defined in
fixtures. Any user without System Manager role gets a cryptic permission error.

**What to do:**

1. Create `f_watcher/f_watcher/role/F Watcher Operator.json`:

```json
{
  "doctype": "Role",
  "role_name": "F Watcher Operator",
  "desk_access": 1,
  "is_custom": 0
}
```

2. Create `f_watcher/f_watcher/role/F Watcher Viewer.json` (read-only monitoring):

```json
{
  "doctype": "Role",
  "role_name": "F Watcher Viewer",
  "desk_access": 1,
  "is_custom": 0
}
```

3. Add both roles to `hooks.py` fixtures:

```python
fixtures = [
    {"dt": "Role", "filters": [["role_name", "in", ["F Watcher Operator", "F Watcher Viewer"]]]},
    # ... existing fixtures
]
```

4. Add DocType permissions to each DocType JSON — recommended matrix:

| DocType | System Manager | F Watcher Operator | F Watcher Viewer |
|---|---|---|---|
| F Watcher System Metric | CRUD | R | R |
| F Watcher Queue Metric | CRUD | RW | R |
| F Watcher DB Metric | CRUD | R | R |
| F Watcher DB Storage Snapshot | CRUD | R | R |
| F Watcher DB Table Storage | CRUD | R | R |
| F Watcher Redis Metric | CRUD | R | R |
| F Watcher App Metric | CRUD | R | R |
| F Watcher Alert Rule | CRUD | RW | R |
| F Watcher Alert Log | CRUD | R | R |
| F Watcher Action Audit | CRUD | R | R |

---

## 1.3 Metric Data Retention (Auto-Cleanup)

**Problem:** Collector data (system metrics, queue metrics, DB metrics, etc.) is written every
1–60 minutes and never deleted. Over weeks this bloats the database significantly.

**Example growth:**
- System Metric @ 1/min → ~43,000 rows/month
- Queue Metric @ 1/min × 3 queues → ~130,000 rows/month
- DB Metric @ 5/min (top 10 queries) → ~86,000 rows/month

**What to do:**

Create `f_watcher/collectors/retention.py`:

```python
from __future__ import annotations
import frappe

RETENTION_DAYS = {
    "F Watcher System Metric": 30,
    "F Watcher Queue Metric": 30,
    "F Watcher DB Metric": 14,
    "F Watcher DB Storage Snapshot": 90,
    "F Watcher DB Table Storage": 30,
    "F Watcher Redis Metric": 30,
    "F Watcher App Metric": 30,
    "F Watcher Alert Log": 90,
    "F Watcher Action Audit": 365,
}

def collect():
    for doctype, days in RETENTION_DAYS.items():
        table = f"tab{doctype}"
        frappe.db.sql(
            f"DELETE FROM `{table}` WHERE creation < DATE_SUB(NOW(), INTERVAL %(days)s DAY)",
            {"days": days},
        )
    frappe.db.commit()
```

Register in `hooks.py` — run daily at midnight:

```python
scheduler_events = {
    # ... existing entries
    "cron": {
        # ... existing cron entries
        "0 2 * * *": [
            "f_watcher.collectors.retention.collect",
        ],
    },
}
```

---

## 1.4 Test Suite Bootstrap

**Problem:** All 10 DocType test files exist but contain only empty skeleton classes.

**What to do:** Write at minimum smoke tests for the three action modules
(`cleanup`, `control`, `queue`) and the two dashboard endpoints (`latest`, `audit`).

Recommended test file structure:

```
f_watcher/
  f_watcher/
    doctype/
      f_watcher_action_audit/
        test_f_watcher_action_audit.py   ← test cleanup + control audit entries
      f_watcher_system_metric/
        test_f_watcher_system_metric.py  ← test collector inserts a record
      f_watcher_alert_rule/
        test_f_watcher_alert_rule.py     ← test alerting engine evaluation
```

Key scenarios to cover:

- `cleanup.preview()` returns correct count
- `cleanup.execute()` deletes rows and creates audit record
- `cleanup.execute()` rejects unknown table names
- `alerting.evaluate_rule()` fires on threshold breach
- `dashboards.metrics.latest()` returns expected shape

---

---

## 1.5 Alerting Engine Bugs

### BUG-07 — `frappe.make_post_request` doesn't exist — `collectors/alerting.py:31`

**Root cause:** `frappe.make_post_request` is not a Frappe API. Every webhook alert has thrown
`AttributeError` silently since day one. Webhooks have never worked.

**Fix:**
```python
# Wrong
frappe.make_post_request(url=rule.webhook_url, data=json.dumps({"text": msg}))

# Right — use requests directly
import requests
requests.post(rule.webhook_url, json={"text": msg}, timeout=5)
```

**Files:** `f_watcher/collectors/alerting.py`

---

### BUG-08 — "System Notification" alert channel not implemented — `collectors/alerting.py`

**Root cause:** The Alert Rule doctype has three channels: Webhook, Email, System Notification.
Only the first two have handler code. Selecting "System Notification" silently does nothing —
no alert is sent and no failure is logged.

**Fix:**
```python
elif rule.alert_channel == "System Notification":
    frappe.publish_realtime(
        event="fw_alert",
        message={"title": rule.rule_name, "message": msg},
        after_commit=True,
    )
```

**Files:** `f_watcher/collectors/alerting.py`

---

### BUG-09 — Missing `frappe.db.commit()` in alerting engine — `collectors/alerting.py`

**Root cause:** After inserting the Alert Log and updating `last_triggered` via `frappe.db.set_value`,
there is no `frappe.db.commit()`. On a background job failure the entire batch rolls back — alerts
are evaluated but nothing is persisted.

**Fix:** Add `frappe.db.commit()` after the `set_value` call inside the trigger block.

**Files:** `f_watcher/collectors/alerting.py`

---

### BUG-10 — `get_latest_metric` missing Backup/Security/Redis types — `collectors/alerting.py`

**Root cause:** The metric type mapping in `get_latest_metric()` only covers System, Database,
and Queue. Alert Rules with `metric_type = Backup`, `Security`, or `Redis` always return `None`
and silently skip — they can never trigger.

**Fix:**
```python
mapping = {
    "System":   "F Watcher System Metric",
    "Database": "F Watcher DB Metric",
    "Queue":    "F Watcher Queue Metric",
    "Redis":    "F Watcher Redis Metric",
    # Backup and Security alerts come from F Watcher Alert Log directly — no separate metric fetch needed
}
```

**Files:** `f_watcher/collectors/alerting.py`

---

## 1.6 Collector Bugs

### BUG-11 — `infrastructure.py` writes partial rows into `F Watcher System Metric`

**Root cause:** `check_node_memory()` calls `frappe.get_doc({"doctype": "F Watcher System Metric", ...})`
with only `ram_used_mb` filled. All other fields (cpu_percent, ram_percent, disk_percent, loads)
are NULL/0. This pollutes the system metric table and distorts dashboard averages and charts.

**Fix:** Write to `F Watcher App Metric` instead with `metric_type = "Node.js Memory"`:
```python
frappe.get_doc({
    "doctype": "F Watcher App Metric",
    "timestamp": now_datetime(),
    "metric_type": "APM Trace",
    "count": node_instances,
    "details": f"Node.js total RSS: {total_node_mem_mb:.1f} MB across {node_instances} processes",
}).insert(ignore_permissions=True)
```

**Files:** `f_watcher/collectors/infrastructure.py`

---

### BUG-12 — `datetime.datetime.utcnow()` deprecated in Python 3.12+ — `collectors/infrastructure.py`

**Root cause:** `datetime.datetime.utcnow()` was deprecated in Python 3.12 and emits
`DeprecationWarning` on every hourly run.

**Fix:**
```python
# Wrong
datetime.datetime.utcnow()

# Right
datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
```

**Files:** `f_watcher/collectors/infrastructure.py`

---

### BUG-13 — Missing `frappe.db.commit()` in `collectors/database.py`

**Root cause:** The slow query collector inserts records in a loop via `frappe.get_doc().insert()`
but never commits. In a background job context the transaction may not auto-commit, causing
slow query records to be lost on every run.

**Fix:** Add `frappe.db.commit()` once after the loop.

**Files:** `f_watcher/collectors/database.py`

---

### BUG-14 — `frappe.db.commit()` called inside loop in `collectors/apm.py`

**Root cause:** `apm.py` commits once per slow path inside the `for q in slow_queries` loop.
For 5 paths this means 5 separate commits instead of one. Wasteful and unnecessary.

**Fix:** Move `frappe.db.commit()` to after the loop.

**Files:** `f_watcher/collectors/apm.py`

---

### BUG-15 — Healthy backup state never recorded — `collectors/backups.py`

**Root cause:** When a backup is healthy the function does `pass` and writes nothing. There is no
way to see backup health history — only failures appear in the logs. The dashboard shows nothing
when backups are fine.

**Fix:** Write a success metric on healthy backup:
```python
frappe.get_doc({
    "doctype": "F Watcher App Metric",
    "timestamp": now_datetime(),
    "metric_type": "Backup",
    "count": 1,
    "details": f"Latest backup is {diff_hours:.1f}h old — OK",
}).insert(ignore_permissions=True)
frappe.db.commit()
```

**Files:** `f_watcher/collectors/backups.py`

---

### BUG-16 — `security.py` inserts active sessions metric even when 0 — `collectors/security.py`

**Root cause:** `track_active_sessions()` always inserts a `F Watcher App Metric` record
every 15 minutes regardless of session count. At zero sessions this is pure noise.

**Fix:** Guard with `if active_sessions > 0:` before inserting.

**Files:** `f_watcher/collectors/security.py`

---

## 1.7 Log Viewer Bugs (Fixed)

### LV-01 through LV-08 ✅ Fixed 2026-04-13

All 8 log viewer bugs were fixed: poll interval not clearing on navigation, global selectors,
handler accumulation, no error callback, auto-scroll fighting manual scroll, concurrent request
stacking, invalid CSS font-family, and missing server-side lines cap.

**Files:** `f_watcher/f_watcher/page/f_watcher_log_viewer/f_watcher_log_viewer.js`,
`f_watcher/f_watcher/page/f_watcher_log_viewer/f_watcher_log_viewer.html`,
`f_watcher/api/logs.py`

---

## Checklist

**Bug Fixes — Done**
- [x] BUG-01 — `affected_rows` AttributeError in `actions/cleanup.py`
- [x] BUG-02 — Duplicate rows in big_tables dashboard query
- [x] BUG-03 — Unquoted `timestamp` reserved keyword in raw SQL
- [x] BUG-04 — `frappe.only_for` blocking System Manager in cleanup
- [x] BUG-05 — 6 cleanup dialog bugs in Control Center JS
- [x] BUG-06 — `app_health.py` querying wrong DocType for scheduled job status
- [x] LV-01 through LV-08 — 8 log viewer bugs

**Bug Fixes — Pending**
- [ ] BUG-07 — `frappe.make_post_request` doesn't exist → webhooks broken (`alerting.py`)
- [ ] BUG-08 — System Notification channel not implemented (`alerting.py`)
- [ ] BUG-09 — Missing `frappe.db.commit()` in alerting engine (`alerting.py`)
- [ ] BUG-10 — `get_latest_metric` missing Backup/Security/Redis types (`alerting.py`)
- [ ] BUG-11 — `infrastructure.py` writes partial rows to System Metric
- [ ] BUG-12 — `datetime.utcnow()` deprecated in Python 3.12+ (`infrastructure.py`)
- [ ] BUG-13 — Missing `frappe.db.commit()` in `database.py`
- [ ] BUG-14 — `frappe.db.commit()` inside loop in `apm.py`
- [ ] BUG-15 — Healthy backup state never recorded (`backups.py`)
- [ ] BUG-16 — Sessions metric inserted even at 0 (`security.py`)

**Role & Permissions**
- [ ] Define `F Watcher Operator` role in fixtures
- [ ] Define `F Watcher Viewer` role in fixtures
- [ ] Add DocType permission rows for all 10 DocTypes

**Metric Data Retention**
- [ ] Create `collectors/retention.py` with daily cleanup job
- [ ] Register retention job in `hooks.py`

**Test Suite**
- [ ] Write smoke tests for `actions/cleanup.py`
- [ ] Write smoke tests for `actions/control.py`
- [ ] Write smoke tests for `dashboards/metrics.py`
- [ ] Write smoke test for `collectors/system.py`
- [ ] Write smoke tests for `collectors/alerting.py`
