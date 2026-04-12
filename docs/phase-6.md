# Phase 6 — Security & Compliance

> Goal: Harden the site's security posture through deep monitoring,
> active threat detection, and a full compliance audit trail.
> F Watcher should be the first place you look after a security incident.

---

## 6.1 IP-Based Brute Force Detection

**Problem:** `security.py` currently tracks failed logins per *user* but not per *IP address*.
An attacker trying many different usernames from the same IP will not be detected.

**What to do:**

Update `collectors/security.py` — query the `communication_medium` or `ip_address` column
in `tabActivity Log` (Frappe stores the IP there on newer versions):

```python
def track_brute_force_by_ip():
    fifteen_mins_ago = add_to_date(now_datetime(), minutes=-15)
    anomalies = frappe.db.sql("""
        SELECT ip_address, COUNT(name) AS attempts
        FROM `tabActivity Log`
        WHERE subject = 'Failed Login'
          AND creation >= %(since)s
          AND ip_address IS NOT NULL
          AND ip_address != ''
        GROUP BY ip_address
        HAVING attempts > 10
    """, {"since": fifteen_mins_ago}, as_dict=True)

    for row in anomalies:
        msg = (f"Brute force detected: {row.attempts} failed login attempts "
               f"from IP {row.ip_address} in the last 15 minutes.")
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": msg,
            "metric_value": f"{row.ip_address} ({row.attempts} attempts)",
        }).insert(ignore_permissions=True)
    frappe.db.commit()
```

---

## 6.2 Suspicious Activity Detector

**Problem:** Beyond failed logins, many other suspicious patterns go unmonitored:
bulk document deletes, mass exports, role changes, API key creation at odd hours.

**What to do:**

Add to `collectors/security.py`:

```python
SUSPICIOUS_PATTERNS = [
    {
        "label": "Bulk delete",
        "doctype": "Activity Log",
        "filter": {"operation": "Delete"},
        "threshold": 50,   # >50 deletes in 15 min by one user
        "group_by": "user",
    },
    {
        "label": "Permission change",
        "doctype": "Activity Log",
        "filter": {"reference_doctype": ["in", ["User", "Role", "Has Role", "User Permission"]]},
        "threshold": 5,
        "group_by": "user",
    },
]

def track_suspicious_activity():
    fifteen_mins_ago = add_to_date(now_datetime(), minutes=-15)
    for pattern in SUSPICIOUS_PATTERNS:
        results = frappe.db.sql("""
            SELECT `{group}`, COUNT(name) AS cnt
            FROM `tabActivity Log`
            WHERE operation = %(op)s AND creation >= %(since)s
            GROUP BY `{group}`
            HAVING cnt > %(threshold)s
        """.format(group=pattern["group_by"]),
        {"op": pattern["filter"].get("operation",""), "since": fifteen_mins_ago,
         "threshold": pattern["threshold"]}, as_dict=True)
        for r in results:
            _log_security_event(pattern["label"], r)
```

---

## 6.3 Active Session Manager

**Problem:** Admins can see how many sessions are active (from `security.py`) but cannot
see *who* is logged in or force-logout a specific suspicious user from F Watcher.

**What to do:**

Create `api/sessions.py`:
```python
@frappe.whitelist()
def list_sessions():
    _check_permission()
    return frappe.db.sql("""
        SELECT user, device, ip_address, last_active, sid
        FROM `tabSessions`
        WHERE user != 'Guest'
        ORDER BY last_active DESC
        LIMIT 100
    """, as_dict=True)

@frappe.whitelist()
def force_logout(sid: str):
    _check_permission()
    session = frappe.db.get_value("Sessions", sid, ["user", "sid"], as_dict=True)
    if not session:
        frappe.throw("Session not found.")
    frappe.db.delete("Sessions", {"sid": sid})
    frappe.db.commit()
    _audit("force_logout", session.user, f"Force logout session {sid}", "Success", "")
    return {"status": "ok", "user": session.user}
```

Add an "Active Sessions" card to the Control Center showing users, IPs, last active time,
and a "Force logout" button per session.

---

## 6.4 API Key & Token Monitor

