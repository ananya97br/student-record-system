"""Django settings for the Student Record System.

The default development database is SQLite so a clean checkout can be tested
without a service. Docker and production use MySQL through DATABASE_URL.
"""
from pathlib import Path
import base64
import json
import os
import secrets

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

_dev_secret_file = BASE_DIR / "var" / "dev-secrets.json"


def _development_secrets():
    if _dev_secret_file.exists():
        try:
            return json.loads(_dev_secret_file.read_text())
        except (OSError, ValueError):
            pass
    values = {
        "django": secrets.token_urlsafe(48),
        "field": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
        "lookup": secrets.token_urlsafe(32),
        "jwt": secrets.token_urlsafe(48),
        "payment": secrets.token_urlsafe(48),
    }
    _dev_secret_file.parent.mkdir(parents=True, exist_ok=True)
    _dev_secret_file.write_text(json.dumps(values))
    try:
        _dev_secret_file.chmod(0o600)
    except OSError:
        pass
    return values


_generated_dev_secrets = _development_secrets() if os.getenv("DJANGO_DEBUG", "1").lower() in {"1", "true", "yes"} else {}
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or _generated_dev_secrets.get("django") or secrets.token_urlsafe(48)
DEBUG = os.getenv("DJANGO_DEBUG", "1").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip()]
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")
CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "core",
    "accounts",
    "academic",
    "students",
    "enrollments",
    "attendance",
    "grading",
    "finance",
    "portal",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.CorrelationIdMiddleware",
    "core.middleware.JwtCookieMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "portal.context_processors.portal_context",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def database_config():
    url = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
    if url.startswith("mysql://") or url.startswith("mysql2://"):
        value = url.split("://", 1)[1]
        credentials, host_part = value.rsplit("@", 1)
        user, password = credentials.split(":", 1)
        host_port, database = host_part.split("/", 1)
        if ":" in host_port:
            host, port = host_port.split(":", 1)
        else:
            host, port = host_port, "3306"
        return {
            "ENGINE": "django.db.backends.mysql",
            "NAME": database,
            "USER": user,
            "PASSWORD": password,
            "HOST": host,
            "PORT": port,
            "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
            "CONN_MAX_AGE": 60,
        }
    path = url.removeprefix("sqlite:///")
    return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / path}


DATABASES = {"default": database_config()}
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]
PASSWORD_RESET_TIMEOUT = 600

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / os.getenv("DOCUMENT_STORAGE_PATH", "var/documents")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.getenv("SECURE_COOKIES", "0").lower() in {"1", "true", "yes"}
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("SMTP_HOST", "localhost")
EMAIL_PORT = int(os.getenv("SMTP_PORT", "1025"))
EMAIL_HOST_USER = os.getenv("SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASS", "")
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = os.getenv("MAIL_FROM", "no-reply@student-record.local")

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "core.errors.drf_exception_handler",
}

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
JWT_COOKIE_NAME = "srs_access"
JWT_TTL_MINUTES = 30
FIELD_ENCRYPTION_KEY = os.getenv("FIELD_ENCRYPTION_KEY")
LOOKUP_HMAC_KEY = os.getenv("LOOKUP_HMAC_KEY")
PAYMENT_MOCK_HMAC_SECRET = os.getenv("PAYMENT_MOCK_HMAC_SECRET") or SECRET_KEY
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "0").lower() in {"1", "true", "yes"}
OTP_TTL_MINUTES = int(os.getenv("OTP_TTL_MINUTES", "10"))
ACCOUNT_LOCK_FAILED_ATTEMPTS = int(os.getenv("ACCOUNT_LOCK_FAILED_ATTEMPTS", "5"))
ATTENDANCE_THRESHOLD_DEFAULT = int(os.getenv("ATTENDANCE_THRESHOLD_DEFAULT", "75"))
RETENTION_YEARS = int(os.getenv("RETENTION_YEARS", "10"))
MALWARE_SCANNER = os.getenv("MALWARE_SCANNER", "deterministic")

# Ephemeral keys make tests and first-run development usable, but production
# must set both keys explicitly and rotate them through a secret manager.
if not FIELD_ENCRYPTION_KEY:
    FIELD_ENCRYPTION_KEY = _generated_dev_secrets.get("field") or base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
if not LOOKUP_HMAC_KEY:
    LOOKUP_HMAC_KEY = _generated_dev_secrets.get("lookup") or secrets.token_urlsafe(32)
if not os.getenv("JWT_SECRET_KEY"):
    JWT_SECRET_KEY = _generated_dev_secrets.get("jwt") or JWT_SECRET_KEY
if not os.getenv("PAYMENT_MOCK_HMAC_SECRET"):
    PAYMENT_MOCK_HMAC_SECRET = _generated_dev_secrets.get("payment") or PAYMENT_MOCK_HMAC_SECRET

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"structured": {"format": "time={asctime} level={levelname} message={message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "structured"}},
    "loggers": {"srs": {"handlers": ["console"], "level": "INFO"}},
}
