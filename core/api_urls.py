from django.urls import include, path, re_path

from core import views as core_views
from core.api_views import api_docs, openapi_json

urlpatterns = [
    path("openapi.json", openapi_json, name="openapi-json"),
    path("docs", api_docs, name="api-docs"),
    path("health/live", core_views.live_health, name="api-health-live"),
    path("health/ready", core_views.ready_health, name="api-health-ready"),
    re_path(r"auth/?", include("accounts.api_urls")),
    re_path(r"catalog/?", include("academic.api_urls")),
    re_path(r"students/?", include("students.api_urls")),
    re_path(r"enrollments/?", include("enrollments.api_urls")),
    re_path(r"attendance/?", include("attendance.api_urls")),
    re_path(r"grades/?", include("grading.api_urls")),
    re_path(r"fees/?", include("finance.api_urls")),
    re_path(r"reports/?", include("portal.report_urls")),
]
