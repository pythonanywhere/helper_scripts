from textwrap import dedent
import getpass
import os
from pathlib import Path
import requests

from pythonanywhere.exceptions import SanityException
from pythonanywhere.snakesay import snakesay


PYTHON_VERSIONS = {
    '2.7': 'python27',
    '3.4': 'python34',
    '3.5': 'python35',
    '3.6': 'python36',
}



class AuthenticationError(Exception):
    pass


def get_api_endpoint():
    domain = os.environ.get('PYTHONANYWHERE_DOMAIN', 'pythonanywhere.com')
    return f'https://www.{domain}/api/v0/user/{{username}}/webapps/'


def call_api(url, method, **kwargs):
    token = os.environ['API_TOKEN']
    insecure = os.environ.get('PYTHONANYWHERE_INSECURE_API') == 'true'
    response = requests.request(
        method=method,
        url=url,
        headers={'Authorization': f'Token {token}'},
        verify=not insecure,
        **kwargs
    )
    if response.status_code == 401:
        print(response, response.text)
        raise AuthenticationError(f'Authentication error {response.status_code} calling API: {response.text}')
    return response



class Webapp:

    def __init__(self, domain):
        self.domain = domain


    def __eq__(self, other):
        return self.domain == other.domain


    def sanity_checks(self, nuke):
        print(snakesay('Running API sanity checks'))
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

        url = get_api_endpoint().format(username=getpass.getuser()) + self.domain + '/'
        response = call_api(url, 'get')
        if response.status_code == 200:
            raise SanityException(f'You already have a webapp for {self.domain}.\n\nUse the --nuke option if you want to replace it.')



    def create(self, python_version, virtualenv_path, project_path, nuke):
        print(snakesay('Creating web app via API'))
        if nuke:
            webapp_url = get_api_endpoint().format(username=getpass.getuser()) + self.domain + '/'
            call_api(webapp_url, 'delete')
        post_url = get_api_endpoint().format(username=getpass.getuser())
        patch_url = post_url + self.domain + '/'
        response = call_api(post_url, 'post', data={
            'domain_name': self.domain, 'python_version': PYTHON_VERSIONS[python_version]},
        )
        if not response.ok or response.json().get('status') == 'ERROR':
            raise Exception(f'POST to create webapp via API failed, got {response}:{response.text}')
        response = call_api(patch_url, 'patch', data={'virtualenv_path': virtualenv_path, 'source_directory': project_path})
        if not response.ok:
            raise Exception(f'PATCH to set virtualenv path and source directory via API failed, got {response}:{response.text}')



    def add_default_static_files_mappings(self, project_path):
        print(snakesay('Adding static files mappings for /static/ and /media/'))

        url = get_api_endpoint().format(username=getpass.getuser()) + self.domain + '/static_files/'
        call_api(url, 'post', json=dict(
            url='/static/', path=str(Path(project_path) / 'static'),
        ))
        call_api(url, 'post', json=dict(
            url='/media/', path=str(Path(project_path) / 'media'),
        ))



    def reload(self):
        print(snakesay(f'Reloading {self.domain} via API'))
        url = get_api_endpoint().format(username=getpass.getuser()) + self.domain + '/reload/'
        response = call_api(url, 'post')
        if not response.ok:
            raise Exception(f'POST to reload webapp via API failed, got {response}:{response.text}')

