from django.urls import path

from . import api_views

urlpatterns = [
    path("components", api_views.components, name="api-assessment-components"),
    path("components/<int:component_id>/marks", api_views.bulk_marks, name="api-bulk-marks"),
    path("offerings/<int:offering_id>/finalize", api_views.finalize_offering, name="api-finalize-offering"),
    path("results", api_views.results, name="api-results"),
    path("results/<int:result_id>/override", api_views.override_result, name="api-override-result"),
    path("gpa", api_views.gpa, name="api-gpa"),
    path("transcript", api_views.transcript, name="api-transcript"),
    path("transcript/verify/<str:code>", api_views.verify_transcript, name="api-verify-transcript"),
]
