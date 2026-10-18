from django.urls import path

from . import api_views

urlpatterns = [
    path("me", api_views.my_profile, name="api-my-profile"),
    path("me/change-requests", api_views.my_change_requests, name="api-my-change-requests"),
    path("me/documents", api_views.my_documents, name="api-my-documents"),
    path("documents/<uuid:document_id>/download", api_views.download_document, name="api-download-document"),
    path("", api_views.student_list_or_create, name="api-students"),
    path("<int:student_pk>", api_views.student_detail, name="api-student-detail"),
    path("change-requests", api_views.change_requests, name="api-change-requests"),
    path("change-requests/<int:request_id>/decision", api_views.change_request_decision, name="api-change-request-decision"),
]
