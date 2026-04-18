import frappe


def _check_permission():
    if not (
        frappe.session.user == "Administrator"
        or "System Manager" in frappe.get_roles()
        or "F Watcher Operator" in frappe.get_roles()
        or "F Watcher Viewer" in frappe.get_roles()
    ):
        frappe.throw("Not permitted.", frappe.PermissionError)


@frappe.whitelist()
def audit():
    _check_permission()

    custom_fields = frappe.db.get_all(
        "Custom Field",
        fields=["name", "dt", "fieldname", "fieldtype", "modified_by", "modified"],
        order_by="modified desc",
        limit=50,
    )

    client_scripts = []
    if frappe.db.exists("DocType", "Client Script"):
        client_scripts = frappe.db.get_all(
            "Client Script",
            fields=["name", "dt", "enabled", "modified_by", "modified"],
            order_by="modified desc",
            limit=20,
        )

    server_scripts = []
    if frappe.db.exists("DocType", "Server Script"):
        server_scripts = frappe.db.get_all(
            "Server Script",
            fields=["name", "script_type", "reference_doctype", "disabled", "modified_by", "modified"],
            order_by="modified desc",
            limit=20,
        )

    property_setters_count = frappe.db.count("Property Setter")

    return {
        "custom_fields": custom_fields,
        "custom_fields_count": len(custom_fields),
        "client_scripts": client_scripts,
        "server_scripts": server_scripts,
        "property_setters_count": property_setters_count,
    }
