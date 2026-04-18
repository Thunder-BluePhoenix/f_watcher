import frappe
from frappe.model.document import Document


class FWatcherMaintenanceWindow(Document):
    def before_insert(self):
        self.created_by = frappe.session.user
