frappe.ui.form.on("F Watcher Alert Rule", {
    refresh(frm) {
        // 3.8c: Test now button
        frm.add_custom_button("Test Now", function() {
            frappe.call({
                method: "f_watcher.collectors.alerting.test_rule",
                args: { rule_name: frm.doc.name },
                callback(r) {
                    const res = r.message || {};
                    const indicator = res.status === "would_fire" ? "red" : "green";
                    frappe.msgprint({
                        title: res.status === "would_fire" ? "Would Fire" : "Would NOT Fire",
                        message: res.message || JSON.stringify(res),
                        indicator,
                    });
                },
            });
        }, "Actions");

        // 3.4: Get Recommendations button
        frm.add_custom_button("Get Threshold Recommendations", function() {
            frappe.call({
                method: "f_watcher.dashboards.metrics.recommend_thresholds",
                callback(r) {
                    const res = r.message || {};
                    if (res.status === "insufficient_data") {
                        frappe.msgprint({ title: "Not enough data", message: res.message, indicator: "yellow" });
                        return;
                    }
                    const rows = (res.recommendations || []).map(rec =>
                        `<tr>
                            <td>${rec.metric}</td>
                            <td><b>${rec.suggested_threshold}</b></td>
                            <td>${rec.note}</td>
                        </tr>`
                    ).join("");
                    frappe.msgprint({
                        title: "Threshold Recommendations (P95 over last 7 days)",
                        message: `<table class="table table-bordered" style="margin-top:8px;">
                            <thead><tr><th>Metric</th><th>Suggested Threshold</th><th>Note</th></tr></thead>
                            <tbody>${rows}</tbody>
                        </table>`,
                        indicator: "blue",
                    });
                },
            });
        }, "Actions");
    },
});
