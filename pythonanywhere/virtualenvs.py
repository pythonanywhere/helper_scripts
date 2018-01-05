import os
from pathlib import Path
import subprocess

from pythonanywhere.snakesay import snakesay


class Virtualenv:

    def __init__(self, domain, python_version):
        self.domain = domain
        self.python_version = python_version
        self.path = Path(os.environ['WORKON_HOME']) / domain

    def __eq__(self, other):
        return self.domain == other.domain and self.python_version == other.python_version


    def create(self, nuke):
        command = f'mkvirtualenv --python=/usr/bin/python{self.python_version} {self.domain}'
        if nuke:
            command = f'rmvirtualenv {self.domain} && {command}'
        subprocess.check_call(['bash', '-c', f'source virtualenvwrapper.sh && {command}'])


    def pip_install(self, packages):
        commands = [str(self.path / 'bin/pip'), 'install'] + packages.split()
        subprocess.check_call(commands)



def create_virtualenv(name, python_version, packages, nuke):
    print(snakesay(f'Creating virtualenv with Python{python_version} and installing {packages}'))
    v = Virtualenv(name, python_version)
    v.create(nuke=nuke)
    v.pip_install(packages)
    return v.path

