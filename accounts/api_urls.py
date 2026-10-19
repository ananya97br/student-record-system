from django.urls import path

from . import api_views

urlpatterns = [
    path("login", api_views.login, name="api-login"),
    path("logout", api_views.logout, name="api-logout"),
    path("me", api_views.me, name="api-me"),
    path("forgot-password", api_views.forgot_password, name="api-forgot-password"),
    path("reset-password", api_views.reset_password, name="api-reset-password"),
    path("unlock/<uuid:user_id>", api_views.unlock_user, name="api-unlock-user"),
    path("users", api_views.users, name="api-users"),
    path("users/<uuid:user_id>", api_views.update_user, name="api-update-user"),
    path("security-alerts", api_views.security_alerts, name="api-security-alerts"),
    path("security-alerts/<int:alert_id>/resolve", api_views.resolve_alert, name="api-resolve-alert"),
]
