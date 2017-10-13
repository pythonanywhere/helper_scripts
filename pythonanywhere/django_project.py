from pathlib import Path
import shutil
import subprocess
from textwrap import dedent

from pythonanywhere.snakesay import snakesay


class DjangoProject:
    def __init__(self, domain, virtualenv_path):
        self.domain = domain
        self.virtualenv_path = virtualenv_path
        self.project_folder = Path('~/').expanduser() / self.domain


    def run_startproject(self, nuke):
        print(snakesay('Starting Django project'))
        if nuke:
            shutil.rmtree(self.project_folder)
        self.project_folder.mkdir()
        subprocess.check_call([
            Path(self.virtualenv_path) / 'bin/django-admin.py',
            'startproject',
            'mysite',
            self.project_folder
        ])




def start_django_project(domain, virtualenv_path, nuke):
    project = DjangoProject(domain, virtualenv_path)
    project.run_startproject(nuke=nuke)
    return project.project_folder




def run_collectstatic(virtualenv_path, target_folder):
    print(snakesay('Running collectstatic'))

    subprocess.check_call([
        Path(virtualenv_path) / 'bin/python',
        target_folder / 'manage.py',
        'collectstatic',
        '--noinput',
    ])



def update_settings_file(domain, project_path):
    print(snakesay('Updating settings.py'))

    with open(project_path / 'mysite/settings.py') as f:
        settings = f.read()
    new_settings = settings.replace(
        'ALLOWED_HOSTS = []',
        f'ALLOWED_HOSTS = [{domain!r}]'
    )
    new_settings += dedent(
        """
        MEDIA_URL = '/media/'
        STATIC_ROOT = os.path.join(BASE_DIR, 'static')
        MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
        """
    )
    with open(project_path / 'mysite' / 'settings.py', 'w') as f:
        f.write(new_settings)



def update_wsgi_file(wsgi_file_path, project_path):
    print(snakesay(f'Updating wsgi file at {wsgi_file_path}'))

    template = open(Path(__file__).parent / 'wsgi_file_template.py').read()
    with open(wsgi_file_path, 'w') as f:
        f.write(template.format(project_path=project_path))

