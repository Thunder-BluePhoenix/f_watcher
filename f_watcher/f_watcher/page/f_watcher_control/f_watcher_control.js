// apps/f_watcher/f_watcher/page/f_watcher_control/f_watcher_control.js
// Premium tooltips (custom, readable) + DB size guidance (bands + status + directions)

frappe.pages["f_watcher-control"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "F Watcher Control Center",
    single_column: true,
  });

  const $body = $(page.body);

  $(wrapper).find(".page-head").css({
    background:
      "linear-gradient(90deg, rgba(59,130,246,0.12), rgba(16,185,129,0.10), rgba(245,158,11,0.10))",
    borderBottom: "1px solid rgba(15,23,42,0.08)",
  });
  $(wrapper).find(".page-title .title-text").css({
    fontWeight: 950,
    letterSpacing: "-0.02em",
  });


  $body.addClass("f_watcher-root");

  // -----------------------------
  // Premium UI styles
  // -----------------------------
  if (!document.getElementById("f_watcher-style")) {
    const style = document.createElement("style");
    style.id = "f_watcher-style";


    style.innerHTML = `
    .f_watcher-root{
      padding-bottom: 24px;
      /* soft “control center” background */
      background:
        radial-gradient(900px 420px at 12% 0%, rgba(59,130,246,0.10), transparent 55%),
        radial-gradient(820px 420px at 88% 8%, rgba(16,185,129,0.10), transparent 55%),
        radial-gradient(700px 380px at 60% 92%, rgba(245,158,11,0.10), transparent 55%),
        linear-gradient(180deg, rgba(255,255,255,1), rgba(248,250,252,1));
    }

    /* ===== Theme tokens ===== */
    :root{
      --upeo-blue: #3b82f6;
      --upeo-green:#10b981;
      --upeo-amber:#f59e0b;
      --upeo-violet:#6366f1;
      --upeo-red:  #ef4444;

      --upeo-ink: #0f172a;
      --upeo-muted: rgba(15,23,42,0.62);
    }

    .upeo-glass{
      background: rgba(255,255,255,0.74);
      border: 1px solid rgba(15,23,42,0.08);
      border-radius: 18px;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      box-shadow:
        0 18px 48px rgba(2,6,23,0.08),
        0 1px 0 rgba(255,255,255,0.55) inset;
    }

    .upeo-section{ position: relative; overflow: hidden; }
    .upeo-section:before{
      content:"";
      position:absolute;
      inset:0;
      opacity: 0.70;
      pointer-events:none;
      background:
        radial-gradient(circle at 20% 10%, rgba(15,23,42,0.05), transparent 60%),
        radial-gradient(circle at 90% 20%, rgba(59,130,246,0.06), transparent 58%);
    }

    /* ===== Accents: now actually colorful ===== */
    .upeo-accent{ height: 4px; border-radius: 999px; margin-bottom: 12px; }
    .upeo-accent.health{
      background: linear-gradient(90deg, rgba(16,185,129,0.95), rgba(59,130,246,0.85));
    }
    .upeo-accent.tables{
      background: linear-gradient(90deg, rgba(59,130,246,0.95), rgba(99,102,241,0.85));
    }
    .upeo-accent.actions{
      background: linear-gradient(90deg, rgba(245,158,11,0.95), rgba(239,68,68,0.80));
    }
    .upeo-accent.audit{
      background: linear-gradient(90deg, rgba(99,102,241,0.95), rgba(16,185,129,0.80));
    }

    .upeo-fade-in{ animation: upeoFade .22s ease-out; }
    @keyframes upeoFade{ from{opacity:.55; transform:translateY(8px)} to{opacity:1; transform:translateY(0)} }

    .upeo-header{ display:flex; align-items:flex-start; justify-content:space-between; gap: 12px; margin-bottom: 12px; }
    .upeo-title{ font-weight: 900; font-size: 16px; color: var(--upeo-ink); }
    .upeo-subtle{ color: var(--upeo-muted); font-size:12px; line-height: 1.35; }

    /* KPI more “hero” */
    .upeo-kpi{
      font-size: 24px;
      font-weight: 950;
      line-height: 1.0;
      letter-spacing: -0.03em;
      color: var(--upeo-ink);
    }
    .upeo-kpi-label{
      font-size: 12px;
      color: var(--upeo-muted);
      margin-top: 6px;
      display:flex;
      align-items:center;
      gap:8px;
    }

    /* Pills: subtle tint + clearer hierarchy */
    .upeo-pill{
      display:inline-flex; align-items:center; gap:8px;
      padding: 6px 10px;
      border-radius: 999px;
      font-weight: 850;
      font-size: 12px;
      border: 1px solid rgba(15,23,42,0.08);
      background: rgba(255,255,255,0.65);
    }

    .upeo-dot{ width:10px; height:10px; border-radius:999px; display:inline-block; }
    .upeo-dot.green{ background: var(--upeo-green); box-shadow: 0 0 0 4px rgba(16,185,129,0.14); }
    .upeo-dot.yellow{ background: var(--upeo-amber); box-shadow: 0 0 0 4px rgba(245,158,11,0.14); }
    .upeo-dot.red{ background: var(--upeo-red); box-shadow: 0 0 0 4px rgba(239,68,68,0.14); }

    .upeo-skeleton{
      background: linear-gradient(90deg, rgba(15,23,42,0.04), rgba(15,23,42,0.09), rgba(15,23,42,0.04));
      background-size: 200% 100%;
      animation: upeoShimmer 1.15s infinite;
      border-radius: 12px;
    }
    @keyframes upeoShimmer{ 0%{background-position:200% 0} 100%{background-position:-200% 0} }

    .upeo-card-pad{ padding: 16px; }
    .upeo-divider{ height:1px; background: rgba(15,23,42,0.08); margin: 12px 0; }

    /* Tables: cleaner header + hover */
    .upeo-table{
      border-color: rgba(15,23,42,0.10) !important;
    }
    .upeo-table thead th{
      font-size: 12px;
      color: rgba(15,23,42,0.65);
      background:
        linear-gradient(180deg, rgba(59,130,246,0.06), rgba(99,102,241,0.03));
      border-color: rgba(15,23,42,0.10) !important;
    }
    .upeo-table td{
      vertical-align: top;
      border-color: rgba(15,23,42,0.08) !important;
    }
    .upeo-table tbody tr:hover{
      background: rgba(59,130,246,0.045);
    }

    /* Buttons: premium but readable */
    .upeo-btn{
      border-radius: 12px !important;
      font-weight: 850 !important;
      border: 1px solid rgba(15,23,42,0.10) !important;
      box-shadow: 0 10px 22px rgba(2,6,23,0.08);
      transition: transform .12s ease, box-shadow .12s ease;
    }
    .upeo-btn:hover{
      transform: translateY(-1px);
      box-shadow: 0 14px 30px rgba(2,6,23,0.10);
    }

    /* Primary buttons: gradient */
    .btn.btn-primary.upeo-btn{
      background: linear-gradient(90deg, rgba(59,130,246,1), rgba(99,102,241,1)) !important;
      color: #fff !important;
    }

    /* Warning (cleanup) button: amber gradient */
    .btn.btn-warning.upeo-btn{
      background: linear-gradient(90deg, rgba(245,158,11,1), rgba(239,68,68,0.95)) !important;
      color: #111827 !important;
    }

    .upeo-badge{
      font-size: 11px;
      font-weight: 900;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(15,23,42,0.05);
      border: 1px solid rgba(15,23,42,0.08);
      color: rgba(15,23,42,0.75);
    }
    .upeo-muted{ color: var(--upeo-muted); }

    .upeo-toast{ display:none; position: sticky; top: 0; z-index: 5; margin-bottom: 12px; }

    /* ===== Tooltips: keep your premium tooltip, just polish text tone ===== */
    .upeo-tip-btn{
      width: 18px; height: 18px; border-radius: 999px;
      display:inline-flex; align-items:center; justify-content:center;
      background: rgba(59,130,246,0.10);
      border: 1px solid rgba(59,130,246,0.14);
      color: rgba(37,99,235,0.85);
      font-size: 12px;
      cursor: pointer;
      user-select: none;
      transition: transform .12s ease, background .12s ease;
    }
    .upeo-tip-btn:hover{
      transform: translateY(-1px);
      background: rgba(59,130,246,0.14);
    }

    .upeo-tooltip{
      position: fixed;
      z-index: 9999;
      width: min(360px, calc(100vw - 24px));
      padding: 12px 12px;
      border-radius: 14px;
      background: rgba(15,23,42,0.90);
      color: rgba(255,255,255,0.94);
      border: 1px solid rgba(255,255,255,0.10);
      box-shadow: 0 18px 60px rgba(0,0,0,0.30);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      display: none;
      animation: upeoTipIn .14s ease-out;
    }
    @keyframes upeoTipIn{ from{opacity:0; transform: translateY(6px)} to{opacity:1; transform: translateY(0)} }

    .upeo-tip-title{ font-weight: 900; font-size: 13px; margin-bottom: 6px; }
    .upeo-tip-text{ font-size: 12px; line-height: 1.35; color: rgba(255,255,255,0.88); }
    .upeo-tip-bands{ margin-top: 8px; display:flex; flex-direction: column; gap: 6px; }
    .upeo-tip-band{ display:flex; align-items:flex-start; gap: 8px; }
    .upeo-tip-tag{
      font-size: 11px; font-weight: 950;
      padding: 2px 8px; border-radius: 999px;
      background: rgba(59,130,246,0.22);
      border: 1px solid rgba(59,130,246,0.28);
      white-space: nowrap;
      margin-top: 1px;
    }
    .upeo-tip-actions{
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid rgba(255,255,255,0.10);
    }
    .upeo-tip-actions b{ color: rgba(255,255,255,0.95); }

    .upeo-tip-close{
      position:absolute; top: 10px; right: 10px;
      width: 22px; height: 22px; border-radius: 999px;
      display:inline-flex; align-items:center; justify-content:center;
      background: rgba(255,255,255,0.10);
      cursor:pointer;
      font-size: 12px;
      color: rgba(255,255,255,0.9);
    }
  `;



    document.head.appendChild(style);
  }

  // Layout containers
  const $toast           = $(`<div class="upeo-toast"></div>`).appendTo($body);
  const $maintenance     = $(`<div style="margin-bottom:8px;"></div>`).appendTo($body);
  const $health          = $(`<div></div>`).appendTo($body);
  const $healthMap       = $(`<div style="margin-top:12px;"></div>`).appendTo($body);
  const $charts          = $(`<div style="margin-top:12px;"></div>`).appendTo($body);
  const $row             = $(`<div class="row" style="margin-top:12px;"></div>`).appendTo($body);
  const $left            = $(`<div class="col-md-8"></div>`).appendTo($row);
  const $right           = $(`<div class="col-md-4"></div>`).appendTo($row);
  const $alertRulesPanel = $(`<div style="margin-top:12px;"></div>`).appendTo($body);
  const $queuesPanel     = $(`<div style="margin-top:12px;"></div>`).appendTo($body);
  const $audit           = $(`<div style="margin-top:12px;"></div>`).appendTo($body);
  const $errorPatterns   = $(`<div style="margin-top:12px;"></div>`).appendTo($body);

  // One premium tooltip element reused for all tips
  let $tip = $("#upeo-tooltip");
  if (!$tip.length) {
    $tip = $(`
      <div id="upeo-tooltip" class="upeo-tooltip" role="dialog" aria-live="polite">
        <div class="upeo-tip-close" title="Close">✕</div>
        <div class="upeo-tip-title"></div>
        <div class="upeo-tip-text"></div>
        <div class="upeo-tip-bands"></div>
        <div class="upeo-tip-actions"></div>
      </div>
    `).appendTo(document.body);

    $tip.find(".upeo-tip-close").on("click", () => hideTip());
    $(document).on("keydown", (e) => { if (e.key === "Escape") hideTip(); });
    $(document).on("click", (e) => {
      // close if click outside tooltip and outside a tip button
      const isInside = $(e.target).closest("#upeo-tooltip").length;
      const isBtn = $(e.target).closest("[data-upeo-tip]").length;
      if (!isInside && !isBtn) hideTip();
    });
  }

  function showTip(anchorEl, payload) {
    const rect = anchorEl.getBoundingClientRect();
    const pad = 10;

    $tip.find(".upeo-tip-title").text(payload.title || "");
    $tip.find(".upeo-tip-text").text(payload.text || "");

    const $bands = $tip.find(".upeo-tip-bands").empty();
    (payload.bands || []).forEach((b) => {
      $bands.append(`
        <div class="upeo-tip-band">
          <span class="upeo-tip-tag">${b.tag}</span>
          <div class="upeo-tip-text">${frappe.utils.escape_html(b.desc)}</div>
        </div>
      `);
    });

    const $actions = $tip.find(".upeo-tip-actions").empty();
    if (payload.actions && payload.actions.length) {
      $actions.append(`<div class="upeo-tip-title" style="margin-bottom:6px;">What to do</div>`);
      $actions.append(`<div class="upeo-tip-text"><b>Directions:</b> ${frappe.utils.escape_html(payload.actions.join(" · "))}</div>`);
    }

    // Position (prefer below; flip above if needed)
    $tip.show();
    const tipRect = $tip[0].getBoundingClientRect();

    let top = rect.bottom + pad;
    if (top + tipRect.height > window.innerHeight - 10) {
      top = rect.top - tipRect.height - pad;
    }
    let left = rect.left;
    if (left + tipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tipRect.width - 10;
    }
    if (left < 10) left = 10;

    $tip.css({ top: `${top}px`, left: `${left}px` });
  }

  function hideTip() {
    $tip.hide();
  }

  function wirePremiumTooltips() {
    $("[data-upeo-tip]").off("click").on("click", function (e) {
      e.preventDefault();
      const payload = $(this).data("upeoTipPayload");
      if (!payload) return;
      // toggle
      if ($tip.is(":visible")) {
        hideTip();
      } else {
        showTip(this, payload);
      }
    });
  }

  // -----------------------------
  // Helpers
  // -----------------------------

  function formatDbSize(totalMb) {
	const n = Number(totalMb);
	if (Number.isNaN(n)) return "-";
	if (n < 1024) return `${n.toFixed(0)} MB`;
	return `${(n / 1024).toFixed(1)} GB`;
   }


  function prettyTime(dt) {
    if (!dt) return "-";
    try { return frappe.datetime.prettyDate(dt); } catch (e) { return dt; }
  }

  function mb(x) {
    if (x == null) return "-";
    const n = Number(x);
    if (Number.isNaN(n)) return "-";
    return `${n.toFixed(1)} MB`;
  }

  function gbFromMb(mbVal) {
    const n = Number(mbVal);
    if (Number.isNaN(n)) return null;
    return n / 1024.0;
  }

  function clampPct(x) {
    const n = Number(x);
    if (Number.isNaN(n)) return null;
    return Math.max(0, Math.min(100, n));
  }

  function deltaArrow(val) {
    if (val == null) return "";
    const n = Number(val);
    if (Number.isNaN(n) || n === 0) return "";
    const up = n > 0;
    const color = up ? "#ef4444" : "#10b981";
    return ` <span style="font-size:13px;color:${color};font-weight:700;">${up ? "↑" : "↓"}${Math.abs(n).toFixed(1)}</span>`;
  }

  function healthLevel(sys) {
    if (!sys) return { level: "yellow", title: "No data yet", msg: "Metrics are still loading." };

    const cpu = clampPct(sys.cpu_percent);
    const ram = clampPct(sys.ram_percent);
    const disk = clampPct(sys.disk_percent);

    if ((cpu != null && cpu > 85) || (ram != null && ram > 90) || (disk != null && disk > 92)) {
      return { level: "red", title: "High stress", msg: "Users may feel slowness or timeouts. Consider action." };
    }
    if ((cpu != null && cpu > 65) || (ram != null && ram > 80) || (disk != null && disk > 88)) {
      return { level: "yellow", title: "Moderate stress", msg: "System is working harder than usual. Monitor trends." };
    }
    return { level: "green", title: "Healthy", msg: "System looks stable. No action needed." };
  }

  function advice(sys) {
    if (!sys) return "Action: None.";
    const cpu = clampPct(sys.cpu_percent);
    const ram = clampPct(sys.ram_percent);
    const disk = clampPct(sys.disk_percent);

    if (disk != null && disk > 92) return "Action: Free disk space or increase disk size soon.";
    if (ram != null && ram > 85) return "Action: Reduce heavy reports/jobs or increase server RAM.";
    if (cpu != null && cpu > 85) return "Action: Check slow reports, stuck jobs, and database pressure.";
    return "Action: None needed.";
  }

  // Database size guidance (rule-of-thumb, works for most ERPNext installs)
  function dbGuidance(totalMb) {
    const gb = gbFromMb(totalMb);
    if (gb == null) {
      return {
        level: "yellow",
        badge: "UNKNOWN",
        msg: "No DB size data yet.",
        directions: [],
        gb: null
      };
    }

    // Rule-of-thumb bands (not absolute)
    // OK: < 5GB, WATCH: 5-20GB, ACTION: >20GB (many ERP systems start to feel it here depending on reports, indexing, hardware)
    if (gb < 5) {
      return {
        level: "green",
        badge: "OK",
        msg: "Rule of thumb: under 5 GB is usually healthy for most small/medium setups.",
        directions: ["Keep monitoring growth", "Clean old logs occasionally"],
        gb
      };
    }
    if (gb < 20) {
      return {
        level: "yellow",
        badge: "WATCH",
        msg: "Rule of thumb: 5-20 GB is normal for growing systems, but performance depends on usage and server size.",
        directions: ["Review biggest tables", "Archive/clean logs & integration history", "Monitor slow reports"],
        gb
      };
    }
    return {
      level: "red",
      badge: "ACTION",
      msg: "Rule of thumb: above 20 GB often needs active maintenance to keep the system fast (especially backups and reports).",
      directions: ["Reduce database growth (clean logs/history)", "Review integrations generating excess logs", "Consider scaling DB/server resources"],
      gb
    };
  }

  function showToast(type, text) {
    const color = type === "error" ? "red" : type === "warn" ? "yellow" : "green";
    $toast.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent ${color === "green" ? "health" : color === "yellow" ? "actions" : "audit"}"></div>
        <div class="upeo-pill"><span class="upeo-dot ${color}"></span>${frappe.utils.escape_html(text)}</div>
      </div>
    `);
    $toast.show();
    setTimeout(() => $toast.fadeOut(300), 2400);
  }

  // -----------------------------
  // Loading skeletons
  // -----------------------------
  function renderLoading() {
    $health.html(`
      <div class="upeo-glass upeo-card-pad upeo-section">
        <div class="upeo-accent health"></div>
        <div class="upeo-skeleton" style="height:18px; width: 38%;"></div>
        <div class="upeo-skeleton" style="height:14px; width: 66%; margin-top:10px;"></div>
        <div class="upeo-skeleton" style="height:14px; width: 42%; margin-top:8px;"></div>
        <div class="upeo-divider"></div>
        <div class="row">
          ${[1, 2, 3, 4].map(() => `
            <div class="col-sm-3">
              <div class="upeo-skeleton" style="height:26px; width: 65%;"></div>
              <div class="upeo-skeleton" style="height:12px; width: 40%; margin-top:8px;"></div>
            </div>
          `).join("")}
        </div>
      </div>
    `);

    $left.html(`
      <div class="upeo-glass upeo-card-pad upeo-section">
        <div class="upeo-accent tables"></div>
        <div class="upeo-skeleton" style="height:16px; width: 35%;"></div>
        <div class="upeo-skeleton" style="height:220px; width: 100%; margin-top:12px;"></div>
      </div>
    `);

    $right.html(`
      <div class="upeo-glass upeo-card-pad upeo-section">
        <div class="upeo-accent actions"></div>
        <div class="upeo-skeleton" style="height:16px; width: 55%;"></div>
        <div class="upeo-skeleton" style="height:34px; width: 100%; margin-top:12px;"></div>
        <div class="upeo-skeleton" style="height:34px; width: 100%; margin-top:12px;"></div>
      </div>
    `);

    $audit.html(`
      <div class="upeo-glass upeo-card-pad upeo-section">
        <div class="upeo-accent audit"></div>
        <div class="upeo-skeleton" style="height:16px; width: 40%;"></div>
        <div class="upeo-skeleton" style="height:180px; width: 100%; margin-top:12px;"></div>
      </div>
    `);
  }

  // -----------------------------
  // Dialogs
  // -----------------------------
  function reasonDialog(title, subtitle, onSubmit) {
    const d = new frappe.ui.Dialog({
      title,
      fields: [
        { fieldname: "subtitle", fieldtype: "HTML", options: `<div class="upeo-subtle">${frappe.utils.escape_html(subtitle || "")}</div>` },
        { fieldname: "reason", fieldtype: "Small Text", label: "Reason", reqd: 1 },
      ],
      primary_action_label: "Confirm",
      primary_action(values) {
        d.hide();
        onSubmit(values.reason);
      },
    });
    d.show();
  }

  function cleanupDialog(table) {
    const d = new frappe.ui.Dialog({
      title: `Clean up old data: ${table}`,
      fields: [
        {
          fieldname: "help",
          fieldtype: "HTML",
          options: `
            <div class="upeo-subtle">
              This removes old log/history records to reduce database size. It does <b>not</b> affect business transactions.
            </div>
          `,
        },
        { fieldname: "days", fieldtype: "Int", label: "Delete records older than (days)", reqd: 1, default: 30 },
        { fieldname: "reason", fieldtype: "Small Text", label: "Reason", reqd: 1 },
        { fieldname: "preview_html", fieldtype: "HTML" },
      ],
      primary_action_label: "Preview impact",
      primary_action() {
        // Always read fresh values from the dialog at call time
        const vals = d.get_values();
        if (!vals) return; // validation failed

        const $previewWrap = d.fields_dict.preview_html.$wrapper;
        const $primaryBtn = d.get_primary_btn();

        // Freeze the Preview button to prevent double-calls
        $primaryBtn.prop("disabled", true).text("Loading…");

        frappe.call({
          method: "f_watcher.actions.cleanup.preview",
          args: { table, days: vals.days },
          callback(r) {
            $primaryBtn.prop("disabled", false).text("Preview impact");
            const info = r.message || {};
            const count = info.records_to_delete ?? 0;

            // Hide execute button when there is nothing to delete
            const execBtn = count > 0
              ? `<button class="btn btn-danger btn-sm upeo-btn upeo-exec-cleanup">Execute cleanup</button>`
              : `<div class="upeo-subtle" style="color:#16a34a;margin-top:4px;">Nothing to delete — all records are within the retention window.</div>`;

            $previewWrap.html(`
              <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section" style="margin-top:10px;">
                <div class="upeo-accent actions"></div>
                <div style="font-weight:850;">Preview</div>
                <div class="upeo-subtle" style="margin-top:6px;">
                  This will delete approximately <b>${count}</b> records older than <b>${info.days ?? vals.days}</b> days.
                </div>
                <div class="upeo-subtle" style="margin-top:6px;">${frappe.utils.escape_html(info.warning || "")}</div>
                <div style="margin-top:12px;">${execBtn}</div>
              </div>
            `);

            // Scope selector to dialog wrapper — avoids stale global DOM matches
            $previewWrap.find(".upeo-exec-cleanup").off("click").on("click", function () {
              const $btn = $(this);
              frappe.confirm("This cannot be undone. Proceed?", () => {
                // Re-read values at execute time in case user edited after previewing
                const execVals = d.get_values();
                if (!execVals) return;

                $btn.prop("disabled", true).text("Deleting…");
                frappe.call({
                  method: "f_watcher.actions.cleanup.execute",
                  args: { table, days: execVals.days, reason: execVals.reason },
                  callback(resp) {
                    d.hide();
                    showToast("ok", `Cleanup done: deleted ${resp.message?.deleted ?? 0} rows.`);
                    refresh(true);
                  },
                  error() {
                    // frappe.msgprint renders above dialog backdrop — toast is hidden behind it
                    frappe.msgprint({
                      title: "Cleanup failed",
                      message: "The cleanup could not be completed. Check the server error log for details.",
                      indicator: "red",
                    });
                    $btn.prop("disabled", false).text("Execute cleanup");
                  },
                });
              });
            });
          },
          error() {
            $primaryBtn.prop("disabled", false).text("Preview impact");
            frappe.msgprint({
              title: "Preview failed",
              message: "Could not load preview. Check your permissions or the server error log.",
              indicator: "red",
            });
          },
        });
      },
    });

    d.show();
  }

  // -----------------------------
  // Render
  // -----------------------------
  function render(data) {
    const sys = data.system;
    const snap = data.db_snapshot;
    const queues = data.queues || [];
    const big = data.big_tables || [];

    const h = healthLevel(sys);
    const score = healthScore(sys, queues);
    const scoreDot = score == null ? "yellow" : score >= 80 ? "green" : score >= 60 ? "yellow" : "red";
    const scoreLabel = score == null ? "–" : score;
    const qSummary = queues.slice(0, 3).map(q => `${q.queue_name}: ${q.job_count} waiting`).join(" · ") || "No queue data yet";

    // Premium tooltip payloads (readable + actionable)
    const tipCPU = {
      title: "CPU (How busy the server is)",
      text: "CPU is the server’s processing power. High CPU means the server is working very hard.",
      bands: [
        { tag: "Normal", desc: "20-65% most of the time." },
        { tag: "Watch", desc: "65-85% during busy hours may feel slower." },
        { tag: "Action", desc: "85%+ for 10-15 minutes: users may see delays/timeouts." },
      ],
      actions: ["check slow reports", "check stuck background jobs", "consider adding CPU"],
    };

    const tipRAM = {
      title: "RAM (Server memory)",
      text: "RAM is the server’s working memory (like a desk). More RAM helps it handle more users and tasks smoothly.",
      bands: [
        { tag: "Normal", desc: "30-75% is usually fine." },
        { tag: "Watch", desc: "75-85%: system may feel slower at peak times." },
        { tag: "Action", desc: "85%+ for 10-15 minutes: performance can drop sharply." },
      ],
      actions: ["reduce heavy reports", "reduce background pressure", "consider adding RAM"],
    };

    const tipDisk = {
      title: "Disk (Storage used)",
      text: "Disk is where the database and files live. When disk gets too full, systems can fail or slow down.",
      bands: [
        { tag: "Normal", desc: "Below 80%." },
        { tag: "Watch", desc: "80-90%: plan cleanup soon." },
        { tag: "Action", desc: "Above 90%: risk of failures and slowdowns." },
      ],
      actions: ["clean old logs/files", "increase disk size", "review large attachments"],
    };

    const tipLoad = {
		title: "Load (Work waiting in line)",
		text:
			"Load shows how much work the server is trying to handle at the same time. " +
			"To know if it’s healthy, compare Load to the number of CPU cores on the server.",

		bands: [
			{
			tag: "Step 1",
			desc:
				"Find your CPU cores. Example: if your server has 4 CPU cores, use 4 as your reference."
			},
			{
			tag: "Normal",
			desc:
				"Load is BELOW the number of CPU cores. " +
				"Example: Load 0.8-3.0 on a 4-core server → system feels fast."
			},
			{
			tag: "Watch",
			desc:
				"Load is AROUND the number of CPU cores. " +
				"Example: Load ~4.0 on a 4-core server → system is busy but OK."
			},
			{
			tag: "Action",
			desc:
				"Load is HIGHER than CPU cores for 10-15 minutes. " +
				"Example: Load 6+ on a 4-core server → users will feel slowness."
			}
		],

		actions: [
			"check queue backlog",
			"identify slow reports or heavy jobs",
			"restart background workers if stuck",
			"add more CPU if this happens often"
		]
	};


    // Database size guidance (show status, allowable bands, directions)
    const db = dbGuidance(snap ? snap.total_mb : null);
	const dbSizeText = (snap && snap.total_mb != null) ? formatDbSize(snap.total_mb) : "-";
    const dbDot = db.level === "green" ? "green" : db.level === "yellow" ? "yellow" : "red";

    $health.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent health"></div>

        <div class="upeo-header">
          <div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
              <div class="upeo-pill">
                <span class="upeo-dot ${h.level}"></span>
                <span>${h.title}</span>
                <span class="upeo-badge">${h.level.toUpperCase()}</span>
              </div>
              <div class="upeo-pill" title="System health score (0–100)">
                <span class="upeo-dot ${scoreDot}"></span>
                <span>Health Score: <b>${scoreLabel}</b>/100</span>
              </div>
              ${(function() {
                const u = currentUptime;
                if (!u || u.uptime_pct == null) return "";
                const dot = u.uptime_pct >= 99.9 ? "green" : u.uptime_pct >= 99 ? "yellow" : "red";
                return `<div class="upeo-pill" title="Uptime over last 24 hours (${u.total_checks} checks)">
                  <span class="upeo-dot ${dot}"></span>
                  <span>Uptime: <b>${u.uptime_pct}%</b></span>
                </div>`;
              })()}
            </div>
            <div class="upeo-subtle" style="margin-top:8px;">${h.msg}</div>
            <div class="upeo-subtle" style="margin-top:6px;">Background tasks: ${frappe.utils.escape_html(qSummary)}</div>
            <div class="upeo-subtle" style="margin-top:6px;"><b>${frappe.utils.escape_html(advice(sys))}</b></div>
          </div>

          <div style="text-align:right;">
            <div class="upeo-subtle">Last update</div>
            <div style="font-weight:850;">${sys ? prettyTime(sys.timestamp) : "-"}</div>
          </div>
        </div>

        <div class="upeo-divider"></div>

        <div class="row">
          <div class="col-sm-3">
            <div class="upeo-kpi">${sys ? `${Number(sys.cpu_percent).toFixed(0)}%${deltaArrow(currentDeltas?.cpu)}` : "-"}</div>
            <div class="upeo-kpi-label">
              <span>CPU</span>
              <span class="upeo-tip-btn" data-upeo-tip="cpu">i</span>
            </div>
          </div>

          <div class="col-sm-3">
            <div class="upeo-kpi">${sys ? `${Number(sys.ram_percent).toFixed(0)}%${deltaArrow(currentDeltas?.ram)}` : "-"}</div>
            <div class="upeo-kpi-label">
              <span>RAM</span>
              <span class="upeo-tip-btn" data-upeo-tip="ram">i</span>
            </div>
          </div>

          <div class="col-sm-3">
            <div class="upeo-kpi">${sys ? `${Number(sys.disk_percent).toFixed(0)}%${deltaArrow(currentDeltas?.disk)}` : "-"}</div>
            <div class="upeo-kpi-label">
              <span>Disk</span>
              <span class="upeo-tip-btn" data-upeo-tip="disk">i</span>
            </div>
            ${(function() {
              const f = currentForecast;
              if (!f || !f.days_until_full) return "";
              return `<div class="upeo-subtle" style="font-size:11px;margin-top:3px;">full in ~${f.days_until_full}d</div>`;
            })()}
          </div>

          <div class="col-sm-3">
            <div class="upeo-kpi">${sys ? Number(sys.load_1).toFixed(2) : "-"}</div>
            <div class="upeo-kpi-label">
              <span>Load (1m)</span>
              <span class="upeo-tip-btn" data-upeo-tip="load">i</span>
            </div>
          </div>
        </div>

        <div class="upeo-divider"></div>

        <div class="upeo-header" style="margin-bottom:0;">
          <div>
            <div style="font-weight:850; display:flex; align-items:center; gap:10px;">
              <span>Database size</span>
              <span class="upeo-pill" style="padding:5px 10px;">
                <span class="upeo-dot ${dbDot}"></span>
                <span>${db.badge}</span>
              </span>
            </div>

            <div class="upeo-subtle" style="margin-top:6px;">
              Current: <b>${dbSizeText}</b>
              ${snap ? `· (${mb(snap.total_mb)} total)` : ""}
            </div>

            <div class="upeo-subtle" style="margin-top:6px;">
              <b>Under 5 GB</b> is usually OK · <b>5-20 GB</b> is common for growing systems · <b>20 GB+</b> needs active maintenance.
            </div>

            <div class="upeo-subtle" style="margin-top:6px;">
              ${frappe.utils.escape_html(db.msg)}
            </div>

            ${
              db.level !== "green"
                ? `<div class="upeo-subtle" style="margin-top:8px;">
                     <b>Directions:</b> ${frappe.utils.escape_html(db.directions.join(" · "))}
                   </div>`
                : `<div class="upeo-subtle" style="margin-top:8px;">
                     <b>Directions:</b> ${frappe.utils.escape_html(db.directions.join(" · "))}
                   </div>`
            }
          </div>

          <div style="text-align:right;">
            <span class="upeo-badge">${snap ? (snap.tables_count ?? "-") : "-"} tables</span>
          </div>
        </div>
      </div>
    `);

    // Attach tooltip payloads to each tip button
    const map = { cpu: tipCPU, ram: tipRAM, disk: tipDisk, load: tipLoad };
    $("[data-upeo-tip]").each(function () {
      const key = $(this).attr("data-upeo-tip");
      $(this).data("upeoTipPayload", map[key]);
    });

    $left.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent tables"></div>

        <div class="upeo-header">
          <div>
            <div class="upeo-title">Biggest tables</div>
            <div class="upeo-subtle">Top 10 by size · includes plain-English meaning</div>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <div class="upeo-badge">Auto-updating</div>
            <button class="btn btn-default btn-sm upeo-btn" id="upeo-refresh-tables" title="Fetch latest table sizes from the database now">↻ Refresh</button>
          </div>
        </div>

        <div class="table-responsive">
          <table class="table table-bordered upeo-table">
            <thead>
              <tr>
                <th>Table</th>
                <th>Total</th>
                <th>Rows</th>
                <th>Importance</th>
                <th>Why it matters</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="upeo-tables-body">
              ${renderTableRows(big)}
            </tbody>
          </table>
        </div>
      </div>
    `);

    $right.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent actions"></div>

        <div class="upeo-title">Operator actions</div>
        <div class="upeo-subtle" style="margin-top:6px;">
          Permission-based and audited. Use only when needed.
        </div>

        <div class="upeo-divider"></div>

        <button class="btn btn-primary btn-sm upeo-btn" id="upeo-restart-workers" style="width:100%;">Restart background workers</button>
        <div class="upeo-subtle" style="margin-top:6px;">Use if queues are stuck or tasks are not processing.</div>

        <div style="height:10px;"></div>

        <button class="btn btn-primary btn-sm upeo-btn" id="upeo-restart-scheduler" style="width:100%;">Restart scheduler (automation)</button>
        <div class="upeo-subtle" style="margin-top:6px;">Use if scheduled jobs are not running.</div>

        <div style="height:10px;"></div>

        <button class="btn btn-default btn-sm upeo-btn" id="upeo-start-maintenance" style="width:100%;">Start Maintenance Window</button>
        <div class="upeo-subtle" style="margin-top:6px;">Suppress alerts during planned changes.</div>

        <div class="upeo-divider"></div>

        <div class="upeo-subtle">
          Tip: If issues persist after restarts, check database growth and slow reports.
        </div>
      </div>
    `);

    bindActions();
    wirePremiumTooltips();
  }

  function renderAudit(rows) {
    $audit.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent audit"></div>

        <div class="upeo-header">
          <div>
            <div class="upeo-title">Recent actions (audit)</div>
            <div class="upeo-subtle">Who did what, and when</div>
          </div>
          <div class="upeo-badge">Last 15</div>
        </div>

        <div class="table-responsive">
          <table class="table table-bordered upeo-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>User</th>
                <th>Action</th>
                <th>Target</th>
                <th>Result</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              ${(rows || []).map(r => `
                <tr>
                  <td>${prettyTime(r.creation || r.timestamp)}</td>
                  <td>${frappe.utils.escape_html(r.user)}</td>
                  <td><span class="upeo-badge">${frappe.utils.escape_html(r.action)}</span></td>
                  <td>${frappe.utils.escape_html(r.target || "-")}</td>
                  <td>${frappe.utils.escape_html(r.result || "-")}</td>
                  <td style="max-width:420px;">${frappe.utils.escape_html(r.reason || "")}</td>
                </tr>
              `).join("")}
              ${rows && rows.length ? "" : `<tr><td colspan="6" class="upeo-muted">No actions yet.</td></tr>`}
            </tbody>
          </table>
        </div>
      </div>
    `);
  }

  // -----------------------------
  // 2.7c: Health score (0-100)
  // -----------------------------
  function healthScore(sys, queues) {
    if (!sys) return null;
    let score = 100;
    if (sys.cpu_percent > 90)       score -= 30;
    else if (sys.cpu_percent > 70)  score -= 15;
    if (sys.ram_percent > 90)       score -= 25;
    else if (sys.ram_percent > 75)  score -= 10;
    if (sys.disk_percent > 90)      score -= 20;
    else if (sys.disk_percent > 80) score -= 10;
    const totalFailed = (queues || []).reduce((s, q) => s + (q.failed_count || 0), 0);
    if (totalFailed > 10)      score -= 15;
    else if (totalFailed > 0)  score -= 5;
    return Math.max(0, score);
  }

  // 2.2: render dependency health map
  function renderHealthMap(data) {
    const nodes = [
      { key: "mysql",       label: "MySQL" },
      { key: "redis_cache", label: "Redis Cache" },
      { key: "redis_queue", label: "Redis Queue" },
      { key: "scheduler",   label: "Scheduler" },
      { key: "workers",     label: "Workers" },
    ];
    const pills = nodes.map(n => {
      const info = data[n.key] || {};
      const dot  = info.status === "ok" ? "green" : info.status === "warn" ? "yellow" : "red";
      const extra = n.key === "workers" && info.count != null ? ` (${info.count})` : "";
      const detail = info.detail ? ` · ${frappe.utils.escape_html(info.detail)}` : "";
      return `<span class="upeo-pill"><span class="upeo-dot ${dot}"></span>${n.label}${extra}${detail}</span>`;
    }).join(" ");

    $healthMap.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent health"></div>
        <div class="upeo-header" style="margin-bottom:8px;">
          <div class="upeo-title">Dependency Health</div>
          <div class="upeo-subtle">Auto-refreshes every 30s</div>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">${pills}</div>
      </div>
    `);
  }

  // 2.1: render time-series charts
  let currentHours = 6;
  let currentSite  = null;   // null = all sites (single-site bench default)
  function renderCharts(data) {
    if (!data || !data.system || !data.system.length) {
      $charts.html(`
        <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
          <div class="upeo-accent tables"></div>
          <div class="upeo-title">Metric History</div>
          <div class="upeo-subtle" style="margin-top:8px;">No historical data yet — metrics are collected every minute.</div>
        </div>
      `);
      return;
    }

    const rangeHtml = [1, 6, 24, 168].map(h => {
      const label = h === 168 ? '7d' : h === 24 ? '24h' : h === 6 ? '6h' : '1h';
      const active = h === currentHours ? 'btn-primary' : 'btn-default';
      return `<button class="btn btn-sm upeo-btn ${active}" data-hours="${h}">${label}</button>`;
    }).join('');

    $charts.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent tables"></div>
        <div class="upeo-header">
          <div class="upeo-title">Metric History</div>
          <div style="display:flex;gap:6px;align-items:center;">
            <div style="display:flex;gap:6px;" id="upeo-range-btns">${rangeHtml}</div>
            <button class="btn btn-default btn-sm upeo-btn" id="upeo-export-csv" title="Export system metrics as CSV">↓ CSV</button>
          </div>
        </div>
        <div id="upeo-cpu-chart" style="margin-top:8px;"></div>
        <div id="upeo-db-chart" style="margin-top:8px;"></div>
      </div>
    `);

    const labels = data.system.map(r => r.bucket ? r.bucket.slice(11, 16) : '');

    if (typeof frappe.Chart !== 'undefined') {
      new frappe.Chart("#upeo-cpu-chart", {
        type: "line",
        data: {
          labels,
          datasets: [
            { name: "CPU %",  values: data.system.map(r => parseFloat(r.cpu  || 0).toFixed(1)) },
            { name: "RAM %",  values: data.system.map(r => parseFloat(r.ram  || 0).toFixed(1)) },
            { name: "Disk %", values: data.system.map(r => parseFloat(r.disk || 0).toFixed(1)) },
          ],
        },
        colors: ["#5e64ff", "#f59e0b", "#ef4444"],
        lineOptions: { regionFill: 1, hideDots: labels.length > 60 },
        axisOptions: { xIsSeries: true },
        height: 200,
        title: "CPU / RAM / Disk %",
      });
    }

    if (data.db_size && data.db_size.length && typeof frappe.Chart !== 'undefined') {
      const dbLabels = data.db_size.map(r => r.bucket ? r.bucket.slice(11, 16) : '');
      new frappe.Chart("#upeo-db-chart", {
        type: "line",
        data: {
          labels: dbLabels,
          datasets: [
            { name: "DB Size (MB)", values: data.db_size.map(r => parseFloat(r.total_mb || 0).toFixed(0)) },
          ],
        },
        colors: ["#10b981"],
        lineOptions: { regionFill: 1, hideDots: dbLabels.length > 60 },
        axisOptions: { xIsSeries: true },
        height: 160,
        title: "Database Size trend (MB)",
      });
    }

    // Bind range selector buttons
    $charts.find("#upeo-range-btns").find("[data-hours]").off("click").on("click", function() {
      currentHours = parseInt($(this).data("hours"));
      fetchHistory();
    });

    // CSV export
    $charts.find("#upeo-export-csv").off("click").on("click", function() {
      const $btn = $(this);
      $btn.prop("disabled", true).text("Exporting…");
      frappe.call({
        method: "f_watcher.api.export.system_metrics_csv",
        args: { hours: currentHours },
        callback(r) {
          $btn.prop("disabled", false).text("↓ CSV");
          if (!r.message) return;
          const blob = new Blob([r.message], { type: "text/csv" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `system_metrics_${currentHours}h.csv`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        },
        error() {
          $btn.prop("disabled", false).text("↓ CSV");
          showToast("error", "Export failed. Check permissions.");
        },
      });
    });
  }

  // 2.7a: collector health panel (rendered inside $right)
  function renderCollectorStatus(rows) {
    if (!rows || !rows.length) return;
    const dots = rows.map(r => {
      const dot = r.status === "ok" ? "green" : r.status === "never" ? "red" : "yellow";
      const age = r.minutes_ago != null ? `${r.minutes_ago}m ago` : "never";
      return `<div style="display:flex;align-items:center;gap:6px;margin:4px 0;">
        <span class="upeo-dot ${dot}"></span>
        <span style="font-size:12px;">${frappe.utils.escape_html(r.label)}</span>
        <span class="upeo-subtle" style="font-size:11px;">${age}</span>
      </div>`;
    }).join('');

    // Append to $right (below operator actions)
    const $existing = $right.find('#upeo-collector-panel');
    const html = `
      <div id="upeo-collector-panel" class="upeo-glass upeo-card-pad upeo-fade-in upeo-section" style="margin-top:12px;">
        <div class="upeo-accent health"></div>
        <div class="upeo-title">Collector Status</div>
        <div style="margin-top:8px;">${dots}</div>
      </div>
    `;
    if ($existing.length) {
      $existing.replaceWith(html);
    } else {
      $right.append(html);
    }
  }

  // 2.7b: active alert rules panel
  function renderAlertRules() {
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "F Watcher Alert Rule",
        filters: { is_active: 1 },
        fields: ["name", "rule_name", "metric_type", "property_name", "condition", "threshold_value", "last_triggered"],
        limit: 20,
      },
      callback(r) {
        const rules = r.message || [];
        if (!rules.length) {
          $alertRulesPanel.html('');
          return;
        }
        const rows = rules.map(rule => {
          const last = rule.last_triggered ? prettyTime(rule.last_triggered) : '<span class="upeo-subtle">Never</span>';
          return `<tr>
            <td><b>${frappe.utils.escape_html(rule.rule_name)}</b></td>
            <td>${frappe.utils.escape_html(rule.metric_type)}</td>
            <td>${frappe.utils.escape_html(rule.property_name || '-')}</td>
            <td>${frappe.utils.escape_html(rule.condition)} ${rule.threshold_value}</td>
            <td>${last}</td>
          </tr>`;
        }).join('');

        $alertRulesPanel.html(`
          <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
            <div class="upeo-accent audit"></div>
            <div class="upeo-header">
              <div class="upeo-title">Active Alert Rules</div>
              <div class="upeo-badge">${rules.length} active</div>
            </div>
            <div class="table-responsive">
              <table class="table table-bordered upeo-table">
                <thead><tr>
                  <th>Rule</th><th>Metric</th><th>Property</th><th>Threshold</th><th>Last Triggered</th>
                </tr></thead>
                <tbody>${rows}</tbody>
              </table>
            </div>
          </div>
        `);
      }
    });
  }

  // 2.7d: queue panel with retry buttons
  function renderQueuesPanel(queues) {
    if (!queues || !queues.length) {
      $queuesPanel.html('');
      return;
    }

    // Group by queue_name, take most recent row per queue
    const byQueue = {};
    queues.forEach(q => {
      if (!byQueue[q.queue_name] || q.timestamp > byQueue[q.queue_name].timestamp) {
        byQueue[q.queue_name] = q;
      }
    });

    const cards = Object.values(byQueue).map(q => {
      const failedDot = q.failed_count > 0 ? "red" : "green";
      const qSafe = frappe.utils.escape_html(q.queue_name);
      return `
        <div class="col-sm-4" style="margin-bottom:12px;">
          <div class="upeo-glass upeo-card-pad upeo-section" style="border-radius:14px;">
            <div style="font-weight:850;">${qSafe}</div>
            <div class="upeo-subtle" style="margin-top:4px;">Waiting: <b>${q.job_count || 0}</b></div>
            <div class="upeo-subtle">Workers: <b>${q.active_workers || 0}</b></div>
            <div style="display:flex;align-items:center;gap:6px;margin-top:6px;">
              <span class="upeo-dot ${failedDot}"></span>
              <span class="upeo-subtle">Failed: <b>${q.failed_count || 0}</b></span>
            </div>
            <div style="display:flex;gap:6px;margin-top:8px;">
              <button class="btn btn-default btn-xs upeo-btn upeo-view-jobs-btn"
                      data-queue="${qSafe}" data-status="queued" style="flex:1;">
                View queued
              </button>
              ${q.failed_count > 0 ? `
                <button class="btn btn-warning btn-xs upeo-btn upeo-view-jobs-btn"
                        data-queue="${qSafe}" data-status="failed" style="flex:1;">
                  View failed
                </button>
              ` : ''}
            </div>
            ${q.failed_count > 0 ? `
              <button class="btn btn-warning btn-sm upeo-btn upeo-retry-btn"
                      data-queue="${qSafe}"
                      style="margin-top:6px;width:100%;">
                Retry failed jobs
              </button>
            ` : ''}
            <div id="upeo-jobs-${qSafe}" style="margin-top:4px;"></div>
          </div>
        </div>
      `;
    }).join('');

    $queuesPanel.html(`
      <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
        <div class="upeo-accent actions"></div>
        <div class="upeo-title" style="margin-bottom:12px;">Queue Status</div>
        <div class="row">${cards}</div>
      </div>
    `);

    $queuesPanel.find(".upeo-retry-btn").off("click").on("click", function() {
      const qName = $(this).data("queue");
      const $btn = $(this);
      frappe.confirm(`Requeue all failed jobs in "${qName}"?`, () => {
        $btn.prop("disabled", true).text("Requeueing…");
        frappe.call({
          method: "f_watcher.actions.queue.retry_failed_jobs",
          args: { queue_name: qName },
          callback(r) {
            showToast("ok", r.message?.message || "Jobs requeued.");
            $btn.prop("disabled", false).text("Retry failed jobs");
            refresh(true);
          },
          error() {
            showToast("error", "Requeue failed. Check permissions.");
            $btn.prop("disabled", false).text("Retry failed jobs");
          },
        });
      });
    });

    $queuesPanel.find(".upeo-view-jobs-btn").off("click").on("click", function() {
      const qName = $(this).data("queue");
      const status = $(this).data("status");
      const $panel = $queuesPanel.find(`#upeo-jobs-${qName}`);
      if ($panel.is(":visible") && $panel.data("active-status") === status) {
        $panel.empty().hide();
      } else {
        $panel.show().data("active-status", status);
        renderJobInspector(qName, status);
      }
    });
  }

  // -----------------------------
  // 4.1: Maintenance window
  // -----------------------------
  function checkMaintenance() {
    frappe.call({
      method: "f_watcher.api.maintenance.active_window",
      callback(r) {
        const win = r.message;
        if (win) {
          $maintenance.html(`
            <div style="background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.4);
                        border-radius:10px;padding:10px 14px;display:flex;align-items:center;gap:12px;">
              <span class="upeo-dot yellow"></span>
              <span style="font-weight:700;">Maintenance window active:</span>
              <span>${frappe.utils.escape_html(win.title)}</span>
              <span class="upeo-subtle">ends ${prettyTime(win.ends_at)}</span>
              ${win.reason ? `<span class="upeo-subtle">· ${frappe.utils.escape_html(win.reason)}</span>` : ""}
            </div>
          `);
        } else {
          $maintenance.html("");
        }
      },
    });
  }

  function startMaintenanceDialog() {
    const d = new frappe.ui.Dialog({
      title: "Start Maintenance Window",
      fields: [
        { fieldname: "title", fieldtype: "Data", label: "Title", reqd: 1,
          default: "Planned maintenance" },
        { fieldname: "duration_minutes", fieldtype: "Select", label: "Duration",
          options: "15\n30\n60\n120\n240", default: "30" },
        { fieldname: "reason", fieldtype: "Small Text", label: "Reason" },
      ],
      primary_action_label: "Start",
      primary_action(values) {
        d.hide();
        frappe.call({
          method: "f_watcher.api.maintenance.create_window",
          args: { title: values.title, duration_minutes: values.duration_minutes, reason: values.reason || "" },
          callback() {
            showToast("ok", "Maintenance window started. Alerts suppressed.");
            checkMaintenance();
          },
          error() { showToast("error", "Failed to start maintenance window."); },
        });
      },
    });
    d.show();
  }

  // 4.3: Queue job inspector
  function renderJobInspector(queueName, status) {
    frappe.call({
      method: "f_watcher.actions.queue.queue_jobs",
      args: { queue_name: queueName, status, limit: 20 },
      callback(r) {
        const jobs = r.message || [];
        const $panel = $queuesPanel.find(`#upeo-jobs-${queueName}`);
        if (!jobs.length) {
          $panel.html(`<div class="upeo-subtle" style="padding:8px;">No ${status} jobs.</div>`);
          return;
        }
        const rows = jobs.map(j => `
          <tr>
            <td style="font-family:monospace;font-size:11px;">${frappe.utils.escape_html(j.id.slice(0, 12))}…</td>
            <td style="font-size:11px;">${frappe.utils.escape_html(j.func || j.description || "-")}</td>
            <td class="upeo-subtle">${j.enqueued_at ? j.enqueued_at.slice(0, 16) : "-"}</td>
            <td>
              <button class="btn btn-danger btn-xs upeo-cancel-job"
                      data-queue="${frappe.utils.escape_html(queueName)}"
                      data-job="${frappe.utils.escape_html(j.id)}">✕</button>
            </td>
          </tr>
        `).join("");
        $panel.html(`
          <table class="table table-bordered upeo-table" style="font-size:12px;margin-top:4px;">
            <thead><tr><th>ID</th><th>Function</th><th>Enqueued</th><th></th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
        `);
        $panel.find(".upeo-cancel-job").off("click").on("click", function() {
          const $btn = $(this);
          frappe.call({
            method: "f_watcher.actions.queue.cancel_job",
            args: { queue_name: $btn.data("queue"), job_id: $btn.data("job") },
            callback() { showToast("ok", "Job cancelled."); renderJobInspector(queueName, status); },
            error() { showToast("error", "Failed to cancel job."); },
          });
        });
      },
    });
  }

  // 4.4: Cache card — rendered in $right
  function renderCacheCard() {
    frappe.call({
      method: "f_watcher.api.cache.stats",
      callback(r) {
        const s = r.message || {};
        const patternRows = (s.key_patterns || []).slice(0, 8).map(([k, c]) =>
          `<tr><td style="font-size:11px;">${frappe.utils.escape_html(k)}</td>
               <td style="text-align:right;font-size:11px;">${c}</td></tr>`
        ).join("");

        const html = `
          <div id="upeo-cache-card" class="upeo-glass upeo-card-pad upeo-fade-in upeo-section" style="margin-top:12px;">
            <div class="upeo-accent health"></div>
            <div class="upeo-title">Redis Cache</div>
            <div class="upeo-subtle" style="margin-top:6px;">
              Memory: <b>${s.used_memory_human || "-"}</b> / ${s.maxmemory_human || "no limit"}
            </div>
            <div class="upeo-subtle">Hit ratio: <b>${s.hit_ratio != null ? s.hit_ratio + "%" : "-"}</b></div>
            <div class="upeo-subtle">Total keys: <b>${s.total_keys || 0}</b></div>
            ${patternRows ? `
              <div class="upeo-divider" style="margin:8px 0;"></div>
              <div class="upeo-subtle" style="margin-bottom:4px;">Top key prefixes</div>
              <table class="table table-bordered upeo-table" style="margin:0;">
                <tbody>${patternRows}</tbody>
              </table>
            ` : ""}
            <div style="margin-top:10px;">
              <button class="btn btn-warning btn-sm upeo-btn" id="upeo-flush-cache" style="width:100%;">
                Flush cache
              </button>
            </div>
          </div>
        `;

        const $existing = $right.find("#upeo-cache-card");
        if ($existing.length) $existing.replaceWith(html);
        else $right.append(html);

        $right.find("#upeo-flush-cache").off("click").on("click", function() {
          frappe.confirm("Flush the entire Redis cache? This may slow the next few requests.", () => {
            frappe.call({
              method: "f_watcher.api.cache.flush_cache",
              callback() { showToast("ok", "Cache flushed."); renderCacheCard(); },
              error() { showToast("error", "Flush failed. Check permissions."); },
            });
          });
        });
      },
      error() {
        // Cache card is non-critical — silently skip on error
      },
    });
  }

  // 5.8: Error patterns panel
  function renderErrorPatterns() {
    frappe.call({
      method: "f_watcher.dashboards.metrics.error_patterns",
      args: { hours: 24, limit: 15 },
      callback(r) {
        const rows = r.message || [];
        if (!rows.length) {
          $errorPatterns.html("");
          return;
        }
        const trs = rows.map(e => `
          <tr>
            <td style="font-family:monospace;font-size:11px;max-width:480px;word-break:break-word;">
              ${frappe.utils.escape_html(e.snippet || "")}
            </td>
            <td style="text-align:right;"><span class="upeo-badge">${e.count}</span></td>
            <td class="upeo-subtle">${prettyTime(e.last_seen)}</td>
            <td style="font-size:11px;">${frappe.utils.escape_html(e.method || "-")}</td>
          </tr>
        `).join("");

        $errorPatterns.html(`
          <div class="upeo-glass upeo-card-pad upeo-fade-in upeo-section">
            <div class="upeo-accent audit"></div>
            <div class="upeo-header">
              <div>
                <div class="upeo-title">Error Patterns (last 24 h)</div>
                <div class="upeo-subtle">Grouped by error prefix — most frequent first</div>
              </div>
              <div class="upeo-badge">${rows.length} patterns</div>
            </div>
            <div class="table-responsive">
              <table class="table table-bordered upeo-table">
                <thead><tr>
                  <th>Error snippet</th><th style="text-align:right;">Count</th>
                  <th>Last seen</th><th>Method</th>
                </tr></thead>
                <tbody>${trs}</tbody>
              </table>
            </div>
          </div>
        `);
      },
    });
  }

  // -----------------------------
  // Action bindings
  // -----------------------------
  // -----------------------------
  // Table rows helper (used by render + refreshBigTables)
  // -----------------------------
  function renderTableRows(rows) {
    if (!rows || !rows.length) {
      return `<tr><td colspan="6" class="upeo-muted">No table stats yet.</td></tr>`;
    }
    return rows.map(r => `
      <tr>
        <td><b>${frappe.utils.escape_html(r.table_name)}</b></td>
        <td>${mb(r.total_mb)}</td>
        <td>${r.rows_est || 0}</td>
        <td><span class="upeo-badge">${frappe.utils.escape_html(r.importance || "-")}</span></td>
        <td style="max-width:420px;">${frappe.utils.escape_html(r.importance_note || "-")}</td>
        <td>
          ${r.cleanup_allowed
            ? `<button class="btn btn-warning btn-sm upeo-btn" data-clean="${frappe.utils.escape_html(r.table_name)}">Clean up</button>
               <div class="upeo-subtle" style="margin-top:6px;">${frappe.utils.escape_html(r.cleanup_hint || "")}</div>`
            : `<span class="upeo-muted">—</span>`}
        </td>
      </tr>
    `).join("");
  }

  // -----------------------------
  // Refresh biggest tables only
  // -----------------------------
  function refreshBigTables() {
    const $btn = $("#upeo-refresh-tables");
    const $tbody = $("#upeo-tables-body");

    $btn.prop("disabled", true).text("Loading…");
    $tbody.css("opacity", "0.4");

    frappe.call({
      method: "f_watcher.dashboards.metrics.latest",
      callback(r) {
        const rows = (r.message || {}).big_tables || [];
        $tbody.html(renderTableRows(rows)).css("opacity", "1");
        // re-bind cleanup buttons on the new rows
        $tbody.find("[data-clean]").off("click").on("click", function () {
          cleanupDialog($(this).data("clean"));
        });
        $btn.prop("disabled", false).text("↻ Refresh");
        showToast("ok", "Table sizes refreshed.");
      },
      error() {
        $tbody.css("opacity", "1");
        $btn.prop("disabled", false).text("↻ Refresh");
        frappe.msgprint({
          title: "Refresh failed",
          message: "Could not fetch latest table data. Check server logs.",
          indicator: "red",
        });
      },
    });
  }

  function bindActions() {
    $("#upeo-restart-workers").off("click").on("click", () => {
      reasonDialog(
        "Restart background workers",
        "Use this if queues are not draining and background tasks appear stuck.",
        (reason) => {
          frappe.call({
            method: "f_watcher.actions.control.restart_workers",
            args: { reason },
            callback() {
              showToast("ok", "Workers restart executed (audited).");
              refresh(true);
            },
            error() {
              showToast("error", "Restart failed. Check server logs or permissions.");
            }
          });
        }
      );
    });

    $("#upeo-restart-scheduler").off("click").on("click", () => {
      reasonDialog(
        "Restart scheduler (automation)",
        "Use this if scheduled jobs are not running as expected.",
        (reason) => {
          frappe.call({
            method: "f_watcher.actions.control.restart_scheduler",
            args: { reason },
            callback() {
              showToast("ok", "Scheduler restart executed (audited).");
              refresh(true);
            },
            error() {
              showToast("error", "Restart failed. Check server logs or permissions.");
            }
          });
        }
      );
    });

    $("[data-clean]").off("click").on("click", function () {
      cleanupDialog($(this).data("clean"));
    });

    $("#upeo-refresh-tables").off("click").on("click", () => refreshBigTables());

    $("#upeo-start-maintenance").off("click").on("click", () => startMaintenanceDialog());
  }

  // -----------------------------
  // Auto-refresh
  // -----------------------------
  let f_watcherTimer = null;
  let healthMapTimer = null;
  let maintenanceTimer = null;
  let cacheTimer = null;

  // Phase 5: auxiliary state — one cycle behind, that's fine
  let currentDeltas   = null;
  let currentForecast = null;
  let currentUptime   = null;

  function fetchHealthMap() {
    frappe.call({
      method: "f_watcher.api.health.check",
      callback(r) { renderHealthMap(r.message || {}); },
    });
  }

  function fetchHistory() {
    const args = { hours: currentHours };
    if (currentSite) args.site = currentSite;
    frappe.call({
      method: "f_watcher.dashboards.metrics.history",
      args,
      callback(r) { renderCharts(r.message || {}); },
    });
  }

  function fetchCollectorStatus() {
    frappe.call({
      method: "f_watcher.dashboards.metrics.collector_status",
      callback(r) { renderCollectorStatus(r.message || []); },
    });
  }

  // 3.5: site selector — populate from compare() and wire to refresh
  function initSiteSelector() {
    frappe.call({
      method: "f_watcher.dashboards.metrics.compare",
      callback(r) {
        const sites = Object.keys(r.message || {});
        if (sites.length < 2) return;  // single-site bench, no need for selector

        const opts = sites.map(s =>
          `<option value="${frappe.utils.escape_html(s)}">${frappe.utils.escape_html(s)}</option>`
        ).join("");

        const $sel = $(`
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
            <span class="upeo-subtle" style="font-size:12px;">Site:</span>
            <select id="upeo-site-select" class="form-control" style="width:220px;font-size:13px;">
              <option value="">All sites</option>
              ${opts}
            </select>
          </div>
        `).prependTo($body);

        $sel.find("#upeo-site-select").on("change", function() {
          currentSite = $(this).val() || null;
          refresh(true);
          fetchHistory();
        });
      },
    });
  }

  function refresh(silent = false) {
    if (!silent) renderLoading();

    const args = {};
    if (currentSite) args.site = currentSite;

    // Fire auxiliary state fetches in parallel — used from NEXT render cycle (lag is fine)
    frappe.call({
      method: "f_watcher.dashboards.metrics.compare_periods",
      args: { hours: 24, ...(currentSite ? { site: currentSite } : {}) },
      callback(r) { currentDeltas = (r.message || {}).delta || null; },
    });
    frappe.call({
      method: "f_watcher.dashboards.metrics.disk_forecast",
      callback(r) { currentForecast = r.message || null; },
    });
    frappe.call({
      method: "f_watcher.dashboards.metrics.uptime_summary",
      args: { ...(currentSite ? { site: currentSite } : {}) },
      callback(r) { currentUptime = r.message || null; },
    });

    frappe.call({
      method: "f_watcher.dashboards.metrics.latest",
      args,
      callback(r) {
        const data = r.message || {};
        render(data);
        renderQueuesPanel(data.queues || []);
        frappe.call({
          method: "f_watcher.dashboards.metrics.audit",
          args: { limit: 15 },
          callback(a) { renderAudit(a.message || []); }
        });
        renderAlertRules();
        fetchCollectorStatus();
        renderErrorPatterns();
      },
      error() {
        showToast("error", "Failed to load metrics. Check server logs.");
      }
    });
  }

  function startAutoRefresh() {
    if (f_watcherTimer) clearInterval(f_watcherTimer);
    f_watcherTimer = setInterval(() => refresh(true), 15000);

    // Health map refreshes every 30s
    if (healthMapTimer) clearInterval(healthMapTimer);
    fetchHealthMap();
    healthMapTimer = setInterval(fetchHealthMap, 30000);

    // Maintenance window banner — every 60s
    if (maintenanceTimer) clearInterval(maintenanceTimer);
    checkMaintenance();
    maintenanceTimer = setInterval(checkMaintenance, 60000);

    // Cache card — every 60s
    if (cacheTimer) clearInterval(cacheTimer);
    renderCacheCard();
    cacheTimer = setInterval(renderCacheCard, 60000);

    // Charts load once on start
    fetchHistory();

    // Site selector (no-op on single-site bench)
    initSiteSelector();
  }

  $(wrapper).on("remove", () => {
    if (f_watcherTimer) clearInterval(f_watcherTimer);
    if (healthMapTimer) clearInterval(healthMapTimer);
    if (maintenanceTimer) clearInterval(maintenanceTimer);
    if (cacheTimer) clearInterval(cacheTimer);
    hideTip();
  });

  // Initial load
  renderLoading();
  refresh(false);
  startAutoRefresh();
};
