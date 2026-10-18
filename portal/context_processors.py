from django.conf import settings


def portal_context(request):
    return {"app_name": "Student Record System", "app_base_url": settings.APP_BASE_URL}
