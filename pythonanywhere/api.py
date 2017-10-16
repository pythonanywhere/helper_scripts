import getpass
import os
from pathlib import Path
import requests

from pythonanywhere.snakesay import snakesay


API_ENDPOINT = 'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/'
PYTHON_VERSIONS = {
    '2.7': 'python27',
    '3.4': 'python34',
    '3.5': 'python35',
    '3.6': 'python36',
}



class AuthenticationError(Exception):
    pass



class Webapp:
    def __init__(self, domain):
        self.domain = domain



def call_api(url, method, **kwargs):
    token = os.environ['API_TOKEN']
    response = requests.request(
        method=method,
        url=url,
        headers={'Authorization': f'Token {token}'},
        **kwargs
    )
    if response.status_code == 401:
        print(response, response.text)
        raise AuthenticationError(f'Authentication error {response.status_code} calling API: {response.text}')
    return response



def create_webapp(domain, python_version, virtualenv_path, project_path, nuke):
    print(snakesay('Creating web app via API'))
    if nuke:
        webapp_url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/'
        call_api(webapp_url, 'delete')
    post_url = API_ENDPOINT.format(username=getpass.getuser())
    patch_url = post_url + domain + '/'
    response = call_api(post_url, 'post', data={
        'domain_name': domain, 'python_version': PYTHON_VERSIONS[python_version]},
    )
    if not response.ok or response.json().get('status') == 'ERROR':
        raise Exception(f'POST to create webapp via API failed, got {response}:{response.text}')
    response = call_api(patch_url, 'patch', data={'virtualenv_path': virtualenv_path})
    if not response.ok:
        raise Exception(f'PATCH to set virtualenv path via API failed, got {response}:{response.text}')



def add_static_file_mappings(domain, project_path):
    print(snakesay('Adding static files mappings for /static/ and /media/'))

    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/static_files/'
    call_api(url, 'post', json=dict(
        url='/static/', path=str(Path(project_path) / 'static'),
    ))
    call_api(url, 'post', json=dict(
        url='/media/', path=str(Path(project_path) / 'media'),
    ))



def reload_webapp(domain):
    print(snakesay(f'Reloading {domain} via API'))
    url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/reload/'
    response = call_api(url, 'post')
    if not response.ok:
        raise Exception(f'POST to reload webapp via API failed, got {response}:{response.text}')

