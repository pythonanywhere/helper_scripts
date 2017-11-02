from pathlib import Path
import shutil
import subprocess
from textwrap import dedent
import os

from pythonanywhere.api import Webapp
from pythonanywhere.exceptions import SanityException
from pythonanywhere.snakesay import snakesay
from pythonanywhere.virtualenvs import create_virtualenv, virtualenv_path


class DjangoProject:

    def __init__(self, domain):
        self.domain = domain
        self.project_path = Path('~/').expanduser() / self.domain
        self.wsgi_file_path = '/var/www/' + domain.replace('.', '_') + '_wsgi.py'
        self.webapp = Webapp(domain)
        self.virtualenv_path = virtualenv_path(domain)


    def sanity_checks(self, nuke):
        self.webapp.sanity_checks(nuke=nuke)
        if nuke:
            return
        if self.virtualenv_path.exists():
            raise SanityException(f'You already have a virtualenv for {self.domain}.\n\nUse the --nuke option if you want to replace it.')
        if self.project_path.exists():
            raise SanityException(f'You already have a project folder at {self.project_path}.\n\nUse the --nuke option if you want to replace it.')



    def download_repo(self, repo, nuke):
        if nuke and self.project_path.exists():
            shutil.rmtree(self.project_path)
        subprocess.check_call(['git', 'clone', repo, self.project_path])


    def create_virtualenv(self, python_version, django_version=None, nuke=False):
        if django_version is None:
            packages = self.detect_django_version()
        elif django_version == 'latest':
            packages = 'django'
        else:
            packages = f'django=={django_version}'
        self.virtualenv_path = create_virtualenv(
            self.domain, python_version, packages, nuke=nuke
        )
        self.python_version = python_version


    def detect_django_version(self):
        requirements_txt = self.project_path / 'requirements.txt'
        if requirements_txt.exists():
            return f'-r {requirements_txt.resolve()}'
        return 'django'



    def run_startproject(self, nuke):
        print(snakesay('Starting Django project'))
        if nuke and self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir()
        subprocess.check_call([
            Path(self.virtualenv_path) / 'bin/django-admin.py',
            'startproject',
            'mysite',
            self.project_path
        ])


    def find_django_files(self):
        try:
            self.settings_path = next(self.project_path.glob('**/settings.py'))
        except StopIteration:
            raise SanityException('Could not find your settings.py')
        try:
            self.manage_py_path = next(self.project_path.glob('**/manage.py'))
        except StopIteration:
            raise SanityException('Could not find your manage.py')


    def update_settings_file(self):
        print(snakesay('Updating settings.py'))

        with open(self.settings_path) as f:
            settings = f.read()
        new_settings = settings.replace(
            'ALLOWED_HOSTS = []',
            f'ALLOWED_HOSTS = [{self.domain!r}]'
        )
        new_settings += dedent(
            """
            MEDIA_URL = '/media/'
            STATIC_ROOT = os.path.join(BASE_DIR, 'static')
            MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
            """
        )
        with open(self.settings_path, 'w') as f:
            f.write(new_settings)


    def run_collectstatic(self):
        print(snakesay('Running collectstatic'))
        subprocess.check_call([
            Path(self.virtualenv_path) / 'bin/python',
            self.manage_py_path,
            'collectstatic',
            '--noinput',
        ])


    def update_wsgi_file(self):
        print(snakesay(f'Updating wsgi file at {self.wsgi_file_path}'))
        template = open(Path(__file__).parent / 'wsgi_file_template.py').read()
        with open(self.wsgi_file_path, 'w') as f:
            f.write(template.format(project=self))


    def create_webapp(self, nuke):
        self.webapp.create(self.python_version, self.virtualenv_path, self.project_path, nuke=nuke)


    def add_static_file_mappings(self):
        self.webapp.add_default_static_files_mappings(self.project_path)


