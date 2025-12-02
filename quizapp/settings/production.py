import os
import dj_database_url
from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Google Cloud Storage for Media
if "GS_BUCKET_NAME" in os.environ:
    GS_BUCKET_NAME = os.environ["GS_BUCKET_NAME"]
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


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-production-key-change-me")

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
if "DATABASE_URL" in os.environ:
    DATABASES["default"] = dj_database_url.config(conn_max_age=600)
elif "DB_HOST" in os.environ:
    # GKE deployment with individual environment variables
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "prod"),
        "USER": os.getenv("DB_USER", "prod_user"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,
    }

try:
    from .local import *
except ImportError:
    pass

# Secret Manager Integration
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
        SECRET_KEY = get_secret("quizapp-prod-django-secret-key")
        db_password = get_secret("quizapp-prod-db-password")
        
        if "default" in DATABASES:
            DATABASES["default"]["PASSWORD"] = db_password
            
except ImportError:
    print("Warning: google-cloud-secret-manager not installed.")
except Exception as e:
    print(f"Warning: Failed to fetch secrets from Secret Manager: {e}")
