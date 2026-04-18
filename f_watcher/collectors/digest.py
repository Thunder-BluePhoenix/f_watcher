import frappe
from frappe.utils import now_datetime, add_to_date


def send_daily_digest():
    since = add_to_date(None, days=-1)

    avg_row = frappe.db.sql("""
        SELECT
            AVG(cpu_percent)  AS cpu,
            MAX(cpu_percent)  AS max_cpu,
            AVG(ram_percent)  AS ram,
            MAX(disk_percent) AS disk
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %(since)s
    """, {"since": since}, as_dict=True)
    avg = avg_row[0] if avg_row else {}

    alerts = frappe.db.count("F Watcher Alert Log", {"status": "Triggered", "timestamp": [">=", since]})

    failed_jobs = frappe.db.sql("""
        SELECT SUM(failed_count)
        FROM `tabF Watcher Queue Metric`
        WHERE `timestamp` >= %(since)s
    """, {"since": since})[0][0] or 0

    recipients = frappe.get_all(
        "Has Role",
        filters={"role": "F Watcher Operator"},
        fields=["parent"],
        pluck="parent",
    )
    if not recipients:
        return

    cpu = avg.get("cpu") or 0
    max_cpu = avg.get("max_cpu") or 0
    ram = avg.get("ram") or 0
    disk = avg.get("disk") or 0

    subject = f"[F Watcher] Daily Health Digest — {now_datetime().strftime('%Y-%m-%d')}"
    message = f"""
    <h3>System Summary (last 24h)</h3>
    <ul>
      <li>CPU avg: {cpu:.1f}% | peak: {max_cpu:.1f}%</li>
      <li>RAM avg: {ram:.1f}%</li>
      <li>Disk peak: {disk:.1f}%</li>
      <li>Alerts triggered: {alerts}</li>
      <li>Failed queue jobs: {int(failed_jobs)}</li>
    </ul>
    <p style="color:#888;font-size:12px;">Sent by F Watcher · {frappe.local.site}</p>
    """

    frappe.sendmail(recipients=recipients, subject=subject, message=message)
