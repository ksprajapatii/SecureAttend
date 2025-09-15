"""
WSGI config for SecureAttend project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secureattend.settings')

application = get_wsgi_application()
