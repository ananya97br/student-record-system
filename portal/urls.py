from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login", views.login_page, name="login-page"),
    path("portal/<str:section>", views.portal_page, name="portal-page"),
]
