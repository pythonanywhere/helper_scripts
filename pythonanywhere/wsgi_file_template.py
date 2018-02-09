# This file contains the WSGI configuration required to serve up your
# Django app
import os
import sys

# Add your project directory to the sys.path
settings_path = '{project.settings_path.parent.parent}'
sys.path.insert(0, settings_path)

# Set environment variable to tell django where your settings.py is
os.environ['DJANGO_SETTINGS_MODULE'] = '{project.settings_path.parent.name}.settings'

# Set the 'application' variable to the Django wsgi app
from django.core.wsgi import get_wsgi_application
{staticfileshandler_import}
application = {application}
