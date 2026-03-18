frappe.pages['f-watcher-log-viewer'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Real-Time Telemetry & Log Streaming',
        single_column: true
    });

    $(frappe.render_template('f_watcher_log_viewer', {})).appendTo(page.body);

    let pollInterval = null;

    const fetch_logs = () => {
        let filename = $('#log_file_selector').val();
        $('#log_status').text('Polling ' + filename + '...');
        
        frappe.call({
            method: 'f_watcher.api.logs.tail_log',
            args: { filename: filename, lines: 200 },
            callback: function(r) {
                if (r.message && typeof r.message === "string") {
                    let out = $('#log_output');
                    // Prevent DOM overload, just set text
                    out.text(r.message);
                    
                    // Auto scroll to bottom
                    out.scrollTop(out[0].scrollHeight);
                    $('#log_status').text('Streaming Live | Last Updated: ' + frappe.datetime.now_time());
                } else if (r.message && r.message.error) {
                    $('#log_output').text(r.message.error);
                }
            }
        });
    };

    $('#refresh_log_btn').on('click', fetch_logs);
    $('#log_file_selector').on('change', function() {
        $('#log_output').text("Switching log file...");
        fetch_logs();
    });

    // Initial fetch
    fetch_logs();

    // Poll every 4 seconds for a semi-realtime streaming feel
    pollInterval = setInterval(fetch_logs, 4000);

    // Destroy interval quietly if user navigates away
    $(wrapper).on('hide', function() {
        if (pollInterval) {
            clearInterval(pollInterval);
        }
    });
}