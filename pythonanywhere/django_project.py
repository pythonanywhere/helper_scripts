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
            shutil.rmtree(str(self.project_path))
        subprocess.check_call(['git', 'clone', repo, str(self.project_path)])


    def create_virtualenv(self, django_version=None, nuke=False):
        self.virtualenv.create(nuke=nuke)
        if django_version is None:
            packages = self.detect_requirements()
        elif django_version == 'latest':
            packages = 'django'
        else:
            packages = 'django=={django_version}'.format(django_version=django_version)
        self.virtualenv.pip_install(packages)


    def detect_requirements(self):
        requirements_txt = self.project_path / 'requirements.txt'
        if requirements_txt.exists():
            return '-r {resolved_requirements}'.format(resolved_requirements=requirements_txt.resolve())
        return 'django'


    def run_startproject(self, nuke):
        print(snakesay('Starting Django project'))
        if nuke and self.project_path.exists():
            shutil.rmtree(str(self.project_path))
        self.project_path.mkdir()
        subprocess.check_call([
            str(Path(self.virtualenv.path) / 'bin/django-admin.py'),
            'startproject',
            'mysite',
            str(self.project_path),
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

        with self.settings_path.open() as f:
            settings = f.read()
        new_settings = settings.replace(
            'ALLOWED_HOSTS = []',
            'ALLOWED_HOSTS = [{domain!r}]'.format(domain=self.domain)
        )
        new_settings += dedent(
            """
            MEDIA_URL = '/media/'
            STATIC_ROOT = os.path.join(BASE_DIR, 'static')
            MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
            """
        )
        with self.settings_path.open('w') as f:
            f.write(new_settings)


    def run_collectstatic(self):
        print(snakesay('Running collectstatic'))
        subprocess.check_call([
            str(Path(self.virtualenv.path) / 'bin/python'),
            str(self.manage_py_path),
            'collectstatic',
            '--noinput',
        ])


    def run_migrate(self):
        print(snakesay('Running migrate database'))
        subprocess.check_call([
            str(Path(self.virtualenv.path) / 'bin/python'),
            str(self.manage_py_path),
            'migrate',
        ])


    def update_wsgi_file(self):
        print(snakesay('Updating wsgi file at {wsgi_file_path}'.format(wsgi_file_path=self.wsgi_file_path)))
        template = (Path(__file__).parent / 'wsgi_file_template.py').open().read()
        with self.wsgi_file_path.open('w') as f:
            f.write(template.format(project=self))
