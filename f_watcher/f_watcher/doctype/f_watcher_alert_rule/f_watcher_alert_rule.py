from urllib.parse import urlparse
import frappe
from frappe.model.document import Document


class FWatcherAlertRule(Document):
    def validate(self):
        if self.alert_channel == "Webhook" and self.webhook_url:
            parsed = urlparse(self.webhook_url)
            if parsed.scheme not in ("http", "https"):
                frappe.throw("Webhook URL must use http or https.")
            if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
                frappe.throw("Webhook URL cannot point to localhost.")
        if not self.cooldown_minutes or self.cooldown_minutes < 1:
            self.cooldown_minutes = 15
