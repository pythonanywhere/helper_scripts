# This file contains the WSGI configuration required to serve up your
# Django app
import os
import sys

# Add your project directory to the sys.path
project_path = {project_path!r}
sys.path.insert(0, project_path)

# Set environment variable to tell django where your settings.py is
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'

# Set the 'application' variable to the Django wsgi app
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
