from pathlib import Path
import shutil
import subprocess
from textwrap import dedent

from pythonanywhere.exceptions import SanityException
from pythonanywhere.snakesay import snakesay
from .project import Project


class DjangoProject(Project):

    def download_repo(self, repo, nuke):
        if nuke and self.project_path.exists():
            shutil.rmtree(self.project_path)
        subprocess.check_call(['git', 'clone', repo, self.project_path])


    def create_virtualenv(self, django_version=None, nuke=False):
        self.virtualenv.create(nuke=nuke)
        if django_version is None:
            packages = self.detect_requirements()
        elif django_version == 'latest':
            packages = 'django'
        else:
            packages = f'django=={django_version}'
        self.virtualenv.pip_install(packages)


    def detect_requirements(self):
        requirements_txt = self.project_path / 'requirements.txt'
        if requirements_txt.exists():
            return f'-r {requirements_txt.resolve()}'
        return 'django<2'  # FIXME: this is a hack for djangogirls while they update to 2.x


    def run_startproject(self, nuke):
        print(snakesay('Starting Django project'))
        if nuke and self.project_path.exists():
            shutil.rmtree(self.project_path)
        self.project_path.mkdir()
        subprocess.check_call([
            Path(self.virtualenv.path) / 'bin/django-admin.py',
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
            Path(self.virtualenv.path) / 'bin/python',
            self.manage_py_path,
            'collectstatic',
            '--noinput',
        ])


    def run_migrate(self):
        print(snakesay('Running migrate database'))
        subprocess.check_call([
            Path(self.virtualenv.path) / 'bin/python',
            self.manage_py_path,
            'migrate',
        ])


    def update_wsgi_file(self):
        print(snakesay(f'Updating wsgi file at {self.wsgi_file_path}'))
        template = open(Path(__file__).parent / 'wsgi_file_template.py').read()
        with open(self.wsgi_file_path, 'w') as f:
            f.write(template.format(project=self))

