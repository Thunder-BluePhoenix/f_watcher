import frappe
from rq import Queue
from frappe.utils.background_jobs import get_redis_conn


def _check_permission():
    if not frappe.has_permission("F Watcher Queue Metric", "write"):
        frappe.throw("Not permitted", frappe.PermissionError)


@frappe.whitelist(allow_guest=False)
def retry_failed_jobs(queue_name="default"):
    _check_permission()
    redis = get_redis_conn()
    q = Queue(queue_name, connection=redis)
    count = 0
    for job_id in q.failed_job_registry.get_job_ids():
        q.failed_job_registry.requeue(job_id)
        count += 1
    return {"status": "success", "message": f"Requeued {count} jobs from '{queue_name}'."}


@frappe.whitelist(allow_guest=False)
def queue_jobs(queue_name="default", status="queued", limit=50):
    _check_permission()
    redis = get_redis_conn()
    q = Queue(queue_name, connection=redis)

    if status == "failed":
        job_ids = q.failed_job_registry.get_job_ids()[:int(limit)]
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
                    "enqueued_at": str(job.enqueued_at or ""),
                    "status": str(job.get_status()),
                    "description": job.description or "",
                })
        except Exception:
            pass
    return jobs


@frappe.whitelist(allow_guest=False)
def cancel_job(queue_name="default", job_id=None):
    _check_permission()
    if not job_id:
        frappe.throw("job_id is required")
    redis = get_redis_conn()
    q = Queue(queue_name, connection=redis)
    try:
        job = q.fetch_job(job_id)
        if job:
            job.cancel()
            return {"status": "cancelled"}
        # try failed registry
        q.failed_job_registry.remove(job_id, delete_job=True)
        return {"status": "removed"}
    except Exception as e:
        frappe.throw(f"Could not cancel job: {e}")


@frappe.whitelist(allow_guest=False)
def job_detail(queue_name="default", job_id=None):
    _check_permission()
    if not job_id:
        frappe.throw("job_id is required")
    redis = get_redis_conn()
    q = Queue(queue_name, connection=redis)
    try:
        job = q.fetch_job(job_id)
        if not job:
            from rq.job import Job as RQJob
            job = RQJob.fetch(job_id, connection=redis)
        if not job:
            frappe.throw("Job not found")
        return {
            "id": job.id,
            "func": job.func_name,
            "status": str(job.get_status()),
            "enqueued_at": str(job.enqueued_at or ""),
            "ended_at": str(getattr(job, "ended_at", None) or ""),
            "exc_info": job.exc_info or "",
            "description": job.description or "",
        }
    except Exception as e:
        frappe.throw(f"Could not fetch job detail: {e}")


@frappe.whitelist(allow_guest=False)
def scheduler_timeline(hours: int = 24):
    if not frappe.has_permission("F Watcher Queue Metric", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    if not frappe.db.exists("DocType", "Scheduled Job Log"):
        return []
    since = frappe.utils.add_to_date(None, hours=-int(hours))
    return frappe.db.sql("""
        SELECT scheduled_job_type, status, details, creation
        FROM `tabScheduled Job Log`
        WHERE creation >= %(since)s
        ORDER BY creation DESC
        LIMIT 100
    """, {"since": since}, as_dict=True)
