# Settings package - imports from base by default
# Use DJANGO_SETTINGS_MODULE environment variable to switch:
# - leasing_core.settings.development (default)
# - leasing_core.settings.production

import os

environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
else:
    from .development import *

