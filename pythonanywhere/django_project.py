from pathlib import Path
import shutil
import subprocess
from textwrap import dedent

from pythonanywhere.snakesay import snakesay
from pythonanywhere.virtualenvs import create_virtualenv


class DjangoProject:

    def __init__(self, domain):
        self.domain = domain
        self.project_path = Path('~/').expanduser() / self.domain
        self.wsgi_file_path = '/var/www/' + domain.replace('.', '_') + '_wsgi.py'


    def create_virtualenv(self):
        create_virtualenv(self.domain, self.python_version, 'django', nuke=False)



    def run_startproject(self, nuke):
        print(snakesay('Starting Django project'))
        if nuke:
            shutil.rmtree(self.project_path)
        self.project_path.mkdir()
        subprocess.check_call([
            Path(self.virtualenv_path) / 'bin/django-admin.py',
            'startproject',
            'mysite',
            self.project_path
        ])


    def update_settings_file(self):
        print(snakesay('Updating settings.py'))

        with open(self.project_path / 'mysite/settings.py') as f:
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
        with open(self.project_path / 'mysite' / 'settings.py', 'w') as f:
            f.write(new_settings)


    def run_collectstatic(self):
        print(snakesay('Running collectstatic'))
        subprocess.check_call([
            Path(self.virtualenv_path) / 'bin/python',
            self.project_path / 'manage.py',
            'collectstatic',
            '--noinput',
        ])


    def update_wsgi_file(self):
        print(snakesay(f'Updating wsgi file at {self.wsgi_file_path}'))
        template = open(Path(__file__).parent / 'wsgi_file_template.py').read()
        with open(self.wsgi_file_path, 'w') as f:
            f.write(template.format(project_path=self.project_path))

