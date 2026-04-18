import frappe
from frappe.utils.background_jobs import get_redis_conn
from frappe.utils import now_datetime, get_datetime


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
        import redis as redis_lib
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

    # Scheduler — last completed job within 6 minutes
    try:
        last = frappe.db.get_value(
            "Scheduled Job Log", {"status": "Complete"}, "creation", order_by="creation desc"
        )
        if last and (now_datetime() - get_datetime(last)).total_seconds() < 360:
            results["scheduler"] = {"status": "ok", "last_run": str(last)}
        else:
            results["scheduler"] = {"status": "warn", "detail": "No job completed in the last 6 min"}
    except Exception as e:
        results["scheduler"] = {"status": "error", "detail": str(e)}

    # Workers — active RQ workers
    try:
        from rq import Worker
        workers = Worker.all(connection=get_redis_conn())
        results["workers"] = {
            "status": "ok" if workers else "warn",
            "count": len(workers),
        }
    except Exception as e:
        results["workers"] = {"status": "error", "detail": str(e)}

    return results
