# Phase 2 — Visibility & Usability

> Goal: Add time-series charts, a dependency health map, navbar alert badge, and WebSocket log streaming.
> This phase transforms the app from a "numbers dashboard" into a real observability tool.

---

## 2.1 Time-Series Charts (Frappe Charts)

**Problem:** The Control Center shows only the *latest* values for CPU, RAM, Disk, and Queue.
There is no way to see trends, spikes, or degradation over time.

**What to do:**

Add a `history()` endpoint in `f_watcher/dashboards/metrics.py`:

```python
@frappe.whitelist()
def history(hours: int = 6):
    """Return time-bucketed metric series for charting."""
    hours = min(int(hours), 72)  # cap at 3 days
    since = frappe.utils.add_to_date(None, hours=-hours)

    system = frappe.db.sql("""
        SELECT
            DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i:00') AS bucket,
            AVG(cpu_percent)  AS cpu,
            AVG(ram_percent)  AS ram,
            AVG(disk_percent) AS disk
        FROM `tabF Watcher System Metric`
        WHERE timestamp >= %(since)s
        GROUP BY bucket
        ORDER BY bucket ASC
        LIMIT 500
    """, {"since": since}, as_dict=True)

    queues = frappe.db.sql("""
        SELECT
            DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i:00') AS bucket,
            queue_name,
            AVG(job_count)    AS job_count,
            SUM(failed_count) AS failed_count
        FROM `tabF Watcher Queue Metric`
        WHERE timestamp >= %(since)s
        GROUP BY bucket, queue_name
        ORDER BY bucket ASC
        LIMIT 1000
    """, {"since": since}, as_dict=True)

    return {"system": system, "queues": queues}
```

**Frontend implementation in Control Center page:**

```javascript
// Add after existing KPI render
function renderCharts(data) {
    const labels = data.system.map(r => r.bucket.slice(11, 16)); // HH:MM
    new frappe.Chart("#cpu-chart", {
        type: "line",
        data: {
            labels,
            datasets: [
                { name: "CPU %",  values: data.system.map(r => r.cpu)  },
                { name: "RAM %",  values: data.system.map(r => r.ram)  },
                { name: "Disk %", values: data.system.map(r => r.disk) },
            ],
        },
        colors: ["#5e64ff", "#f59e0b", "#ef4444"],
        lineOptions: { regionFill: 1 },
        axisOptions: { xIsSeries: true },
    });
}
```

Chart containers to add in the page HTML:
- `#cpu-chart` — CPU / RAM / Disk % over time (line, area fill)
- `#queue-chart` — job_count per queue over time (bar or line)
- `#db-size-chart` — DB total_mb trend (line)

Time-range selector: 1h / 6h / 24h / 7d buttons, re-fetches `history(hours=N)`.

---

## 2.2 Dependency Health Map

**Problem:** There is no single view showing the live status of all critical dependencies
(MySQL, Redis, Scheduler, Workers, Socket.IO).

**What to do:**

Create a new API endpoint `f_watcher/api/health.py`:

```python
import frappe
import redis as redis_lib
from frappe.utils.background_jobs import get_redis_conn

@frappe.whitelist()
def check():
    results = {}

    # MySQL
    try:
        frappe.db.sql("SELECT 1")
        results["mysql"] = {"status": "ok"}
    except Exception as e:
        results["mysql"] = {"status": "error", "detail": str(e)}

    # Redis cache
    try:
        r = redis_lib.from_url(frappe.conf.redis_cache)
        r.ping()
        results["redis_cache"] = {"status": "ok"}
    except Exception as e:
        results["redis_cache"] = {"status": "error", "detail": str(e)}

    # Redis queue
    try:
        conn = get_redis_conn()
        conn.ping()
        results["redis_queue"] = {"status": "ok"}
    except Exception as e:
        results["redis_queue"] = {"status": "error", "detail": str(e)}

    # Scheduler (last heartbeat within 5 minutes)
    try:
        from frappe.utils import now_datetime, get_datetime
        last = frappe.db.get_value("Scheduled Job Log", {"status": "Complete"},
                                   "creation", order_by="creation desc")
        if last and (now_datetime() - get_datetime(last)).seconds < 360:
            results["scheduler"] = {"status": "ok", "last_run": str(last)}
        else:
            results["scheduler"] = {"status": "warn", "detail": "No job completed in last 6 min"}
    except Exception as e:
        results["scheduler"] = {"status": "error", "detail": str(e)}

    # Workers — check active RQ workers
    try:
        from rq import Worker
        workers = Worker.all(connection=get_redis_conn())
        results["workers"] = {"status": "ok" if workers else "warn",
                              "count": len(workers)}
    except Exception as e:
        results["workers"] = {"status": "error", "detail": str(e)}

    return results
```

