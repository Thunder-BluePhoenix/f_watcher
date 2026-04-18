import os
import subprocess
import frappe
from frappe.utils import get_bench_path, add_to_date


def _check_permission():
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
        or "F Watcher Viewer" in frappe.get_roles()
    ):
        frappe.throw("Not permitted.", frappe.PermissionError)


def _git(app_dir, *args):
    try:
        return subprocess.run(
            ["git"] + list(args),
            cwd=app_dir, capture_output=True, text=True, timeout=3
        ).stdout.strip()
    except Exception:
        return None


@frappe.whitelist()
def installed_apps():
    _check_permission()
    bench_path = get_bench_path()
    apps_root = os.path.join(bench_path, "apps")

    result = []
    for app in frappe.get_installed_apps():
        info = {"name": app, "version": None, "branch": None, "commit": None, "commit_date": None}

        try:
            mod = frappe.get_module(app)
            info["version"] = getattr(mod, "__version__", None)
        except Exception:
            pass

        app_dir = os.path.join(apps_root, app)
        if os.path.isdir(os.path.join(app_dir, ".git")):
            info["branch"]      = _git(app_dir, "rev-parse", "--abbrev-ref", "HEAD")
            info["commit"]      = _git(app_dir, "rev-parse", "--short", "HEAD")
            raw_date            = _git(app_dir, "log", "-1", "--format=%ci")
            info["commit_date"] = raw_date[:10] if raw_date else None

        result.append(info)
    return result


@frappe.whitelist()
def patch_history(limit: int = 40):
    _check_permission()
    if not frappe.db.exists("DocType", "Patch Log"):
        return []
    return frappe.db.sql("""
        SELECT patch, creation
        FROM `tabPatch Log`
        ORDER BY creation DESC
        LIMIT %(limit)s
    """, {"limit": int(limit)}, as_dict=True)


@frappe.whitelist()
def slow_requests(hours: int = 24, limit: int = 50):
    _check_permission()
    if not frappe.db.exists("DocType", "Monitor"):
        return []
    since = add_to_date(None, hours=-int(hours))
    return frappe.db.sql("""
        SELECT path, request_method,
               MAX(duration)               AS max_duration_us,
               AVG(duration)               AS avg_duration_us,
               COUNT(*)                    AS count,
               MAX(creation)               AS last_seen
        FROM `tabMonitor`
        WHERE creation >= %(since)s
          AND duration > 500000
        GROUP BY path, request_method
        ORDER BY max_duration_us DESC
        LIMIT %(limit)s
    """, {"since": since, "limit": int(limit)}, as_dict=True)
