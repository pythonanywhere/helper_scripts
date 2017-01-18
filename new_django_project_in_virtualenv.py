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
import requests
import subprocess
from textwrap import dedent

API_ENDPOINT = 'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/'


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
    post_url = API_ENDPOINT.format(username=getpass.getuser())
    patch_url = post_url + domain + '/'
    response = requests.post(post_url, data={
        'domain_name': domain, 'python_version': python_version
    })
    if not response.ok:
        raise Exception('POST to create webapp via API failed, got {}:{}'.format(response, response.text))
    response = requests.patch(patch_url, data={
        'virtualenv_path': virtualenv_path
    })
    if not response.ok:
        raise Exception('PATCH to set virtualenv path via API failed, got {}:{}'.format(response, response.text))



def update_wsgi_file(wsgi_file_path, project_path):
    template = open(os.path.join(os.path.dirname(__file__), 'wsgi_file_template.py')).read()
    with open(wsgi_file_path, 'w') as f:
        f.write(template.format(project_path=project_path))



def reload_webapp(domain):
    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/reload'
    response = requests.post(url)
    if not response.ok:
        raise Exception('POST to reload webapp via API failed, got {}:{}'.format(response, response.text))



def main(domain, django_version, python_version):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser()
        domain = '{}.pythonanywhere.com'.format(username)
    virtualenv_path = create_virtualenv(domain, python_version, django_version)
    project_path = start_django_project(domain, virtualenv_path)
    create_webapp(domain, python_version, virtualenv_path, project_path)
    wsgi_file_path = '/var/www/' + domain.replace('.', '_') + '_wsgi.py'
    update_wsgi_file(wsgi_file_path, project_path)
    reload_webapp(domain)



if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--django'], arguments['--python'])

