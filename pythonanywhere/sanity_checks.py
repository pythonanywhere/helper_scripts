import getpass
import os
from textwrap import dedent

from pythonanywhere.api import API_ENDPOINT, call_api
from pythonanywhere.django_project import DjangoProject
from pythonanywhere.exceptions import SanityException
from pythonanywhere.snakesay import snakesay
from pythonanywhere.virtualenvs import virtualenv_path



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
    if virtualenv_path(domain).exists():
        raise SanityException(f'You already have a virtualenv for {domain}.\n\nUse the --nuke option if you want to replace it.')
    project = DjangoProject(domain)  # TODO: make non-django-specific parent class
    if project.project_path.exists():
        raise SanityException(f'You already have a project folder at {project.project_path}.\n\nUse the --nuke option if you want to replace it.')

