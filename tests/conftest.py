import os
import getpass
import pytest
import shutil
import subprocess
import responses
import tempfile
from unittest.mock import patch, Mock



@pytest.fixture
def mock_main_functions():
    mocks = Mock()
    patchers = []
    functions = [
        'sanity_checks',
        'create_virtualenv',
        'start_django_project',
        'update_settings_file',
        'run_collectstatic',
        'create_webapp',
        'add_static_file_mappings',
        'update_wsgi_file',
        'reload_webapp',
    ]
    for function in functions:
        mock = getattr(mocks, function)
        patcher = patch(
            'scripts.pa_start_django_webapp_with_virtualenv.{}'.format(function),
            mock
        )
        patchers.append(patcher)
        patcher.start()

    yield mocks

    for patcher in patchers:
        patcher.stop()


@pytest.fixture(scope="session")
def local_pip_cache():
    return tempfile.mkdtemp()


@pytest.fixture
def fake_home(local_pip_cache):
    tempdir = tempfile.mkdtemp()
    os.mkdir(os.path.join(tempdir, '.cache'))
    os.symlink(local_pip_cache, os.path.join(tempdir, '.cache', 'pip'))

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

