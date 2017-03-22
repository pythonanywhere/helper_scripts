#!/usr/bin/python3.5
"""Create a new Django webapp with a virtualenv.  Defaults to
your free domain, the latest version of Django and Python 3.5

Usage:
  pa_start_django_webapp_with_virtualenv.py [--domain=<domain> --django=<django-version> --python=<python-version>]

Options:
  --domain=<domain>         Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]
  --django=<django-version> Django version, eg "1.8.4"  [default: latest]
  --python=<python-version> Python version, eg "2.7"    [default: 3.5]
"""

from docopt import docopt
import getpass
import os
import requests
import subprocess
from textwrap import dedent

API_ENDPOINT = 'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/'
PYTHON_VERSIONS = {
    '2.7': 'python27',
    '3.3': 'python33',
    '3.4': 'python34',
    '3.5': 'python35',
}





class SanityException(Exception):
    pass


class AuthenticationError(Exception):
    pass



def call_api(url, method, **kwargs):
    response = requests.request(
        method=method,
        url=url,
        headers={'Authorization': 'Token {}'.format(os.environ['API_TOKEN'])},
        **kwargs
    )
    if response.status_code == 401:
        print(response, response.text)
        raise AuthenticationError('Authentication error {} calling API: {}'.format(
            response.status_code, response.text
        ))
    return response



def _virtualenv_path(domain):
    return os.path.join(os.environ['WORKON_HOME'], domain)


def _project_folder(domain):
    return os.path.expanduser('~/' + domain)


def sanity_checks(domain):
    token = os.environ.get('API_TOKEN')
    if not token:
        raise SanityException('Could not find your API token. You may need to create it on the Accounts page?')

    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/'
    response = call_api(url, 'get')
    if response.status_code == 200:
        raise SanityException('You already have a webapp for {}.\n\nUse the --nuke option if you want to replace it.'.format(domain))
    if os.path.exists(_virtualenv_path(domain)):
        raise SanityException('You already have a virtualenv for {}.\n\nUse the --nuke option if you want to replace it.'.format(domain))
    project_folder = _project_folder(domain)
    if os.path.exists(project_folder):
        raise SanityException('You already have a project folder at {}.\n\nUse the --nuke option if you want to replace it.'.format(project_folder))



def create_virtualenv(name, python_version, django_version):
    pip_install = 'pip install django'
    if django_version != 'latest':
        pip_install += '==' + django_version
    command = 'mkvirtualenv --python=/usr/bin/python{python_version} {name} && {pip_install}'.format(
        name=name, python_version=python_version, pip_install=pip_install
    )
    subprocess.check_call(['bash', '-c', 'source virtualenvwrapper.sh && {}'.format(command)])
    return _virtualenv_path(name)



def start_django_project(domain, virtualenv_path):
    target_folder = _project_folder(domain)
    os.mkdir(target_folder)
    subprocess.check_call([
        os.path.join(virtualenv_path, 'bin/django-admin.py'),
        'startproject',
        'mysite',
        target_folder
    ])
    return target_folder



def run_collectstatic(virtualenv_path, target_folder):
    subprocess.check_call([
        os.path.join(virtualenv_path, 'bin/python'),
        os.path.join(target_folder, 'manage.py'),
        'collectstatic',
        '--noinput',
    ])



def update_settings_file(domain, project_path):
    with open(os.path.join(project_path, 'mysite', 'settings.py')) as f:
        settings = f.read()
    new_settings = settings.replace(
        'ALLOWED_HOSTS = []',
        "ALLOWED_HOSTS = [{!r}]".format(domain)
    )
    new_settings += dedent(
        """
        MEDIA_URL = '/media/'
        STATIC_ROOT = os.path.join(BASE_DIR, 'static')
        MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
        """
    )
    with open(os.path.join(project_path, 'mysite', 'settings.py'), 'w') as f:
        f.write(new_settings)



def create_webapp(domain, python_version, virtualenv_path, project_path):
    post_url = API_ENDPOINT.format(username=getpass.getuser())
    patch_url = post_url + domain + '/'
    response = call_api(post_url, 'post', data={
        'domain_name': domain, 'python_version': PYTHON_VERSIONS[python_version]},
    )
    if not response.ok or response.json().get('status') == 'ERROR':
        raise Exception('POST to create webapp via API failed, got {}:{}'.format(response, response.text))
    response = call_api(patch_url, 'patch', data={'virtualenv_path': virtualenv_path})
    if not response.ok:
        raise Exception('PATCH to set virtualenv path via API failed, got {}:{}'.format(response, response.text))



def add_static_file_mappings(domain, project_path):
    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/static_files/'
    call_api(url, 'post', json=dict(
        url='/static/', path=os.path.join(project_path, 'static')
    ))
    call_api(url, 'post', json=dict(
        url='/media/', path=os.path.join(project_path, 'media')
    ))




def update_wsgi_file(wsgi_file_path, project_path):
    template = open(os.path.join(os.path.dirname(__file__), 'wsgi_file_template.py')).read()
    with open(wsgi_file_path, 'w') as f:
        f.write(template.format(project_path=project_path))



def reload_webapp(domain):
    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/reload/'
    response = call_api(url, 'post')
    if not response.ok:
        raise Exception('POST to reload webapp via API failed, got {}:{}'.format(response, response.text))



def main(domain, django_version, python_version):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser()
        domain = '{}.pythonanywhere.com'.format(username)
    sanity_checks(domain)
    virtualenv_path = create_virtualenv(domain, python_version, django_version)
    project_path = start_django_project(domain, virtualenv_path)
    update_settings_file(domain, project_path)
    run_collectstatic(virtualenv_path, project_path)
    create_webapp(domain, python_version, virtualenv_path, project_path)
    add_static_file_mappings(domain, project_path)
    wsgi_file_path = '/var/www/' + domain.replace('.', '_') + '_wsgi.py'
    update_wsgi_file(wsgi_file_path, project_path)
    reload_webapp(domain)



if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['--domain'], arguments['--django'], arguments['--python'])

