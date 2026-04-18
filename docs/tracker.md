# F Watcher — Upgrade Tracker

> Last updated: 2026-04-13
> Branch: version-16

---

## Legend

| Symbol | Meaning |
|--------|---------|
| [x] | Done |
| [-] | In progress |
| [ ] | Pending |
| [!] | Blocked |

---

## Phase 1 — Stability & Correctness
> Full spec: [phase-1.md](phase-1.md)
> **Goal:** Fix all known bugs. No collector should silently fail. No action should crash.

### Bug Fixes — Done

| # | Task | File |
|---|------|------|
| BUG-01 | [x] `affected_rows` AttributeError on cleanup execute | `actions/cleanup.py` |
| BUG-02 | [x] Duplicate table rows in "Biggest tables" — missing GROUP BY | `dashboards/metrics.py` |
| BUG-03 | [x] Unquoted `timestamp` reserved keyword in raw SQL | `dashboards/metrics.py` |
| BUG-04 | [x] `frappe.only_for` blocking System Manager (role not in fixtures) | `actions/cleanup.py` |
| BUG-05a | [x] Cleanup dialog uses stale `values` at execute time | `page/f_watcher_control.js` |
| BUG-05b | [x] Global `#upeo-exec-cleanup` selector binds to detached elements | `page/f_watcher_control.js` |
| BUG-05c | [x] Execute button shown when preview returns 0 records | `page/f_watcher_control.js` |
| BUG-05d | [x] Preview error() uses page toast hidden behind dialog backdrop | `page/f_watcher_control.js` |
| BUG-05e | [x] No freeze on "Preview impact" — double-click fires concurrent calls | `page/f_watcher_control.js` |
| BUG-05f | [x] No lock on Execute — rapid clicks stack frappe.confirm dialogs | `page/f_watcher_control.js` |
| BUG-06 | [x] `app_health.py` queries Scheduled Job Type for status (column doesn't exist) | `collectors/app_health.py` |
| LV-01 | [x] `$(wrapper).on('hide')` never fires — poll never clears on navigation | `page/f_watcher_log_viewer.js` |
| LV-02 | [x] Global `$('#...')` selectors break on page re-render | `page/f_watcher_log_viewer.js` |
| LV-03 | [x] Event handlers accumulate on each re-render | `page/f_watcher_log_viewer.js` |
| LV-04 | [x] No error callback — failures are silent | `page/f_watcher_log_viewer.js` |
| LV-05 | [x] Auto-scroll fights manual scroll (yanks to bottom every 4s) | `page/f_watcher_log_viewer.js` |
| LV-06 | [x] setInterval stacks concurrent requests on slow server | `page/f_watcher_log_viewer.js` |
| LV-07 | [x] `font-family: inherit, monospace` — invalid CSS, breaks page load | `page/f_watcher_log_viewer.html` |
| LV-08 | [x] No server-side lines cap | `api/logs.py` |

### Bug Fixes — Pending

| # | Task | File |
|---|------|------|
| BUG-07 | [x] `frappe.make_post_request` doesn't exist — webhooks never fire | `collectors/alerting.py` |
| BUG-08 | [x] "System Notification" alert channel not implemented | `collectors/alerting.py` |
| BUG-09 | [x] Missing `frappe.db.commit()` in alerting engine | `collectors/alerting.py` |
| BUG-10 | [x] `get_latest_metric` missing Backup/Security/Redis types | `collectors/alerting.py` |
| BUG-11 | [x] `check_node_memory()` writes partial rows to System Metric | `collectors/infrastructure.py` |
| BUG-12 | [x] `datetime.utcnow()` deprecated in Python 3.12+ | `collectors/infrastructure.py` |
| BUG-13 | [x] Missing `frappe.db.commit()` after slow query loop | `collectors/database.py` |
| BUG-14 | [x] `frappe.db.commit()` called inside loop | `collectors/apm.py` |
| BUG-15 | [x] Healthy backup state never recorded | `collectors/backups.py` |
| BUG-16 | [x] Sessions metric inserted even at 0 active sessions | `collectors/security.py` |

### Role & Permissions

| Task | Status |
|------|--------|
| Define `F Watcher Operator` role in fixtures | [x] |
| Define `F Watcher Viewer` role in fixtures | [x] |
| Add DocType permission rows for all 10 DocTypes | [x] |

### Metric Data Retention

| Task | Status |
|------|--------|
| Create `collectors/retention.py` | [x] |
| Register daily retention job in `hooks.py` (02:00) | [x] |

### Test Suite

| Task | Status |
|------|--------|
| Tests for `actions/cleanup.py` | [x] |
| Tests for `actions/control.py` | [x] |
| Tests for `dashboards/metrics.py` | [x] |
| Tests for `collectors/system.py` | [x] |
| Tests for `collectors/alerting.py` | [x] |

---

## Phase 2 — Visibility & Usability
> Full spec: [phase-2.md](phase-2.md)
> **Goal:** Charts, health map, alert badge, log enhancements, control center upgrades.

| Task | Status |
|------|--------|
| `history()` endpoint — time-bucketed metrics | [x] |
| Time-range selector in Control Center (1h/6h/24h/7d) | [x] |
| CPU/RAM/Disk line chart (Frappe Charts, area fill) | [x] |
| Queue depth chart per queue | [x] |
| DB size trend chart | [x] |
| `api/health.py` — MySQL, Redis, Scheduler, Workers status | [x] |
| Dependency health map row in Control Center header | [x] |
| `notification_config` hook + `notifications.py` for navbar badge | [x] |
| `api/log_stream.py` — WebSocket log tailing | [x] |
| Replace Log Viewer polling with `frappe.realtime` listener | [x] |
| `collectors/digest.py` — daily email digest | [x] |
| Register digest at 08:00 daily in `hooks.py` | [x] |
| 2.6a — Log Viewer search/filter bar | [x] |
| 2.6b — Log Viewer line color coding by severity | [x] |
| 2.6c — Log Viewer pause/resume button | [x] |
| 2.6d — Log Viewer copy + download buttons | [x] |
| 2.7a — Collector health panel (last-run status per collector) | [x] |
| 2.7b — Active alert rules panel with live values | [x] |
| 2.7c — System health score (0–100) badge in header | [x] |
| 2.7d — Retry failed jobs button per queue in UI | [x] |

---

## Phase 3 — Intelligence & Advanced Monitoring
> Full spec: [phase-3.md](phase-3.md)
> **Goal:** Anomaly detection, query explorer, backup integrity, threshold recommendations.

| Task | Status |
|------|--------|
| `collectors/anomaly.py` — Z-score based spike detection | [x] |
| Register anomaly collector every 15 min | [x] |
| `f-watcher-query-explorer` page | [x] |
| `query_stats()` endpoint — grouped slow queries | [x] |
| Gzip integrity check in `collectors/backups.py` | [x] |
| `recommend_thresholds()` API — P95 over 7 days | [x] |
| Alert Rule "Get Recommendations" button | [x] |
| `site` filter in `latest()` and `history()` | [x] |
| Site-selector dropdown in Control Center | [x] |
| `compare()` multi-site endpoint | [x] |
| Redis-based rate limiting in `api/logs.py` | [x] |
| Webhook URL validation in Alert Rule `validate()` | [x] |
| 3.8a — `cooldown_minutes` field on Alert Rule | [x] |
| 3.8b — Auto-resolve detection in alerting engine | [x] |
| 3.8c — `test_rule()` API + "Test now" button | [x] |
| 3.9a — Queue collector: dynamic queue names via `get_queue_names()` | [x] |
| 3.9b — DB storage: flag index bloat (`index_mb > data_mb * 1.5`) | [x] |

---

## Phase 4 — Operational Control & Automation
> Full spec: [phase-4.md](phase-4.md)
> **Goal:** Maintenance windows, auto-remediation, queue inspector, cache manager, custom cleanup rules.

| Task | Status |
|------|--------|
| `F Watcher Maintenance Window` DocType | [x] |
| `is_maintenance_active()` check in alerting engine | [x] |
| "Start maintenance" button + active banner in Control Center | [x] |
| `auto_remediate` + `remediation_action` fields on Alert Rule | [x] |
| `_run_remediation()` in alerting engine | [x] |
| `queue_jobs()` API endpoint — list/inspect jobs | [x] |
| Queue job inspector panel in Control Center | [x] |
| Per-job cancel + per-queue retry-all buttons | [x] |
| `api/cache.py` — `stats()` and `flush_cache()` | [x] |
| Cache card in Control Center right column | [x] |
| `F Watcher Cleanup Rule` DocType (custom rules) | [x] |
| Merge custom rules into `cleanup.py` | [x] |

---

## Phase 5 — Reporting & Analytics
> Full spec: [phase-5.md](phase-5.md)
> **Goal:** CSV export, uptime tracking, period comparison, error patterns, forecasting.

| Task | Status |
|------|--------|
| `api/export.py` — `system_metrics_csv()` | [x] |
| Export CSV buttons in Control Center | [x] |
| `F Watcher Uptime Record` DocType | [x] |
| `collectors/uptime.py` — every 5 min | [x] |
| `uptime_summary()` API + uptime % badge in header | [x] |
| `compare_periods()` endpoint — this vs prior period | [x] |
| Delta arrows (↑/↓) next to KPI values | [x] |
| `error_patterns()` API + Error Patterns table | [x] |
| `collectors/weekly_report.py` — Monday 08:00 | [x] |
| Register weekly report in `hooks.py` | [x] |
| `disk_forecast()` API + "full in ~N days" in disk KPI | [x] |

---

## Phase 6 — Security & Compliance
> Full spec: [phase-6.md](phase-6.md)
> **Goal:** IP brute force, session manager, API key monitor, permission audit, SSL dashboard.

| Task | Status |
|------|--------|
| IP-based brute force detection in `security.py` | [x] |
| Suspicious activity patterns (bulk delete, permission changes) | [x] |
| `api/sessions.py` — `list_sessions()` + `force_logout()` | [x] |
| Active Sessions card in Control Center | [x] |
| `collectors/api_keys.py` — stale + newly created keys | [x] |
| Register API key collector hourly in `hooks.py` | [x] |
| `permission_changes()` API + audit timeline | [x] |
| Always write SSL metric record (not only on alert) | [x] |
| SSL expiry KPI card in Control Center | [x] |

---

## Phase 7 — Developer Tools & Framework Health
> Full spec: [phase-7.md](phase-7.md)
> **Goal:** App versions, patch history, custom field audit, job inspector, scheduler timeline.

| Task | Status |
|------|--------|
| `api/apps.py` — `installed_apps()` with git info | [x] |
| Installed Apps card in Control Center | [x] |
| `patch_history()` API endpoint | [x] |
| Patch history section in Control Center | [x] |
| `api/customizations.py` — custom field/script audit | [x] |
| Customization Audit card in Control Center | [x] |
| `job_detail()` API — full traceback for failed jobs | [x] |
| `scheduler_timeline()` API | [x] |
| Scheduler timeline grid in Control Center | [x] |
| `slow_requests()` detail endpoint | [x] |
| Slow Requests section in DB Query Explorer | [x] |

---

## Summary

| Phase | Description | Tasks | Done | Left |
|-------|-------------|-------|------|------|
| Phase 1 | Stability & Correctness | 34 | 34 | 0 |
| Phase 2 | Visibility & Usability | 20 | 20 | 0 |
| Phase 3 | Intelligence & Advanced Monitoring | 17 | 17 | 0 |
| Phase 4 | Operational Control & Automation | 12 | 12 | 0 |
| Phase 5 | Reporting & Analytics | 11 | 11 | 0 |
| Phase 6 | Security & Compliance | 9 | 9 | 0 |
| Phase 7 | Developer Tools & Framework Health | 11 | 11 | 0 |
| **Total** | | **114** | **114** | **0** |

---

## Changelog

| Date | What |
|------|------|
| 2026-04-13 | Initial phase docs created (phase-1 to phase-3) |
| 2026-04-13 | BUG-01 to BUG-06: Fixed 6 core bugs (cleanup, dashboard, app_health) |
| 2026-04-13 | LV-01 to LV-08: Fixed 8 log viewer bugs |
| 2026-04-13 | Added Refresh button to Biggest Tables section |
| 2026-04-13 | Discovered BUG-07 to BUG-16 across alerting and collector files |
| 2026-04-13 | Added sections 1.5–1.7 (alerting bugs, collector bugs, LV summary) |
| 2026-04-13 | Added sections 2.6–2.7 (log viewer + control center enhancements) |
| 2026-04-13 | Added sections 3.8–3.9 (alerting intelligence + collector improvements) |
| 2026-04-13 | Created phase-4.md (Operational Control & Automation) |
| 2026-04-13 | Created phase-5.md (Reporting & Analytics) |
| 2026-04-13 | Created phase-6.md (Security & Compliance) |
| 2026-04-13 | Created phase-7.md (Developer Tools & Framework Health) |
| 2026-04-13 | BUG-07 to BUG-10: Fixed 4 alerting engine bugs (webhook, system notification, commit, metric types) |
| 2026-04-13 | BUG-11 to BUG-12: Fixed infrastructure.py (wrong DocType for Node.js memory, utcnow deprecated) |
| 2026-04-13 | BUG-13: Fixed database.py missing commit after slow query loop |
| 2026-04-13 | BUG-14: Fixed apm.py commit inside loop — moved to after loop |
| 2026-04-13 | BUG-15: Fixed backups.py — healthy backup state now recorded as App Metric |
| 2026-04-13 | BUG-16: Fixed security.py — sessions metric only inserted when count > 0 |
| 2026-04-18 | Phase 1 complete: roles/permissions, retention collector, full test suite |
| 2026-04-18 | Phase 2 complete: charts, health map, alert badge, log streaming, digest, queue panel |
| 2026-04-18 | Phase 3 complete: anomaly detection, query explorer, backup integrity, recommendations, multi-site, alerting intelligence |
| 2026-04-18 | Phase 4 complete: maintenance windows, auto-remediation, queue inspector, cache card, custom cleanup rules |
| 2026-04-19 | CI fix: patch is_maintenance_active + now_datetime in alerting/system tests; fix frappe.get_all mock target |
| 2026-04-19 | Phase 5 complete: CSV export, uptime tracking, period deltas, disk forecast, error patterns, weekly report |
| 2026-04-19 | Phase 6 complete: IP brute-force, suspicious activity, sessions API+card, API key collector, permission changes, SSL card |
