import frappe

def create_doctypes():
    if not frappe.db.exists("DocType", "F Watcher Redis Metric"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "module": "F Watcher",
            "custom": 0,
            "name": "F Watcher Redis Metric",
            "naming_rule": "Expression",
            "autoname": "format:REDM-{######}",
            "fields": [
                {"fieldname": "timestamp", "label": "Timestamp", "fieldtype": "Datetime", "in_list_view": 1},
                {"fieldname": "redis_type", "label": "Redis Instance", "fieldtype": "Data", "default": "Cache", "in_list_view": 1},
                {"fieldname": "used_memory_human", "label": "Used Memory", "fieldtype": "Data", "in_list_view": 1},
                {"fieldname": "hit_ratio", "label": "Hit Ratio (%)", "fieldtype": "Float", "in_list_view": 1},
                {"fieldname": "keyspace_hits", "label": "Keyspace Hits", "fieldtype": "Int"},
                {"fieldname": "keyspace_misses", "label": "Keyspace Misses", "fieldtype": "Int"},
            ]
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created F Watcher Redis Metric")
