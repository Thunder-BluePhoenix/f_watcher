frappe.pages['f-watcher-log-viewer'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Real-Time Telemetry & Log Streaming',
        single_column: true
    });

    $(frappe.render_template('f_watcher_log_viewer', {})).appendTo(page.body);

    // Scope all selectors to this page instance — avoids collisions when
    // Frappe caches the page DOM and re-renders
    const $body     = $(page.body);
    const $selector = $body.find('#log_file_selector');
    const $output   = $body.find('#log_output');
    const $status   = $body.find('#log_status');
    const $lines    = $body.find('#log_lines');
    const $refreshBtn = $body.find('#refresh_log_btn');

    let pollTimer   = null;
    let inFlight    = false;   // LV-06: prevent stacking concurrent requests

    // LV-05: only auto-scroll when user is already at (or near) the bottom
    function isAtBottom() {
        const el = $output[0];
        return el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    }

    function fetch_logs() {
        if (inFlight) return;  // skip if previous call still running
        inFlight = true;

        const filename = $selector.val();
        const lines    = Math.min(parseInt($lines.val()) || 200, 500); // LV-08: cap at 500
        $status.text('Fetching ' + filename + '…').removeClass('text-danger');

        frappe.call({
            method: 'f_watcher.api.logs.tail_log',
            args: { filename, lines },
            callback: function(r) {
                inFlight = false;
                const wasAtBottom = isAtBottom();

                if (r.message && typeof r.message === 'string') {
                    $output.text(r.message);
                    if (wasAtBottom) {
                        $output.scrollTop($output[0].scrollHeight);
                    }
                    $status
                        .text('Live · last updated ' + frappe.datetime.now_time())
                        .removeClass('text-danger');
                } else if (r.message && r.message.error) {
                    $output.text('Error: ' + r.message.error);
                    $status.text('Error reading log file.').addClass('text-danger');
                }
                schedulePoll();  // reschedule only after call finishes (LV-06)
            },
            // LV-04: handle network/permission failures visibly
            error: function() {
                inFlight = false;
                $status.text('Failed to fetch log. Check permissions or server.').addClass('text-danger');
                schedulePoll();
            }
        });
    }

    function schedulePoll() {
        if (pollTimer) clearTimeout(pollTimer);
        pollTimer = setTimeout(fetch_logs, 4000);
    }

    function stopPoll() {
        if (pollTimer) {
            clearTimeout(pollTimer);
            pollTimer = null;
        }
    }

    // LV-03: .off() before .on() so handlers don't accumulate on re-render
    $refreshBtn.off('click').on('click', function() {
        stopPoll();
        fetch_logs();
    });

    $selector.off('change').on('change', function() {
        $output.text('Switching log file…');
        stopPoll();
        fetch_logs();
    });

    $lines.off('change').on('change', function() {
        stopPoll();
        fetch_logs();
    });

    // LV-01: use Frappe's correct page hide event to stop polling on navigation
    page.on_page_hide = function() {
        stopPoll();
    };

    // Also stop if the DOM element itself is removed
    $(wrapper).on('remove', function() {
        stopPoll();
    });

    // Initial fetch
    fetch_logs();
};
