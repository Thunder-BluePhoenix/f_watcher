frappe.pages["f-watcher-query-explorer"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "DB Query Explorer",
        single_column: true,
    });

    const $body = $(page.body);

    if (!document.getElementById("fwqe-style")) {
        const s = document.createElement("style");
        s.id = "fwqe-style";
        s.innerHTML = `
        .fwqe-root { padding-bottom: 24px; }
        .fwqe-glass {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(15,23,42,0.08);
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 8px 32px rgba(2,6,23,0.07);
        }
        .fwqe-title { font-weight: 900; font-size: 15px; margin-bottom: 10px; }
        .fwqe-subtle { color: rgba(15,23,42,0.55); font-size: 12px; }
        .fwqe-badge {
            font-size: 11px; font-weight: 800;
            padding: 3px 9px; border-radius: 999px;
            background: rgba(59,130,246,0.10);
            border: 1px solid rgba(59,130,246,0.15);
            color: rgba(37,99,235,0.9);
        }
        .fwqe-btn {
            border-radius: 10px !important;
            font-weight: 800 !important;
        }
        .fwqe-filter-bar {
            display: flex; flex-wrap: wrap; gap: 10px;
            align-items: center; margin-bottom: 16px;
        }
        .fwqe-table td, .fwqe-table th {
            vertical-align: middle;
            border-color: rgba(15,23,42,0.08) !important;
            font-size: 13px;
        }
        .fwqe-table thead th {
            font-size: 12px; color: rgba(15,23,42,0.6);
            background: rgba(59,130,246,0.05);
        }
        .fwqe-table tbody tr:hover { background: rgba(59,130,246,0.04); cursor: pointer; }
        .fwqe-detail {
            background: #1e1e2e; color: #cdd6f4;
            font-family: monospace; font-size: 12px;
            padding: 12px; border-radius: 8px;
            white-space: pre-wrap; word-break: break-all;
            display: none; margin-top: 8px;
        }
        `;
        document.head.appendChild(s);
    }

    $body.addClass("fwqe-root");

    const $filters = $(`
        <div class="fwqe-glass fwqe-filter-bar" style="margin-bottom:12px;">
            <div>
                <label class="fwqe-subtle" style="margin-right:4px;">Time range</label>
                <select id="fwqe-hours" class="form-control" style="width:100px;display:inline-block;">
                    <option value="1">1 h</option>
                    <option value="6">6 h</option>
                    <option value="24" selected>24 h</option>
                    <option value="168">7 d</option>
                </select>
            </div>
            <div>
                <label class="fwqe-subtle" style="margin-right:4px;">Min executions</label>
                <input id="fwqe-min-exec" type="number" class="form-control" value="1"
                       min="1" style="width:80px;display:inline-block;">
            </div>
            <div>
                <label class="fwqe-subtle" style="margin-right:4px;">Sort by</label>
                <select id="fwqe-sort" class="form-control" style="width:130px;display:inline-block;">
                    <option value="worst">Worst time</option>
                    <option value="avg">Avg time</option>
                    <option value="count">Execution count</option>
                </select>
            </div>
            <button class="btn btn-primary btn-sm fwqe-btn" id="fwqe-search">Search</button>
            <span id="fwqe-status" class="fwqe-subtle"></span>
        </div>
    `).appendTo($body);

    const $results = $(`<div></div>`).appendTo($body);

    function sortRows(rows) {
        const by = $filters.find("#fwqe-sort").val();
        if (by === "avg")   return rows.slice().sort((a, b) => (b.avg_ms || 0) - (a.avg_ms || 0));
        if (by === "count") return rows.slice().sort((a, b) => (b.total_executions || 0) - (a.total_executions || 0));
        return rows.slice().sort((a, b) => (b.worst_ms || 0) - (a.worst_ms || 0));
    }

    function renderTable(rows) {
        if (!rows || !rows.length) {
            $results.html(`<div class="fwqe-glass fwqe-subtle" style="text-align:center;padding:24px;">No slow queries found for this time range.</div>`);
            return;
        }

        const sorted = sortRows(rows);
        const trs = sorted.map((r, idx) => `
            <tr data-idx="${idx}">
                <td><span class="fwqe-badge">${frappe.utils.escape_html(r.query_signature || '')}</span></td>
                <td style="text-align:right;font-weight:700;">${Math.round(r.worst_ms || 0)} ms</td>
                <td style="text-align:right;">${Math.round(r.avg_ms || 0)} ms</td>
                <td style="text-align:right;">${r.total_executions || 0}</td>
                <td>${r.last_seen ? frappe.datetime.prettyDate(r.last_seen) : '-'}</td>
            </tr>
            <tr data-detail="${idx}" style="display:none;">
                <td colspan="5">
                    <div class="fwqe-detail" id="fwqe-detail-${idx}">Query hash: ${frappe.utils.escape_html(r.query_signature || '')}
Worst: ${Math.round(r.worst_ms || 0)} ms  |  Avg: ${Math.round(r.avg_ms || 0)} ms  |  Executions: ${r.total_executions}
Last seen: ${r.last_seen || '-'}</div>
                </td>
            </tr>
        `).join('');

        $results.html(`
            <div class="fwqe-glass">
                <div class="fwqe-title">Slow Queries <span class="fwqe-subtle">(${sorted.length} found)</span></div>
                <div class="table-responsive">
                    <table class="table table-bordered fwqe-table">
                        <thead><tr>
                            <th>Query Hash</th>
                            <th style="text-align:right;">Worst (ms)</th>
                            <th style="text-align:right;">Avg (ms)</th>
                            <th style="text-align:right;">Executions</th>
                            <th>Last Seen</th>
                        </tr></thead>
                        <tbody>${trs}</tbody>
                    </table>
                </div>
            </div>
        `);

        // Expand row on click
        $results.find("tbody tr[data-idx]").on("click", function() {
            const idx = $(this).data("idx");
            const $detail = $results.find(`tr[data-detail="${idx}"]`);
            const $box    = $results.find(`#fwqe-detail-${idx}`);
            if ($detail.is(":visible")) {
                $detail.hide();
                $box.hide();
            } else {
                $detail.show();
                $box.show();
            }
        });
    }

    function fetchStats() {
        const $btn = $filters.find("#fwqe-search");
        $btn.prop("disabled", true).text("Loading…");
        $filters.find("#fwqe-status").text("");

        frappe.call({
            method: "f_watcher.dashboards.metrics.query_stats",
            args: {
                hours: parseInt($filters.find("#fwqe-hours").val()),
                min_executions: parseInt($filters.find("#fwqe-min-exec").val()) || 1,
                limit: 50,
            },
            callback(r) {
                $btn.prop("disabled", false).text("Search");
                const rows = r.message || [];
                $filters.find("#fwqe-status").text(`${rows.length} queries`);
                renderTable(rows);
            },
            error() {
                $btn.prop("disabled", false).text("Search");
                $filters.find("#fwqe-status").text("Failed to load. Check server logs.");
            },
        });
    }

    $filters.find("#fwqe-search").on("click", fetchStats);

    // Slow HTTP Requests section (from tabMonitor)
    const $slowReqs = $(`<div style="margin-top:20px;"></div>`).appendTo($body);

    function renderSlowRequests(rows) {
        if (!rows || !rows.length) {
            $slowReqs.html(`
                <div class="fwqe-glass fwqe-subtle" style="text-align:center;padding:16px;">
                    No slow HTTP requests found in the last 24 hours.
                </div>
            `);
            return;
        }
        const trs = rows.map(r => {
            const maxMs = (r.max_duration_us / 1000).toFixed(0);
            const avgMs = (r.avg_duration_us / 1000).toFixed(0);
            return `
                <tr>
                    <td style="word-break:break-all;max-width:340px;">${frappe.utils.escape_html(r.path || "")}</td>
                    <td>${frappe.utils.escape_html(r.request_method || "")}</td>
                    <td style="text-align:right;">${maxMs}</td>
                    <td style="text-align:right;">${avgMs}</td>
                    <td style="text-align:right;">${r.count}</td>
                    <td class="fwqe-subtle">${(r.last_seen || "").slice(0, 16)}</td>
                </tr>`;
        }).join("");
        $slowReqs.html(`
            <div class="fwqe-glass">
                <div class="fwqe-title">Slow HTTP Requests <span class="fwqe-subtle">(last 24 h, &gt;500 ms)</span></div>
                <table class="table fwqe-table" style="margin:0;">
                    <thead><tr>
                        <th>Path</th><th>Method</th>
                        <th style="text-align:right;">Worst (ms)</th>
                        <th style="text-align:right;">Avg (ms)</th>
                        <th style="text-align:right;">Count</th>
                        <th>Last Seen</th>
                    </tr></thead>
                    <tbody>${trs}</tbody>
                </table>
            </div>
        `);
    }

    frappe.call({
        method: "f_watcher.api.apps.slow_requests",
        args: { hours: 24, limit: 50 },
        callback(r) { renderSlowRequests(r.message || []); },
        error() { $slowReqs.html(""); },
    });

    // Initial load
    fetchStats();
};
