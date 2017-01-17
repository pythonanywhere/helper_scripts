#!/usr/bin/python3.5
"""Create a new Django webapp with a virtualenv.  Defaults to
your free domain, the latest version of Django and Python 3.5

Usage:
  new_django_project_in_virtualenv.py [--domain=<domain> --django=<django-version> --python=<python-version>]

Options:
  --domain=<domain>         Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]
  --django=<django-version> Django version, eg "1.11" [default: latest]
  --python=<python-version> Python version, eg "2.7"  [default: 3.5]
"""

from docopt import docopt
import getpass
import os
import subprocess
from textwrap import dedent


def create_virtualenv(name, python_version, django_version):
    pip_install = 'pip install django'
    if django_version != 'latest':
        pip_install += '==' + django_version
    command = 'mkvirtualenv --python=/usr/bin/python{python_version} {name} && {pip_install}'.format(
        name=name, python_version=python_version, pip_install=pip_install
    )
    subprocess.check_call(['bash', '-c', 'source virtualenvwrapper.sh && {}'.format(command)])



def start_django_project(domain, virtualenv_path):
    target_folder = os.path.expanduser('~/' + domain)
    os.mkdir(target_folder)
    subprocess.check_call([
        os.path.join(virtualenv_path, 'bin/django-admin.py'),
        'startproject',
        'mysite',
        target_folder
    ])
    with open(os.path.join(target_folder, 'mysite', 'settings.py'), 'a') as f:
        f.write(dedent(
            """
            MEDIA_URL = '/media/'
            STATIC_ROOT = os.path.join(BASE_DIR, 'static')
            MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
            """
        ))
    subprocess.check_call([
        os.path.join(virtualenv_path, 'bin/python'),
        os.path.join(target_folder, 'manage.py'),
        'collectstatic',
        '--noinput',
    ])



def create_webapp(domain, python_version, virtualenv_path, project_path):
    pass


def main(domain, django_version, python_version):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser()
        domain = '{}.pythonanywhere.com'.format(username)
    virtualenv_path = create_virtualenv(domain, python_version, django_version)
    project_path = start_django_project(domain, virtualenv_path)
    create_webapp(domain, python_version, virtualenv_path, project_path)



if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--django'], arguments['--python'])

