import frappe


def get_notification_config():
    return {
        "for_doctype": {
            "F Watcher Alert Log": {"status": "Triggered"},
        },
    }
