from django.urls import path

from . import api_views

urlpatterns = [
    path("programs", api_views.programs, name="api-programs"),
    path("programs/<int:program_id>", api_views.program_detail, name="api-program-detail"),
    path("semesters", api_views.semesters, name="api-semesters"),
    path("courses", api_views.courses, name="api-courses"),
    path("prerequisites", api_views.prerequisites, name="api-prerequisites"),
    path("offerings", api_views.offerings, name="api-offerings"),
    path("offerings/<int:offering_id>", api_views.offering_detail, name="api-offering-detail"),
    path("grading-schemes", api_views.grading_schemes, name="api-grading-schemes"),
    path("fee-structures", api_views.fee_structures, name="api-fee-structures"),
    path("scholarships", api_views.scholarships, name="api-scholarships"),
    path("configuration", api_views.configuration, name="api-configuration"),
]
