import frappe

def create_log_page():
    if not frappe.db.exists("Page", "f-watcher-log-viewer"):
        if not frappe.db.exists("Page", "F Watcher Log Viewer"):
            doc = frappe.get_doc({
                "doctype": "Page",
                "module": "F Watcher",
                "page_name": "f-watcher-log-viewer",
                "title": "F Watcher Log Viewer",
                "standard": "Yes",
                "roles": [{"role": "System Manager"}]
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
            print("Page created!")
    else:
        print("Page already exists!")
