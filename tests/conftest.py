import os
import pytest
import shutil
import subprocess
import tempfile

@pytest.fixture
def virtualenvs_folder():
    virtualenvs_path = os.path.expanduser('~/.virtualenvs')
    if not os.path.exists(virtualenvs_path):
        raise Exception('assumes use of virtualenvwrapper')
    old_virtualenvs = os.listdir(virtualenvs_path)

    yield virtualenvs_path

    latest_virtualenvs = os.listdir(virtualenvs_path)
    for new_venv in set(latest_virtualenvs) - set(old_virtualenvs):
        shutil.rmtree(os.path.join(virtualenvs_path, new_venv))


@pytest.fixture
def cleanup_home():
    home = os.path.expanduser('~')
    old_home_contents = os.listdir(home)
    yield
    new_home_contents = os.listdir(home)
    for new_dir in set(new_home_contents) - set(old_home_contents):
        if new_dir.endswith('.test.com'):
            shutil.rmtree(os.path.join(home, new_dir))


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

