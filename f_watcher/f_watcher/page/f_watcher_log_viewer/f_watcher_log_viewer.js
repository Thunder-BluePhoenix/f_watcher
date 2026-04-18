frappe.pages['f-watcher-log-viewer'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Real-Time Telemetry & Log Streaming',
        single_column: true
    });

    $(frappe.render_template('f_watcher_log_viewer', {})).appendTo(page.body);

    const $body       = $(page.body);
    const $selector   = $body.find('#log_file_selector');
    const $output     = $body.find('#log_output');
    const $status     = $body.find('#log_status');
    const $lines      = $body.find('#log_lines');
    const $refreshBtn = $body.find('#refresh_log_btn');
    const $pauseBtn   = $body.find('#log_pause_btn');
    const $copyBtn    = $body.find('#log_copy_btn');
    const $downloadBtn= $body.find('#log_download_btn');
    const $search     = $body.find('#log_search');

    let pollTimer  = null;
    let inFlight   = false;
    let paused     = false;
    let rawText    = '';   // last full text from server (used by search filter)

    // 2.4: realtime lines arrive here; append without a full re-fetch
    frappe.realtime.on('fw_log_line', function(data) {
        if (!data || !data.line) return;
        rawText += '\n' + data.line;
        applyFilter();
        if (isAtBottom()) {
            $output[0].scrollTop = $output[0].scrollHeight;
        }
        $status.text('Streaming · last line ' + frappe.datetime.now_time())
               .removeClass('text-danger');
    });

    function isAtBottom() {
        const el = $output[0];
        return el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    }

    // 2.6b: colorize severity keywords (XSS-safe — escape first, then add spans)
    function colorize(raw) {
        const escaped = frappe.utils.escape_html(raw);
        return escaped
            .replace(/^(.*\bCRITICAL\b.*)$/gm, '<span style="color:#ff4757;font-weight:bold;">$1</span>')
            .replace(/^(.*\bERROR\b.*)$/gm,    '<span style="color:#ff6b6b;">$1</span>')
            .replace(/^(.*\bWARNING\b.*)$/gm,  '<span style="color:#ffd93d;">$1</span>')
            .replace(/^(.*\bINFO\b.*)$/gm,     '<span style="color:#7bed9f;">$1</span>');
    }

    // 2.6a: client-side filter — re-renders from rawText without a server call
    function applyFilter() {
        const term = ($search.val() || '').trim().toLowerCase();
        const lines = rawText.split('\n');
        const filtered = term ? lines.filter(l => l.toLowerCase().includes(term)) : lines;
        $output.html(colorize(filtered.join('\n')));
    }

    function fetch_logs() {
        if (paused || inFlight) return;
        inFlight = true;

        const filename = $selector.val();
        const lines    = Math.min(parseInt($lines.val()) || 200, 500);
        $status.text('Fetching ' + filename + '…').removeClass('text-danger');

        frappe.call({
            method: 'f_watcher.api.logs.tail_log',
            args: { filename, lines },
            callback: function(r) {
                inFlight = false;
                const wasAtBottom = isAtBottom();

                if (r.message && typeof r.message === 'string') {
                    rawText = r.message;
                    applyFilter();
                    if (wasAtBottom) {
                        $output[0].scrollTop = $output[0].scrollHeight;
                    }
                    $status.text('Live · last updated ' + frappe.datetime.now_time())
                           .removeClass('text-danger');
                } else if (r.message && r.message.error) {
                    $status.text('Error: ' + r.message.error).addClass('text-danger');
                }
                schedulePoll();
            },
            error: function() {
                inFlight = false;
                $status.text('Failed to fetch log. Check permissions or server.').addClass('text-danger');
                schedulePoll();
            }
        });
    }

    function schedulePoll() {
        if (pollTimer) clearTimeout(pollTimer);
        if (!paused) {
            pollTimer = setTimeout(fetch_logs, 4000);
        }
    }

    function stopPoll() {
        if (pollTimer) { clearTimeout(pollTimer); pollTimer = null; }
    }

    // Start realtime stream (2.4)
    function startStream() {
        frappe.call({
            method: 'f_watcher.api.log_stream.start_stream',
            args: { filename: $selector.val() },
        });
    }

    $refreshBtn.off('click').on('click', function() {
        stopPoll();
        fetch_logs();
    });

    $selector.off('change').on('change', function() {
        rawText = '';
        $output.html('Switching log file…');
        stopPoll();
        fetch_logs();
        startStream();
    });

    $lines.off('change').on('change', function() {
        stopPoll();
        fetch_logs();
    });

    // 2.6a: filter on search input
    $search.off('input').on('input', applyFilter);

    // 2.6c: pause / resume
    $pauseBtn.off('click').on('click', function() {
        paused = !paused;
        $pauseBtn.text(paused ? '▶ Resume' : '⏸ Pause');
        if (!paused) {
            fetch_logs();
        } else {
            stopPoll();
            $status.text('Paused').removeClass('text-danger');
        }
    });

    // 2.6d: copy to clipboard
    $copyBtn.off('click').on('click', function() {
        navigator.clipboard.writeText(rawText).then(function() {
            frappe.show_alert({ message: 'Copied to clipboard', indicator: 'green' });
        }).catch(function() {
            frappe.show_alert({ message: 'Copy failed — try selecting manually', indicator: 'red' });
        });
    });

    // 2.6d: download as file
    $downloadBtn.off('click').on('click', function() {
        const blob = new Blob([rawText], { type: 'text/plain' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = $selector.val() + '_' + frappe.datetime.now_datetime().replace(/[: ]/g, '-') + '.log';
        a.click();
        URL.revokeObjectURL(a.href);
    });

    page.on_page_hide = function() {
        stopPoll();
    };

    $(wrapper).on('remove', function() {
        stopPoll();
    });

    // Initial load
    fetch_logs();
    startStream();
};
