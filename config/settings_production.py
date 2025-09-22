"""
Production settings for QuizApp
"""

from .settings import *

# Production configuration
DEBUG = False
ALLOWED_HOSTS = ['*']  # Configure with your actual domain names

# Remove development-only apps and middleware
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_browser_reload']
MIDDLEWARE = [middleware for middleware in MIDDLEWARE 
              if middleware != 'django_browser_reload.middleware.BrowserReloadMiddleware']

# Add WhiteNoise for static file serving (insert after SecurityMiddleware)
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Static files configuration for better ASGI compatibility
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True

# Configure WhiteNoise for ASGI
WHITENOISE_AUTOREFRESH = False
WHITENOISE_MAX_AGE = 31536000  # 1 year

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ASGI-specific settings
# Force Django to use ASGI-compatible response handling
USE_I18N = True
USE_TZ = True

# Optional: Environment variables for production
# SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)
# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')
