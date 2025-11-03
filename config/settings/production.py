"""Production settings."""
from .base import *

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = False  # Set to True when HTTPS is configured
SESSION_COOKIE_SECURE = False  # Set to True when HTTPS is configured
CSRF_COOKIE_SECURE = False  # Set to True when HTTPS is configured
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
