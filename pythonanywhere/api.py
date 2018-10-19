import getpass
import os
import requests
from datetime import datetime
from textwrap import dedent
from pathlib import Path

from pythonanywhere.exceptions import SanityException
from pythonanywhere.snakesay import snakesay


PYTHON_VERSIONS = {
    '2.7': 'python27',
    '3.4': 'python34',
    '3.5': 'python35',
    '3.6': 'python36',
    '3.7': 'python37',
}



class AuthenticationError(Exception):
    pass


class NoTokenError(Exception):
    pass


def get_api_endpoint():
    domain = os.environ.get('PYTHONANYWHERE_DOMAIN', 'pythonanywhere.com')
    return 'https://www.{domain}/api/v0/user/{{username}}/{{flavor}}/'.format(domain=domain)


def call_api(url, method, **kwargs):
    token = os.environ.get('API_TOKEN')
    if token is None:
        raise NoTokenError(
            "Oops, you don't seem to have an API token.  "
            "Please go to the 'Account' page on PythonAnywhere, then to the 'API Token' "
            "tab.  Click the 'Create a new API token' button to create the token, then "
            "start a new console and try running this script again."
        )
    insecure = os.environ.get('PYTHONANYWHERE_INSECURE_API') == 'true'
    response = requests.request(
        method=method,
        url=url,
        headers={'Authorization': 'Token {token}'.format(token=token)},
        verify=not insecure,
        **kwargs
    )
    if response.status_code == 401:
        print(response, response.text)
        raise AuthenticationError(
            'Authentication error {status_code} calling API: {response_text}'.format(
                status_code=response.status_code,
                response_text=response.text,
            )
        )
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

        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + '/'
        response = call_api(url, 'get')
        if response.status_code == 200:
            raise SanityException(
                'You already have a webapp for {domain}.\n\nUse the --nuke option if you want to replace it.'.format(
                    domain=self.domain
                )
            )



    def create(self, python_version, virtualenv_path, project_path, nuke):
        print(snakesay('Creating web app via API'))
        if nuke:
            webapp_url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + '/'
            call_api(webapp_url, 'delete')
        post_url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
        patch_url = post_url + self.domain + '/'
        response = call_api(post_url, 'post', data={
            'domain_name': self.domain, 'python_version': PYTHON_VERSIONS[python_version]},
        )
        if not response.ok or response.json().get('status') == 'ERROR':
            raise Exception(
                'POST to create webapp via API failed, got {response}:{response_text}'.format(
                    response=response,
                    response_text=response.text,
                )
            )
        response = call_api(
            patch_url, 'patch',
            data={'virtualenv_path': virtualenv_path, 'source_directory': project_path}
        )
        if not response.ok:
            raise Exception(
                "PATCH to set virtualenv path and source directory via API failed,"
                "got {response}:{response_text}".format(
                    response=response,
                    response_text=response.text,
                )
            )



    def add_default_static_files_mappings(self, project_path):
        print(snakesay('Adding static files mappings for /static/ and /media/'))

        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + '/static_files/'
        call_api(url, 'post', json=dict(
            url='/static/', path=str(Path(project_path) / 'static'),
        ))
        call_api(url, 'post', json=dict(
            url='/media/', path=str(Path(project_path) / 'media'),
        ))



    def reload(self):
        print(snakesay('Reloading {domain} via API'.format(domain=self.domain)))
        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + '/reload/'
        response = call_api(url, 'post')
        if not response.ok:
            raise Exception(
                'POST to reload webapp via API failed, got {response}:{response_text}'.format(
                    response=response,
                    response_text=response.text,
                )
            )


    def set_ssl(self, certificate, private_key):
        print(snakesay('Setting up SSL for {domain} via API'.format(domain=self.domain)))
        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + '/ssl/'
        response = call_api(
            url, 'post',
            json={'cert': certificate, 'private_key': private_key}
        )
        if not response.ok:
            raise Exception(
                'POST to set SSL details via API failed, got {response}:{response_text}'.format(
                    response=response,
                    response_text=response.text,
                )
            )


    def get_ssl_info(self):
        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + '/ssl/'
        response = call_api(url, 'get')
        if not response.ok:
            raise Exception(
                'GET SSL details via API failed, got {response}:{response_text}'.format(
                    response=response,
                    response_text=response.text,
                )
            )

        result = response.json()
        result["not_after"] = datetime.strptime(result["not_after"], "%Y%m%dT%H%M%SZ")
        return result

    def delete_log(self, log_type, index=0):
        if index:
            print(snakesay(
                'Deleting old (archive number {index}) {type} log file for {domain} via API'.format(index=index,
                                                                                                    type=log_type,
                                                                                                    domain=self.domain)))
        else:
            print(snakesay(
                'Deleting current {type} log file for {domain} via API'.format(type=log_type, domain=self.domain)))

        if index == 1:
            url = get_api_endpoint().format(username=getpass.getuser(), flavor="files") + "path/var/log/{domain}.{type}.log.1/".format(
                domain=self.domain, type=log_type)
        elif index > 1:
            url = get_api_endpoint().format(
                username=getpass.getuser(), flavor="files") + "path/var/log/{domain}.{type}.log.{index}.gz/".format(
                domain=self.domain, type=log_type, index=index)
        else:
            url = get_api_endpoint().format(username=getpass.getuser(), flavor="files") + "path/var/log/{domain}.{type}.log/".format(
                domain=self.domain, type=log_type)
        response = call_api(url, "delete")
        if not response.ok:
            raise Exception(
                "DELETE log file via API failed, got {response}:{response_text}".format(
                    response=response,
                    response_text=response.text,
                )
            )

    def get_log_info(self):
        url = get_api_endpoint().format(username=getpass.getuser(),
                                        flavor="files") + "tree/?path=/var/log/"
        response = call_api(url, "get")
        if not response.ok:
            raise Exception(
                "GET log files info via API failed, got {response}:{response_text}".format(
                    response=response,
                    response_text=response.text,
                )
            )
        file_list = response.json()
        log_types = ["access", "error", "server"]
        logs = {"access": [], "error": [], "server": []}
        log_prefix = "/var/log/{domain}.".format(domain=self.domain)
        for file_name in file_list:
            if type(file_name) == str and file_name.startswith(log_prefix):
                log = file_name[len(log_prefix):].split(".")
                if log[0] in log_types:
                    log_type = log[0]
                    if log[-1] == "log":
                        log_index = 0
                    elif log[-1] == "1":
                        log_index = 1
                    elif log[-1] == "gz":
                        log_index = int(log[-2])
                    else:
                        continue
                    logs[log_type].append(log_index)
        return logs