**Problem:** API keys and access tokens created in Frappe are permanent until manually
revoked. There is no monitoring for unused, old, or newly-created keys.

**What to do:**

Create `collectors/api_keys.py`:
```python
def collect():
    # Flag API keys unused for > 90 days
    ninety_days_ago = add_to_date(now_datetime(), days=-90)
    stale_keys = frappe.db.sql("""
        SELECT ak.api_key, ak.parent AS user, ak.creation
        FROM `tabUser API Key` ak
        WHERE ak.creation < %(cutoff)s
    """, {"cutoff": ninety_days_ago}, as_dict=True)

    for key in stale_keys:
        frappe.get_doc({
            "doctype": "F Watcher Alert Log",
            "timestamp": now_datetime(),
            "status": "Triggered",
            "message": f"Stale API key: user {key.user} has an API key created "
                       f"{key.creation} with no recorded recent usage.",
            "metric_value": "Stale API Key",
        }).insert(ignore_permissions=True)

    # Flag newly created keys (created in last 1 hour — needs human review)
    one_hour_ago = add_to_date(now_datetime(), hours=-1)
    new_keys = frappe.db.count("User API Key", {"creation": [">=", one_hour_ago]})
    if new_keys:
        frappe.get_doc({
            "doctype": "F Watcher App Metric",
            "timestamp": now_datetime(),
            "metric_type": "Security",
            "count": new_keys,
            "details": f"{new_keys} new API key(s) created in the last hour.",
        }).insert(ignore_permissions=True)

    frappe.db.commit()
```

Register hourly in `hooks.py`.

---

## 6.5 Permission Change Audit Trail

**Problem:** Frappe's Activity Log tracks document saves but does not specifically surface
role/permission changes in a readable format. If someone gains System Manager access, it
can be hard to find in the audit trail.

**What to do:**

Create a `permission_changes()` API endpoint:
```python
@frappe.whitelist()
def permission_changes(days: int = 30):
    since = frappe.utils.add_to_date(None, days=-int(days))
    return frappe.db.sql("""
        SELECT creation, owner AS changed_by, reference_doctype, reference_name, subject
        FROM `tabActivity Log`
        WHERE reference_doctype IN ('User', 'Role', 'Has Role', 'User Permission',
                                    'Role Profile', 'Module Profile')
          AND creation >= %(since)s
        ORDER BY creation DESC
        LIMIT 200
    """, {"since": since}, as_dict=True)
```

Add a "Permission Changes" tab or section in the Control Center Audit area showing this
timeline. Highlight any changes to System Manager, Administrator, or F Watcher Operator roles.

---

## 6.6 SSL Certificate Dashboard

**Problem:** `infrastructure.py` already checks SSL expiry and fires an alert at <14 days.
But there is no visible SSL status on the dashboard — you only learn about it when the alert
fires. By then it may be too late.

**What to do:**

Extend `infrastructure.py` to always write an `F Watcher App Metric` record:
```python
frappe.get_doc({
    "doctype": "F Watcher App Metric",
    "timestamp": now_datetime(),
    "metric_type": "SSL",
    "count": days_left,
    "details": f"SSL certificate for {domain} expires in {days_left} days",
}).insert(ignore_permissions=True)
```

Show SSL expiry as a KPI card in the Control Center: green (>30 days), yellow (14–30),
red (<14), with the exact expiry date as a tooltip.

---

## Checklist

- [ ] 6.1 — IP-based brute force detection in `collectors/security.py`
- [ ] 6.2 — Suspicious activity patterns (bulk delete, permission changes)
- [ ] 6.3 — Create `api/sessions.py` with `list_sessions()` + `force_logout()`
- [ ] 6.3 — Add Active Sessions card to Control Center
- [ ] 6.4 — Create `collectors/api_keys.py` (stale + newly created API keys)
- [ ] 6.4 — Register API key collector hourly in `hooks.py`
- [ ] 6.5 — Create `permission_changes()` API + audit timeline in Control Center
- [ ] 6.6 — Always write SSL metric record (not only on alert)
- [ ] 6.6 — Add SSL expiry KPI card to Control Center
