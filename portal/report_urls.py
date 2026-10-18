from django.urls import path

from . import report_views

urlpatterns = [
    path("dashboard", report_views.dashboard, name="api-dashboard-report"),
    path("<str:kind>", report_views.report, name="api-report"),
    path("audit/list", report_views.audit_list, name="api-audit-list"),
]
