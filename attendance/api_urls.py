from django.urls import path

from . import api_views

urlpatterns = [
    path("faculty-offerings", api_views.faculty_offerings, name="api-faculty-offerings"),
    path("offerings/<int:offering_id>/roster", api_views.roster, name="api-attendance-roster"),
    path("offerings/<int:offering_id>/sessions", api_views.sessions, name="api-attendance-sessions"),
    path("sessions/<int:session_id>/records", api_views.bulk_records, name="api-bulk-attendance"),
    path("student-summary", api_views.student_summary, name="api-student-attendance"),
    path("flagged", api_views.flagged, name="api-flagged-attendance"),
]