**Frontend:** Render as a row of colored status nodes in the Control Center header:

```
[ MySQL: OK ]  [ Redis Cache: OK ]  [ Redis Queue: OK ]  [ Scheduler: WARN ]  [ Workers: 3 ]
```

Color coding: green = ok, yellow = warn, red = error. Auto-refresh every 30 seconds.

---

## 2.3 Navbar Alert Badge

**Problem:** There is no way to know alerts are firing without opening the Control Center.
ERPNext-style badge on the desk navbar would surface active alerts immediately.

**What to do:**

Add a `notification_config` hook in `hooks.py`:

```python
notification_config = "f_watcher.notifications.get_notification_config"
```

Create `f_watcher/notifications.py`:

```python
import frappe

def get_notification_config():
    return {
        "for_doctype": {
            "F Watcher Alert Log": {
                "status": "Triggered",
            },
        },
    }
```

This plugs into Frappe's standard notification badge system — the count of unacknowledged
`F Watcher Alert Log` records with `status = Triggered` appears next to the app icon.

---

## 2.4 WebSocket Log Streaming

**Problem:** The Log Viewer polls `tail_log` every 4 seconds via HTTP. This causes:
- 15 requests/minute per open tab
- 200ms+ visible jump on each refresh
- No visual indication of new vs old lines

**What to do:**

Use Frappe's built-in `frappe.realtime.emit` to push log lines server-side.

Create `f_watcher/api/log_stream.py`:

```python
import frappe
import os
from frappe.utils import get_bench_path

ALLOWED = ["frappe.log", "web.error.log", "worker.error.log",
           "schedule.error.log", "node-socketio.error.log"]

@frappe.whitelist()
def start_stream(filename: str):
    if not frappe.has_permission("F Watcher System Metric", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    if filename not in ALLOWED:
        frappe.throw("Invalid log file")

    # Enqueue a background job that tails and emits
    frappe.enqueue(
        "f_watcher.api.log_stream._tail_and_emit",
        filename=filename,
        user=frappe.session.user,
        queue="short",
        timeout=300,
    )
    return {"status": "streaming"}

def _tail_and_emit(filename: str, user: str):
    log_path = os.path.join(get_bench_path(), "logs", filename)
    import subprocess, time
    proc = subprocess.Popen(["tail", "-n", "50", "-f", log_path],
                             stdout=subprocess.PIPE, text=True)
    start = time.time()
    for line in proc.stdout:
        frappe.publish_realtime(
            event="fw_log_line",
            message={"line": line.rstrip()},
            user=user,
        )
        if time.time() - start > 280:  # stop after ~5 min
            break
    proc.terminate()
```

**Frontend:** Replace setInterval polling with:

```javascript
frappe.realtime.on("fw_log_line", (data) => {
    appendLine(data.line);
});
frappe.call("f_watcher.api.log_stream.start_stream", { filename });
```

---

## 2.5 Scheduled Health Digest Email

**Problem:** No proactive reporting. Operators only know about issues if they open the dashboard.

**What to do:**

Create `f_watcher/collectors/digest.py`:

