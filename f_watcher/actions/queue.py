import frappe
from rq import Queue
from frappe.utils.background_jobs import get_redis_conn

@frappe.whitelist(allow_guest=False)
def retry_failed_jobs(queue_name="default"):
    # Ensure current user is System Manager
    if not frappe.has_permission("F Watcher Queue Metric", "write"):
        frappe.throw("Not permitted", frappe.PermissionError)

    redis = get_redis_conn()
    q = Queue(queue_name, connection=redis)
    registry = q.failed_job_registry
    
    count = 0
    for job_id in registry.get_job_ids():
        registry.requeue(job_id)
        count += 1
        
    return {"status": "success", "message": f"Successfully requeued {count} jobs from the {queue_name} queue."}
