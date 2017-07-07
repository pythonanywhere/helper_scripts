import getpass
import os
from textwrap import dedent

from pythonanywhere.snakesay import snakesay
from pythonanywhere.api import API_ENDPOINT, call_api
from pythonanywhere.virtualenvs import _virtualenv_path
from pythonanywhere.django_project import _project_folder


class SanityException(Exception):
    pass


def sanity_checks(domain, nuke):
    print(snakesay('Running sanity checks'))
    token = os.environ.get('API_TOKEN')
    if not token:
        raise SanityException(dedent(
            '''
            Could not find your API token.
            You may need to create it on the Accounts page?
            You will also need to close this console and open a new one once you've done that.
            '''
        ))

    if nuke:
        return
    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/'
    response = call_api(url, 'get')
    if response.status_code == 200:
        raise SanityException(f'You already have a webapp for {domain}.\n\nUse the --nuke option if you want to replace it.')
    if os.path.exists(_virtualenv_path(domain)):
        raise SanityException(f'You already have a virtualenv for {domain}.\n\nUse the --nuke option if you want to replace it.')
    project_folder = _project_folder(domain)
    if os.path.exists(project_folder):
        raise SanityException(f'You already have a project folder at {project_folder}.\n\nUse the --nuke option if you want to replace it.')