```python
import frappe
from frappe.utils import now_datetime, add_to_date

def send_daily_digest():
    """Send a daily health summary email to all F Watcher Operator users."""
    since = add_to_date(None, days=-1)

    # Gather 24h summary
    avg = frappe.db.sql("""
        SELECT AVG(cpu_percent) cpu, MAX(cpu_percent) max_cpu,
               AVG(ram_percent) ram, MAX(disk_percent) disk
        FROM `tabF Watcher System Metric`
        WHERE timestamp >= %(since)s
    """, {"since": since}, as_dict=True)[0]

    alerts = frappe.db.count("F Watcher Alert Log",
                              {"status": "Triggered", "timestamp": [">=", since]})

    failed_jobs = frappe.db.sql("""
        SELECT SUM(failed_count) FROM `tabF Watcher Queue Metric`
        WHERE timestamp >= %(since)s
    """, {"since": since})[0][0] or 0

    recipients = frappe.get_all("Has Role",
                                 filters={"role": "F Watcher Operator"},
                                 fields=["parent"],
                                 pluck="parent")

    if not recipients:
        return

    subject = f"[F Watcher] Daily Health Digest — {now_datetime().strftime('%Y-%m-%d')}"
    message = f"""
    <h3>System Summary (last 24h)</h3>
    <ul>
      <li>CPU avg: {avg.cpu:.1f}% | peak: {avg.max_cpu:.1f}%</li>
      <li>RAM avg: {avg.ram:.1f}%</li>
      <li>Disk peak: {avg.disk:.1f}%</li>
      <li>Alerts triggered: {alerts}</li>
      <li>Failed queue jobs: {failed_jobs}</li>
    </ul>
    """

    frappe.sendmail(recipients=recipients, subject=subject, message=message)
```

Register in `hooks.py`:

```python
"0 8 * * *": ["f_watcher.collectors.digest.send_daily_digest"],
```

---

---

## 2.6 Log Viewer Enhancements

**Problem:** The log viewer shows raw text only. No filtering, no color coding, no way to
pause or save. Reading through errors requires manually scanning walls of monochrome text.

**What to do:**

### 2.6a — Search / Filter bar

Add a live filter input that hides non-matching lines client-side (no extra API call):

```javascript
$body.find('#log_search').on('input', function() {
    const term = $(this).val().toLowerCase();
    const lines = $output.text().split('\n');
    const filtered = term
        ? lines.filter(l => l.toLowerCase().includes(term))
        : lines;
    $output.text(filtered.join('\n'));
});
```

Add to HTML:
```html
<input id="log_search" class="form-control" style="width:220px;"
       placeholder="Filter lines…" type="search">
```

### 2.6b — Line color coding by severity

After setting output text, apply regex-based CSS spans to highlight severity:

```javascript
function colorize(raw) {
    return raw
        .replace(/^(.*\bERROR\b.*)$/gm, '<span style="color:#ff6b6b;">$1</span>')
        .replace(/^(.*\bWARNING\b.*)$/gm, '<span style="color:#ffd93d;">$1</span>')
        .replace(/^(.*\bCRITICAL\b.*)$/gm, '<span style="color:#ff4757;font-weight:bold;">$1</span>')
        .replace(/^(.*\bINFO\b.*)$/gm, '<span style="color:#7bed9f;">$1</span>');
}
// Use $output.html(colorize(text)) instead of $output.text(text)
// Note: escape HTML first to prevent XSS before applying spans
```

### 2.6c — Pause / Resume button

Stop the poll while reading without leaving the page:

```javascript
let paused = false;
$body.find('#log_pause_btn').on('click', function() {
    paused = !paused;
    $(this).text(paused ? '▶ Resume' : '⏸ Pause');
    if (!paused) fetch_logs();
});
// In schedulePoll(): if (paused) return;
```

### 2.6d — Copy to clipboard & Download

```javascript
$body.find('#log_copy_btn').on('click', () => {
    navigator.clipboard.writeText($output.text())
        .then(() => frappe.show_alert({ message: 'Copied to clipboard', indicator: 'green' }));
});

$body.find('#log_download_btn').on('click', () => {
    const blob = new Blob([$output.text()], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = $selector.val() + '_' + frappe.datetime.now_datetime() + '.log';
    a.click();
});
```

