from django.urls import path

from . import api_views

urlpatterns = [
    path("eligible", api_views.eligible, name="api-eligible-offerings"),
    path("", api_views.my_enrollments_or_enroll, name="api-enrollments"),
    path("<int:enrollment_id>/drop", api_views.drop_enrollment, name="api-drop-enrollment"),
]
