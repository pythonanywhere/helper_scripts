import os
from getpass import getuser
import pytest
from pathlib import Path
import shutil
import subprocess
import responses
import tempfile
from unittest.mock import patch, Mock


def _get_temp_dir():
    return Path(tempfile.mkdtemp())


@pytest.fixture(scope="session")
def local_pip_cache(request):
    previous_cache = request.config.cache.get('pythonanywhere/pip-cache', None)
    if previous_cache:
        return Path(previous_cache)
    else:
        new_cache = _get_temp_dir()
        request.config.cache.set('pythonanywhere/pip-cache', str(new_cache))
        return new_cache


@pytest.fixture
def fake_home(local_pip_cache):
    tempdir = _get_temp_dir()
    cache_dir = tempdir / '.cache'
    cache_dir.mkdir()
    (cache_dir / 'pip').symlink_to(local_pip_cache)

    old_home = os.environ['HOME']
    old_home_contents = set(Path(old_home).iterdir())

    os.environ['HOME'] = str(tempdir)
    yield tempdir
    os.environ['HOME'] = old_home
    shutil.rmtree(tempdir)

    new_stuff = set(Path(old_home).iterdir()) - old_home_contents
    if new_stuff:
        raise Exception('home mocking failed somewehere: {}, {}'.format(
            new_stuff, tempdir
        ))


@pytest.fixture
def virtualenvs_folder():
    actual_virtualenvs = Path(f'/home/{getuser()}/.virtualenvs')
    old_virtualenvs = set(Path(actual_virtualenvs).iterdir())

    tempdir = _get_temp_dir()
    old_workon = os.environ['WORKON_HOME']
    os.environ['WORKON_HOME'] = str(tempdir)
    yield tempdir
    os.environ['WORKON_HOME'] = old_workon
    shutil.rmtree(tempdir)

    new_envs = set(actual_virtualenvs.iterdir()) - set(old_virtualenvs)
    if new_envs:
        raise Exception('virtualenvs path mocking failed somewehere: {}, {}'.format(
            new_envs, tempdir
        ))


@pytest.fixture
def test_virtualenv(virtualenvs_folder):
    virtualenv_name = Path(tempfile.NamedTemporaryFile().name).name
    subprocess.check_output([
        'bash', '-c',
        'source virtualenvwrapper.sh && mkvirtualenv {} && pip install django==1.8.7'.format(
            virtualenv_name
        )
    ])
    return virtualenvs_folder / virtualenv_name




@pytest.fixture
def mock_subprocess():
    mock = Mock()
    with patch('subprocess.check_call') as mock_check_call:
        mock.check_call = mock_check_call
        with patch('subprocess.check_output') as mock_check_output:
            mock.check_output = mock_check_output
            yield mock



@pytest.fixture
def api_responses():
    with responses.RequestsMock() as r:
        yield r



@pytest.fixture(scope="function")
def api_token():
    old_token = os.environ.get('API_TOKEN')
    token = 'sekrit.token'
    os.environ['API_TOKEN'] = token

    yield token

    if old_token is None:
        del os.environ['API_TOKEN']
    else:
        os.environ['API_TOKEN'] = old_token


@pytest.fixture(scope="function")
def no_api_token():
    if 'API_TOKEN' not in os.environ:
        yield

    else:
        old_token = os.environ['API_TOKEN']
        del os.environ['API_TOKEN']
        yield
        os.environ['API_TOKEN'] = old_token

