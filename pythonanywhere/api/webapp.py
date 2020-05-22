import getpass
import os
from pathlib import Path
from textwrap import dedent

from dateutil.parser import parse

from pythonanywhere.api.base import PYTHON_VERSIONS, call_api, get_api_endpoint
from pythonanywhere.exceptions import SanityException
from pythonanywhere.snakesay import snakesay


class Webapp:
    def __init__(self, domain):
        self.domain = domain

    def __eq__(self, other):
        return self.domain == other.domain

    def sanity_checks(self, nuke):
        print(snakesay("Running API sanity checks"))
        token = os.environ.get("API_TOKEN")
        if not token:
            raise SanityException(
                dedent(
                    """
                Could not find your API token.
                You may need to create it on the Accounts page?
                You will also need to close this console and open a new one once you've done that.
                """
                )
            )

        if nuke:
            return

        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + "/"
        response = call_api(url, "get")
        if response.status_code == 200:
            raise SanityException(
                "You already have a webapp for {domain}.\n\nUse the --nuke option if you want to replace it.".format(
                    domain=self.domain
                )
            )

    def create(self, python_version, virtualenv_path, project_path, nuke):
        print(snakesay("Creating web app via API"))
        if nuke:
            webapp_url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + "/"
            call_api(webapp_url, "delete")
        post_url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
        patch_url = post_url + self.domain + "/"
        response = call_api(
            post_url, "post", data={"domain_name": self.domain, "python_version": PYTHON_VERSIONS[python_version]}
        )
        if not response.ok or response.json().get("status") == "ERROR":
            raise Exception(
                f"POST to create webapp via API failed, got {response}:{response.text}"
            )
        response = call_api(
            patch_url, "patch", data={"virtualenv_path": virtualenv_path, "source_directory": project_path}
        )
        if not response.ok:
            raise Exception(
                "PATCH to set virtualenv path and source directory via API failed,"
                "got {response}:{response_text}".format(response=response, response_text=response.text)
            )

    def add_default_static_files_mappings(self, project_path):
        print(snakesay("Adding static files mappings for /static/ and /media/"))

        url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + "/static_files/"
        )
        call_api(url, "post", json=dict(url="/static/", path=str(Path(project_path) / "static")))
        call_api(url, "post", json=dict(url="/media/", path=str(Path(project_path) / "media")))

    def reload(self):
        print(snakesay(f"Reloading {self.domain} via API"))
        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + "/reload/"
        response = call_api(url, "post")
        if not response.ok:
            if response.status_code == 409 and response.json()["error"] == "cname_error":
                print(
                    snakesay(
                        dedent("""
                            Could not find a CNAME for your website.  If you're using an A record,
                            CloudFlare, or some other way of pointing your domain at PythonAnywhere
                            then that should not be a problem.  If you're not, you should double-check
                            your DNS setup.
                        """)
                    )
                )
                return
            raise Exception(
                f"POST to reload webapp via API failed, got {response}:{response.text}"
            )

    def set_ssl(self, certificate, private_key):
        print(snakesay(f"Setting up SSL for {self.domain} via API"))
        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + "/ssl/"
        response = call_api(url, "post", json={"cert": certificate, "private_key": private_key})
        if not response.ok:
            raise Exception(
                dedent(
                    """
                    POST to set SSL details via API failed, got {response}:{response_text}
                    If you just created an API token, you need to set the API_TOKEN environment variable or start a
                    new console.  Also you need to have setup a `{domain}` PythonAnywhere webapp for this to work.
                    """
                ).format(response=response, response_text=response.text, domain=self.domain)
            )

    def get_ssl_info(self):
        url = get_api_endpoint().format(username=getpass.getuser(), flavor="webapps") + self.domain + "/ssl/"
        response = call_api(url, "get")
        if not response.ok:
            raise Exception(
                f"GET SSL details via API failed, got {response}:{response.text}"
            )

        result = response.json()
        result["not_after"] = parse(result["not_after"])
        return result

    def delete_log(self, log_type, index=0):
        if index:
            print(
                snakesay(
                    "Deleting old (archive number {index}) {type} log file for {domain} via API".format(
                        index=index, type=log_type, domain=self.domain
                    )
                )
            )
        else:
            print(
                snakesay(
                    f"Deleting current {log_type} log file for {self.domain} via API"
                )
            )

        if index == 1:
            url = get_api_endpoint().format(
                username=getpass.getuser(), flavor="files"
            ) + f"path/var/log/{self.domain}.{log_type}.log.1/"
        elif index > 1:
            url = get_api_endpoint().format(
                username=getpass.getuser(), flavor="files"
            ) + f"path/var/log/{self.domain}.{log_type}.log.{index}.gz/"
        else:
            url = get_api_endpoint().format(
                username=getpass.getuser(), flavor="files"
            ) + f"path/var/log/{self.domain}.{log_type}.log/"
        response = call_api(url, "delete")
        if not response.ok:
            raise Exception(
                f"DELETE log file via API failed, got {response}:{response.text}"
            )

    def get_log_info(self):
        url = get_api_endpoint().format(username=getpass.getuser(), flavor="files") + "tree/?path=/var/log/"
        response = call_api(url, "get")
        if not response.ok:
            raise Exception(
                f"GET log files info via API failed, got {response}:{response.text}"
            )
        file_list = response.json()
        log_types = ["access", "error", "server"]
        logs = {"access": [], "error": [], "server": []}
        log_prefix = f"/var/log/{self.domain}."
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
