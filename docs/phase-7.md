# Phase 7 — Developer Tools & Framework Health

> Goal: Give developers deep visibility into the Frappe framework itself —
> app versions, migration history, patch logs, background job code,
> and custom field sprawl — so the platform is as observable as the application.

---

## 7.1 Installed Apps Version Monitor

**Problem:** There is no way to see which Frappe apps are installed, what version they're
on, or whether they're behind their latest Git tag — without using the terminal.

**What to do:**

Create `api/apps.py`:
```python
@frappe.whitelist()
def installed_apps():
    _check_permission()
    import subprocess, os
    from frappe.utils import get_bench_path

    apps = []
    apps_path = os.path.join(get_bench_path(), "apps")

    for app_name in frappe.get_installed_apps():
        app_info = {"name": app_name, "version": None, "branch": None,
                    "last_commit": None, "behind": None}
        app_path = os.path.join(apps_path, app_name)
        try:
            ver = frappe.get_attr(f"{app_name}.__version__", None) \
                  or frappe.get_attr(f"{app_name}.__version__", None)
            app_info["version"] = str(ver) if ver else "unknown"

            branch = subprocess.check_output(
                ["git", "-C", app_path, "rev-parse", "--abbrev-ref", "HEAD"],
                text=True, stderr=subprocess.DEVNULL).strip()
            app_info["branch"] = branch

            log = subprocess.check_output(
                ["git", "-C", app_path, "log", "-1", "--format=%h %s", "--date=short"],
                text=True, stderr=subprocess.DEVNULL).strip()
            app_info["last_commit"] = log
        except Exception:
            pass
        apps.append(app_info)

    return apps
```

Add an "Installed Apps" card to the Control Center showing: app name, version,
git branch, last commit hash + message. Flag apps not on `main`/`master`/`version-*`
branch in yellow.

---

## 7.2 Migration & Patch History Viewer

**Problem:** When something breaks after an update, developers need to know which patches
ran recently. Currently this requires reading `frappe.log` or running `bench migrate`
output manually.

**What to do:**

Add a `patch_history()` API endpoint:
```python
@frappe.whitelist()
def patch_history(limit: int = 50):
    _check_permission()
    return frappe.db.sql("""
        SELECT patch, creation
        FROM `tabPatch Log`
        ORDER BY creation DESC
        LIMIT %(limit)s
    """, {"limit": int(limit)}, as_dict=True)
```

Show in a new "Framework" section of the Control Center: last 20 patches applied with
timestamps. Highlight patches from the last 24h in yellow so developers can correlate
issues to recent migrations.

---

## 7.3 Custom Field & DocType Sprawl Auditor

**Problem:** Over time, systems accumulate custom fields, custom scripts, server scripts,
and custom DocTypes added via the UI. These are invisible in code review, never cleaned up,
and can cause unexpected behavior or performance issues.

**What to do:**

Create `api/customizations.py`:
```python
@frappe.whitelist()
def audit():
    _check_permission()
    custom_fields = frappe.db.count("Custom Field")
    custom_scripts = frappe.db.count("Client Script")
    server_scripts = frappe.db.count("Server Script")
    custom_doctypes = frappe.db.count("DocType", {"custom": 1})
    property_setters = frappe.db.count("Property Setter")

    top_customized = frappe.db.sql("""
        SELECT dt AS doctype, COUNT(name) AS custom_field_count
        FROM `tabCustom Field`
        GROUP BY dt
        ORDER BY custom_field_count DESC
        LIMIT 10
    """, as_dict=True)

    return {
        "custom_fields": custom_fields,
        "client_scripts": custom_scripts,
        "server_scripts": server_scripts,
        "custom_doctypes": custom_doctypes,
        "property_setters": property_setters,
        "top_customized_doctypes": top_customized,
    }
```

Show as a compact "Customization Audit" card in the Control Center.

---

## 7.4 Background Job Code Inspector

**Problem:** When a background job fails, the error log shows the exception but not what
the job was actually trying to do. Developers have to cross-reference the job function
name with the codebase manually.

**What to do:**

Extend the Queue Job Inspector (Phase 4.3) — when viewing a failed job, add a "View
traceback" expandable that shows the full `exc_info` from the RQ job:

```python
@frappe.whitelist()
def job_detail(job_id: str, queue_name: str = "default"):
    _check_permission()
    from rq import Queue
    from frappe.utils.background_jobs import get_redis_conn
    conn = get_redis_conn()
    q = Queue(queue_name, connection=conn)
    job = q.fetch_job(job_id)
    if not job:
        frappe.throw("Job not found.")
    return {
        "id": job.id,
        "func": job.func_name,
        "args": str(job.args),
        "kwargs": str(job.kwargs),
        "enqueued_at": str(job.enqueued_at),
        "status": job.get_status(),
        "exc_info": job.exc_info or "",
        "description": job.description or "",
    }
```

---

## 7.5 Scheduler Health Timeline

**Problem:** `app_health.py` now correctly queries `Scheduled Job Log` for failures,
but there is no visual timeline showing which scheduled jobs ran, when, and whether
they succeeded or failed across the last 24 hours.

**What to do:**

Add a `scheduler_timeline()` API endpoint:
```python
@frappe.whitelist()
def scheduler_timeline(hours: int = 24):
    since = frappe.utils.add_to_date(None, hours=-int(hours))
    return frappe.db.sql("""
        SELECT
            scheduled_job_type,
            status,
            creation,
            details
        FROM `tabScheduled Job Log`
        WHERE creation >= %(since)s
        ORDER BY creation DESC
        LIMIT 200
    """, {"since": since}, as_dict=True)
```

Render as a compact timeline grid (rows = job types, columns = time buckets) in the
Control Center, with green/red cells per run. This makes it immediately obvious which
job type is consistently failing.

---

## 7.6 Frappe Monitor Integration (APM Deep Dive)

**Problem:** `collectors/apm.py` collects the top 5 slowest paths from `tabMonitor` but
discards everything else. Developers have no way to investigate a slow endpoint in depth —
see its parameters, session user, or stack trace.

**What to do:**

Add a `slow_requests()` detail endpoint:
```python
@frappe.whitelist()
def slow_requests(path: str = None, hours: int = 1, limit: int = 20):
    since = frappe.utils.add_to_date(None, hours=-int(hours))
    filters = {"creation": [">=", since], "duration": [">", 1000000]}
    if path:
        filters["path"] = path
    return frappe.get_all(
        "Monitor",
        filters=filters,
        fields=["name", "transaction_type", "request_method", "path",
                "duration", "creation", "site", "user"],
        order_by="duration desc",
        limit=int(limit),
    )
```

Add a "Slow Requests" expandable section in the DB Query Explorer page (Phase 3.2)
or as a standalone tab in the Control Center.

---

## Checklist

- [ ] 7.1 — Create `api/apps.py` with `installed_apps()`
- [ ] 7.1 — Add Installed Apps card to Control Center
- [ ] 7.2 — Add `patch_history()` API endpoint
- [ ] 7.2 — Add patch history section to Control Center (last 20 patches)
- [ ] 7.3 — Create `api/customizations.py` with `audit()`
- [ ] 7.3 — Add Customization Audit card to Control Center
- [ ] 7.4 — Add `job_detail()` API with traceback to Queue Job Inspector
- [ ] 7.5 — Add `scheduler_timeline()` API
- [ ] 7.5 — Render scheduler timeline grid in Control Center
- [ ] 7.6 — Add `slow_requests()` detail endpoint
- [ ] 7.6 — Add Slow Requests section to DB Query Explorer / Control Center
