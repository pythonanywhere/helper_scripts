import os
from pathlib import Path
import subprocess

from pythonanywhere.snakesay import snakesay


def virtualenv_path(domain):
    return Path(os.environ['WORKON_HOME']) / domain


def create_virtualenv(name, python_version, packages, nuke):
    print(snakesay(f'Creating virtualenv with Python{python_version} and installing {packages}'))
    command = f'mkvirtualenv --python=/usr/bin/python{python_version} {name} && pip install {packages}'
    if nuke:
        command = f'rmvirtualenv {name} && {command}'
    subprocess.check_call(['bash', '-c', f'source virtualenvwrapper.sh && {command}'])
    return virtualenv_path(name)

