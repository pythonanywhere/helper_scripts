from pathlib import Path
import shutil
import subprocess
from textwrap import dedent

from pythonanywhere.snakesay import snakesay


def _project_folder(domain):
    return Path('~/').expanduser() / domain



def start_django_project(domain, virtualenv_path, nuke):
    print(snakesay('Starting Django project'))
    target_folder = _project_folder(domain)
    if nuke:
        shutil.rmtree(target_folder)
    target_folder.mkdir()
    subprocess.check_call([
        Path(virtualenv_path) / 'bin/django-admin.py',
        'startproject',
        'mysite',
        target_folder
    ])
    return target_folder



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

