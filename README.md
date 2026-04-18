# F Watcher

**Production observability for Frappe v16.** Monitors system health, queues, logs, database, security, and developer tools — all from a single Control Center page inside your Frappe desk.

---

## Features

### Control Center (`/f-watcher-control`)
Live dashboard that auto-refreshes without page reloads.

| Section | What it shows |
|---------|---------------|
| **KPI strip** | CPU %, RAM %, Disk % with delta arrows vs. the previous period and disk-full forecast |
| **Uptime badge** | Site uptime % over the last 24 hours |
| **Health map** | Per-service status pills (DB, Redis, Scheduler, Workers, Backups, SSL, APM) |
| **Collector status** | Last-run time for every background collector |
| **Alert rules** | Threshold rules with cooldown — fires to System Notification, email, or webhook |
| **Maintenance window** | Schedule a window; alerts are silenced automatically during it |
| **Redis / Cache** | Memory usage, hit rate, eviction policy, keyspace stats |
| **Queue inspector** | Per-queue depth and failed-job count; browse queued/failed jobs, view full traceback, retry or cancel |
| **Scheduler timeline** | Last 100 scheduled-job runs with status and details |
| **Active Sessions** | Authenticated sessions with IP address and last-active time; force-logout any session |
| **SSL certificates** | Days-to-expiry for monitored domains |
| **Installed Apps** | Version, git branch, and commit per installed Frappe app |
| **Patch history** | Last 40 applied Frappe migration patches |
| **Customization audit** | Custom fields, Client Scripts, Server Scripts, and Property Setter count |
| **Error patterns** | Top repeated errors grouped by message prefix |
| **Charts** | CPU / RAM / Disk / DB size history (Chart.js), with CSV export |

### Log Viewer (`/f-watcher-log-viewer`)
Live tail of Frappe error and access logs with pause/resume, auto-scroll control, and line-cap safety.

### DB Query Explorer (`/f-watcher-query-explorer`)
- Slow query analysis from `tabDB Query` with execution count and worst/average duration
- **Slow HTTP Requests** table from `tabMonitor` — paths taking over 500 ms, grouped by route and method

---

## Background Collectors

Collectors run on Frappe's scheduler and write to dedicated DocTypes.

| Collector | Schedule | DocType written |
|-----------|----------|-----------------|
| System metrics (CPU / RAM / Disk) | Every minute | `F Watcher System Metric` |
| Queue metrics | Every minute | `F Watcher Queue Metric` |
| Redis metrics | Every 5 minutes | `F Watcher Redis Metric` |
| DB metrics | Every 5 minutes | `F Watcher DB Metric` |
| DB storage snapshots | Every 5 minutes | `F Watcher DB Storage Snapshot` |
| Uptime check (DB + Redis ping) | Every 5 minutes | `F Watcher Uptime Record` |
| API key audit (stale / new keys) | Every hour | `F Watcher App Metric` |
| Security (failed logins, brute-force, bulk deletes) | Every 5 minutes | `F Watcher Alert Log`, `F Watcher App Metric` |
| APM (slow queries, HTTP traces) | Every minute | `F Watcher App Metric` |
| Infrastructure (SSL expiry) | Every hour | `F Watcher App Metric` |
| Alert engine | Every minute | `F Watcher Alert Log` |
| Retention cleanup | Daily | *(deletes old rows)* |
| Weekly digest email | Monday 08:00 | *(email only)* |

---

## DocTypes

| DocType | Purpose |
|---------|---------|
| `F Watcher System Metric` | CPU, RAM, Disk snapshots |
| `F Watcher Queue Metric` | RQ queue depth and failed-job counts |
| `F Watcher Redis Metric` | Redis memory and keyspace stats |
| `F Watcher DB Metric` | MariaDB connection and query stats |
| `F Watcher DB Storage Snapshot` | Total and table-level DB size over time |
| `F Watcher DB Table Storage` | Per-table size rows |
| `F Watcher Alert Rule` | User-defined threshold rules |
| `F Watcher Alert Log` | Triggered alert history |
| `F Watcher App Metric` | General key/value metric store for collectors |
| `F Watcher Maintenance Window` | Scheduled alert-silence windows |
| `F Watcher Cleanup Rule` | Data retention configuration per DocType |
| `F Watcher Action Audit` | Audit trail for operator actions (e.g. force logout) |
| `F Watcher Uptime Record` | DB + Redis uptime probe results |

---

## Roles

| Role | Access |
|------|--------|
| `System Manager` | Full access |
| `F Watcher Operator` | Read + write; can run actions (force logout, retry jobs, etc.) |
| `F Watcher Viewer` | Read-only; no destructive actions |

---

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench install-app f_watcher
```

---

## Development

### Pre-commit

```bash
cd apps/f_watcher
pre-commit install
```

Configured linters: `ruff`, `eslint`, `prettier`, `pyupgrade`.

### Tests

```bash
cd $PATH_TO_YOUR_BENCH
bench run-tests --app f_watcher
```

Tests use `unittest.TestCase` with mocked Frappe internals — no live site required.

### CI

- **CI workflow**: installs the app and runs unit tests on every push to the `version-16` branch.
- **Linters workflow**: runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and `pip-audit` on every pull request.

---

## License

GPL-3.0