---

## 2.7 Control Center Enhancements

### 2.7a — Collector Health Panel

**Problem:** No way to know if a collector is silently failing. You only discover broken
collectors by noticing stale data or checking `tabError Log` manually.

**What to do:**

Add a `collector_status()` API endpoint in `dashboards/metrics.py`:

```python
@frappe.whitelist()
def collector_status():
    collectors = [
        ("System",       "F Watcher System Metric",       5),
        ("Queue",        "F Watcher Queue Metric",         5),
        ("DB Storage",   "F Watcher DB Storage Snapshot", 10),
        ("DB Queries",   "F Watcher DB Metric",           10),
        ("Redis",        "F Watcher Redis Metric",        10),
        ("App Health",   "F Watcher App Metric",          10),
    ]
    result = []
    for label, doctype, max_minutes in collectors:
        last = frappe.db.get_value(doctype, {}, "creation", order_by="creation desc")
        if not last:
            status = "never"
        else:
            minutes_ago = (frappe.utils.now_datetime() - frappe.utils.get_datetime(last)).seconds // 60
            status = "ok" if minutes_ago <= max_minutes else "stale"
        result.append({"label": label, "status": status, "last": str(last or "")})
    return result
```

Render as a compact row of colored indicator dots in the Control Center below the health KPIs.

### 2.7b — Active Alert Rules Panel

Show all active alert rules with their current metric value and threshold inline — no need to
open the Alert Rule list to see what's being monitored:

```javascript
// New section rendered after $health
// Shows: rule_name | metric | current_value | threshold | status (OK / FIRING)
```

### 2.7c — System Health Score (0–100)

Compute a composite score from latest metrics and show it as a prominent badge:

```javascript
function healthScore(sys, queues) {
    if (!sys) return null;
    let score = 100;
    if (sys.cpu_percent > 90)  score -= 30;
    else if (sys.cpu_percent > 70) score -= 15;
    if (sys.ram_percent > 90)  score -= 25;
    else if (sys.ram_percent > 75) score -= 10;
    if (sys.disk_percent > 90) score -= 20;
    else if (sys.disk_percent > 80) score -= 10;
    const totalFailed = (queues || []).reduce((s, q) => s + (q.failed_count || 0), 0);
    if (totalFailed > 10) score -= 15;
    else if (totalFailed > 0) score -= 5;
    return Math.max(0, score);
}
```

Display as colored badge: ≥80 green, 60–79 yellow, <60 red.

### 2.7d — Retry Failed Jobs Button in UI

`actions/queue.py` already has `retry_failed_jobs(queue_name)` but there is no UI button
to call it. Add per-queue retry buttons in the Queue section of the Control Center.

---

## Checklist

**Original items**
- [ ] Add `history()` endpoint to `dashboards/metrics.py`
- [ ] Add time-range selector + Frappe Charts rendering to Control Center page
- [ ] Create `api/health.py` with dependency status checks
- [ ] Add dependency health map row to Control Center page header
- [ ] Add `notification_config` hook + `notifications.py` for navbar badge
- [ ] Create `api/log_stream.py` for WebSocket-based log tailing
- [ ] Replace Log Viewer polling with `frappe.realtime` listener
- [ ] Create `collectors/digest.py` for daily email digest
- [ ] Register digest job in `hooks.py` at 08:00 daily

**Log Viewer enhancements**
- [ ] 2.6a — Search/filter bar (client-side, no API)
- [ ] 2.6b — Line color coding by severity (ERROR/WARNING/CRITICAL/INFO)
- [ ] 2.6c — Pause / Resume button for auto-poll
- [ ] 2.6d — Copy to clipboard + Download as file buttons

**Control Center enhancements**
- [ ] 2.7a — Collector health panel with last-run status dots
- [ ] 2.7b — Active alert rules panel with live current values
- [ ] 2.7c — System health score (0–100) badge in page header
- [ ] 2.7d — Retry failed jobs button per queue in UI
