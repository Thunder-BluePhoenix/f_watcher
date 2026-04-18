import frappe
from frappe.utils import add_to_date


def send_weekly_report():
    since = add_to_date(None, days=-7)

    avg = frappe.db.sql("""
        SELECT AVG(cpu_percent) AS cpu, AVG(ram_percent) AS ram, AVG(disk_percent) AS disk
        FROM `tabF Watcher System Metric`
        WHERE `timestamp` >= %(since)s
    """, {"since": since}, as_dict=True)
    avg = avg[0] if avg else {}

    alert_count = frappe.db.count(
        "F Watcher Alert Log",
        {"creation": [">=", since], "status": "Triggered"},
    )

    failed_total = frappe.db.sql("""
        SELECT COALESCE(SUM(failed_count), 0)
        FROM `tabF Watcher Queue Metric`
        WHERE `timestamp` >= %(since)s
    """, {"since": since})[0][0] or 0

    errors = frappe.db.sql("""
        SELECT SUBSTRING(error, 1, 100) AS snippet, COUNT(*) AS cnt
        FROM `tabError Log`
        WHERE creation >= %(since)s
        GROUP BY SUBSTRING(error, 1, 100)
        ORDER BY cnt DESC
        LIMIT 5
    """, {"since": since}, as_dict=True)

    uptime_rows = frappe.db.sql("""
        SELECT status FROM `tabF Watcher Uptime Record`
        WHERE `timestamp` >= %(since)s
    """, {"since": since}, as_dict=True)
    total_checks = len(uptime_rows)
    up_checks = sum(1 for r in uptime_rows if r.status == "up")
    uptime_pct = f"{up_checks / total_checks * 100:.2f}%" if total_checks else "N/A"

    def fmt(val):
        return f"{float(val):.1f}%" if val is not None else "-"

    error_rows_html = "".join(
        f"<tr><td style='font-family:monospace;font-size:12px;'>"
        f"{frappe.utils.escape_html(r.snippet or '')}</td>"
        f"<td style='text-align:right;'>{r.cnt}</td></tr>"
        for r in errors
    ) or "<tr><td colspan='2' style='color:#666;'>No errors recorded.</td></tr>"

    body = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="border-bottom:2px solid #3b82f6;padding-bottom:8px;">
        F Watcher — Weekly Report
      </h2>
      <p style="color:#666;">Site: <b>{frappe.local.site}</b> &nbsp;·&nbsp; Last 7 days</p>

      <h3>System Averages</h3>
      <table border="1" cellpadding="6" cellspacing="0"
             style="border-collapse:collapse;width:100%;">
        <tr style="background:#f1f5f9;">
          <th>CPU avg</th><th>RAM avg</th><th>Disk avg</th><th>Uptime</th>
        </tr>
        <tr>
          <td>{fmt(avg.get('cpu'))}</td>
          <td>{fmt(avg.get('ram'))}</td>
          <td>{fmt(avg.get('disk'))}</td>
          <td>{uptime_pct}</td>
        </tr>
      </table>

      <h3>Alerts Triggered: {alert_count}</h3>
      <h3>Failed Background Jobs (total accumulated): {int(failed_total)}</h3>

      <h3>Top Error Patterns</h3>
      <table border="1" cellpadding="6" cellspacing="0"
             style="border-collapse:collapse;width:100%;">
        <tr style="background:#f1f5f9;">
          <th style="text-align:left;">Error snippet</th>
          <th style="text-align:right;">Count</th>
        </tr>
        {error_rows_html}
      </table>
    </div>
    """

    operators = frappe.db.sql("""
        SELECT DISTINCT parent FROM `tabHas Role`
        WHERE role IN ('F Watcher Operator', 'System Manager')
          AND parenttype = 'User'
    """, pluck="parent")

    if operators:
        frappe.sendmail(
            recipients=list(set(operators)),
            subject=f"F Watcher Weekly Report — {frappe.local.site}",
            message=body,
        )
