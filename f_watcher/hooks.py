app_name = "f_watcher"
app_title = "F Watcher"
app_publisher = "BluePhoenix"
app_description = "Watches your Frappe universe. Logs, workers, queues, and system health in one place."
app_email = "bluephoenix00995@gmailcom"
app_license = "gpl-3.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "f_watcher",
		"logo": "/assets/f_watcher/images/f_watcher_logo.png",
		"title": "F Watcher",
		"route": "/app/f-watcher",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/f_watcher/css/f_watcher.css"
# app_include_js = "/assets/f_watcher/js/f_watcher.js"

# include js, css files in header of web template
# web_include_css = "/assets/f_watcher/css/f_watcher.css"
# web_include_js = "/assets/f_watcher/js/f_watcher.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "f_watcher/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "f_watcher/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "f_watcher.utils.jinja_methods",
# 	"filters": "f_watcher.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "f_watcher.install.before_install"
# after_install = "f_watcher.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "f_watcher.uninstall.before_uninstall"
# after_uninstall = "f_watcher.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "f_watcher.utils.before_app_install"
# after_app_install = "f_watcher.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "f_watcher.utils.before_app_uninstall"
# after_app_uninstall = "f_watcher.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

notification_config = "f_watcher.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------


scheduler_events = {
    "cron": {
        "* * * * *": [
            "f_watcher.collectors.system.collect",
            "f_watcher.collectors.queue.collect",
        ],
        "*/5 * * * *": [
            "f_watcher.collectors.db_storage.collect",
            "f_watcher.collectors.database.collect",
            "f_watcher.collectors.alerting.evaluate_and_alert",
            "f_watcher.collectors.app_health.collect",
            "f_watcher.collectors.redis_cache.collect",
            "f_watcher.collectors.apm.collect",
            "f_watcher.collectors.integration.collect",
        ],
        "*/15 * * * *": [
            "f_watcher.collectors.security.collect",
        ],
        "0 * * * *": [
            "f_watcher.collectors.backups.collect",
            "f_watcher.collectors.database_health.collect",
            "f_watcher.collectors.infrastructure.collect",
        ],
        "0 2 * * *": [
            "f_watcher.collectors.retention.purge",
        ],
        "0 8 * * *": [
            "f_watcher.collectors.digest.send_daily_digest",
        ],
    }
}


# Testing
# -------

# before_tests = "f_watcher.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "f_watcher.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "f_watcher.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["f_watcher.utils.before_request"]
# after_request = ["f_watcher.utils.after_request"]

# Job Events
# ----------
# before_job = ["f_watcher.utils.before_job"]
# after_job = ["f_watcher.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"f_watcher.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


fixtures = [
    "Client Script",
    "Custom Field",
    {
        "dt": "Role",
        "filters": [["name", "in", ["F Watcher Operator", "F Watcher Viewer"]]],
    },
]
