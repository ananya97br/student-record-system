from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core import views as core_views
from finance.web_views import mock_checkout

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.api_urls")),
    path("", include("portal.urls")),
    path("health/live", core_views.live_health, name="health-live"),
    path("health/ready", core_views.ready_health, name="health-ready"),
    path("payment/mock/<uuid:payment_id>", mock_checkout, name="mock-payment-checkout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
