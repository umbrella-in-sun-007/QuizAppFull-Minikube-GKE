"""
Django settings for local development with Cloud SQL.
"""
import os
from .base import *

DEBUG = True

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-key-please-change")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

# Cloud SQL Database Configuration
if os.getenv("USE_CLOUD_SQL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.getenv("DB_HOST", "cloud-sql-proxy"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "NAME": os.getenv("DB_NAME", "dev"),
            "USER": os.getenv("DB_USER", "dev_user"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "CONN_MAX_AGE": 600,
            "OPTIONS": {
                "connect_timeout": 10,
            },
        }
    }
    print("✓ Using Cloud SQL for development")
else:
    # Fallback to SQLite for offline development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
    print("✓ Using SQLite for offline development")

# Development-specific settings
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Show SQL queries in console (disable in production!)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if os.getenv("SHOW_SQL") else "INFO",
            "propagate": False,
        },
    },
}
