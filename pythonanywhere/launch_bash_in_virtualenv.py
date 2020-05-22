#!/usr/bin/python
# Copyright (c) 2018 PythonAnywhere LLP.
# All Rights Reserved
#

## FIXME: this file is a pre-release copy of a built-in PythonAnywhere script.
## remove once the updated version is deployed to live.

import os
import sys

HOME = os.path.expanduser('~')
TMP = '/tmp'


def write_temporary_bashrc(virtualenv_path, unique_id, source_directory):
    bashrc_path = os.path.join(HOME, '.bashrc')
    if os.path.exists(bashrc_path):
        with open(bashrc_path) as f:
            bashrc = f.read()
    else:
        bashrc = ''
    if os.path.dirname(virtualenv_path) == os.path.join(HOME, '.virtualenvs'):
        activate_script = f'workon {os.path.basename(virtualenv_path)}'
    else:
        activate_script_path = os.path.join(virtualenv_path, 'bin', 'activate')
        if not os.path.exists(activate_script_path):
            print(f'Could not find virtualenv activation script at {activate_script_path}')
            sys.exit(-1)
        with open(activate_script_path) as f:
            activate_script = f.read()

    tmprc = os.path.join(TMP, f'tmprc.{unique_id}')
    with open(tmprc, 'w') as f:
        f.write(bashrc)
        f.write('\n')
        f.write(activate_script)
        f.write('\n')
        f.write(f'cd {source_directory}\n')
        f.write('\n')
        f.write(f'rm {tmprc}')
    return tmprc


def launch_bash_in_virtualenv(virtualenv_path, unique_id, source_directory):
    tmprc = write_temporary_bashrc(virtualenv_path, unique_id, source_directory)
    os.execv('/bin/bash', ['bash', '--rcfile', tmprc, '-i'])


if __name__ == '__main__':
    launch_bash_in_virtualenv(sys.argv[2], sys.argv[1], sys.argv[3])

