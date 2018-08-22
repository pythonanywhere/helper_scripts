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
        print(snakesay('Creating virtualenv with Python{python_version}'.format(python_version=self.python_version)))
        command = 'mkvirtualenv --python=/usr/bin/python{python_version} {domain}'.format(
            python_version=self.python_version,
            domain=self.domain,
        )
        if nuke:
            command = 'rmvirtualenv {domain} && {command}'.format(
                domain=self.domain,
                command=command,
            )
        subprocess.check_call(['bash', '-c', 'source virtualenvwrapper.sh && {command}'.format(command=command)])
        return self


    def pip_install(self, packages):
        print(snakesay('Pip installing {packages} (this may take a couple of minutes)'.format(packages=packages)))
        commands = [str(self.path / 'bin/pip'), 'install'] + packages.split()
        subprocess.check_call(commands)
