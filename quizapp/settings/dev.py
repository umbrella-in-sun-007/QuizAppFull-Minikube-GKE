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

# Google Cloud Storage for Media (Dev)
if os.getenv("GS_BUCKET_NAME"):
    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
    STORAGES["default"] = {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
        },
    }
    GS_FILE_OVERWRITE = False
    GS_QUERYSTRING_AUTH = False
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"
    print(f"✓ Using GCS Bucket '{GS_BUCKET_NAME}' for media")

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

# Secret Manager Integration (Dev)
try:
    from google.cloud import secretmanager
    import google.auth

    if os.getenv("USE_SECRET_MANAGER"):
        def get_secret(secret_id):
            client = secretmanager.SecretManagerServiceClient()
            _, project_id = google.auth.default()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")

        print("✓ Fetching secrets from Secret Manager...")
        db_password = get_secret("quizapp-prod-db-password")
        
        if "default" in DATABASES:
            DATABASES["default"]["PASSWORD"] = db_password
            
except ImportError:
    pass
except Exception as e:
    print(f"Warning: Failed to fetch secrets from Secret Manager: {e}")
