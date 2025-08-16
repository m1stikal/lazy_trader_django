"""
WSGI config for lazy_trader project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ['REQUESTS_CA_BUNDLE'] = '/Users/m1stikal/Dev/lazy_trader_flask/venv/lib/python3.13/site-packages/certifi/cacert.pem'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lazy_trader.settings')

application = get_wsgi_application()
