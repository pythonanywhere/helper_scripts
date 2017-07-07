import os
import subprocess

from pythonanywhere.snakesay import snakesay


def _virtualenv_path(domain):
    return os.path.join(os.environ['WORKON_HOME'], domain)


def create_virtualenv(name, python_version, django_version, nuke):
    print(snakesay(f'Creating virtualenv with Python{python_version} and Django=={django_version}'))
    pip_install = 'pip install django'
    if django_version != 'latest':
        pip_install += '==' + django_version
    command = f'mkvirtualenv --python=/usr/bin/python{python_version} {name} && {pip_install}'
    if nuke:
        command = f'rmvirtualenv {name} && {command}'
    subprocess.check_call(['bash', '-c', f'source virtualenvwrapper.sh && {command}'])
    return _virtualenv_path(name)

