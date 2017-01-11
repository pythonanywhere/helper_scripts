import os
import getpass
import pytest
import shutil
import subprocess
import tempfile

@pytest.fixture
def fake_home():
    tempdir = tempfile.mkdtemp()
    old_home = os.environ['HOME']
    old_home_contents = os.listdir(old_home)

    os.environ['HOME'] = tempdir
    yield tempdir
    os.environ['HOME'] = old_home
    shutil.rmtree(tempdir)

    new_home_contents = os.listdir(old_home)
    new_stuff = set(new_home_contents) - set(old_home_contents)
    if new_stuff:
        raise Exception('home mocking failed somewehere: {}, {}'.format(
            new_stuff, tempdir
        ))


@pytest.fixture
def virtualenvs_folder():
    actual_virtualenvs = '/home/{}/.virtualenvs'.format(getpass.getuser())
    old_virtualenvs = os.listdir(actual_virtualenvs)

    tempdir = tempfile.mkdtemp()
    old_workon = os.environ['WORKON_HOME']
    os.environ['WORKON_HOME'] = tempdir
    yield tempdir
    os.environ['WORKON_HOME'] = old_workon
    shutil.rmtree(tempdir)

    latest_virtualenvs = os.listdir(actual_virtualenvs)
    new_envs = set(latest_virtualenvs) - set(old_virtualenvs)
    if new_envs:
        raise Exception('virtualenvs path mocking failed somewehere: {}, {}'.format(
            new_envs, tempdir
        ))


@pytest.fixture
def test_virtualenv(virtualenvs_folder):
    virtualenv_name = os.path.basename(tempfile.NamedTemporaryFile().name)
    subprocess.check_output([
        'bash', '-c',
        'source virtualenvwrapper.sh && mkvirtualenv {} && pip install django==1.8.7'.format(
            virtualenv_name
        )
    ])
    return os.path.join(virtualenvs_folder, virtualenv_name)

