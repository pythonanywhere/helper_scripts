from pathlib import Path
import uuid

from pythonanywhere.api.webapp import Webapp
from pythonanywhere.exceptions import SanityException
from pythonanywhere.virtualenvs import Virtualenv
from pythonanywhere.launch_bash_in_virtualenv import launch_bash_in_virtualenv
from pythonanywhere.snakesay import snakesay


class Project:
    def __init__(self, domain, python_version):
        self.domain = domain
        self.python_version = python_version
        self.project_path = Path(f'~/{domain}').expanduser()
        self.virtualenv = Virtualenv(self.domain, self.python_version)
        self.wsgi_file_path = Path(
            f"/var/www/{domain.replace('.', '_')}_wsgi.py"
        )
        self.webapp = Webapp(domain)


    def sanity_checks(self, nuke):
        self.webapp.sanity_checks(nuke=nuke)
        if nuke:
            return
        if self.virtualenv.path.exists():
            raise SanityException(
                "You already have a virtualenv for {domain}.\n\n"
                "Use the --nuke option if you want to replace it.".format(
                    domain=self.domain
                )
            )
        if self.project_path.exists():
            raise SanityException(
                "You already have a project folder at {project_path}.\n\n"
                "Use the --nuke option if you want to replace it.".format(
                    project_path=self.project_path
                )
            )


    def create_webapp(self, nuke):
        self.webapp.create(self.python_version, self.virtualenv.path, self.project_path, nuke=nuke)


    def add_static_file_mappings(self):
        self.webapp.add_default_static_files_mappings(self.project_path)


    def start_bash(self):
        print(snakesay('Starting Bash shell with activated virtualenv in project directory.  Press Ctrl+D to exit.'))
        unique_id = str(uuid.uuid4())
        launch_bash_in_virtualenv(self.virtualenv.path, unique_id, self.project_path)
