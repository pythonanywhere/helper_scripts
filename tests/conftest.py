import os
import pytest
import shutil

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

