import os
import shutil
import tempfile
from getpass import getuser
from pathlib import Path
from platform import python_version
from unittest.mock import Mock, patch

import psutil
import pytest

import responses


def _get_temp_dir():
    return Path(tempfile.mkdtemp())


@pytest.fixture(scope="session")
def local_pip_cache(request):
    previous_cache = request.config.cache.get("pythonanywhere/pip-cache", None)
    if previous_cache:
        return Path(previous_cache)
    else:
        new_cache = _get_temp_dir()
        request.config.cache.set("pythonanywhere/pip-cache", str(new_cache))
        return new_cache


@pytest.fixture
def fake_home(local_pip_cache):
    tempdir = _get_temp_dir()
    cache_dir = tempdir / ".cache"
    cache_dir.mkdir()
    (cache_dir / "pip").symlink_to(local_pip_cache)

    old_home = os.environ["HOME"]
    old_home_contents = set(Path(old_home).iterdir())

    os.environ["HOME"] = str(tempdir)
    yield tempdir
    os.environ["HOME"] = old_home
    shutil.rmtree(str(tempdir), ignore_errors=True)

    new_stuff = set(Path(old_home).iterdir()) - old_home_contents
    if new_stuff:
        raise Exception(f"home mocking failed somewehere: {new_stuff}, {tempdir}")


@pytest.fixture
def virtualenvs_folder():
    actual_virtualenvs = Path(f"/home/{getuser()}/.virtualenvs")
    if actual_virtualenvs.is_dir():
        old_virtualenvs = set(Path(actual_virtualenvs).iterdir())
    else:
        old_virtualenvs = {}

    tempdir = _get_temp_dir()
    old_workon = os.environ.get("WORKON_HOME")
    os.environ["WORKON_HOME"] = str(tempdir)
    yield tempdir
    if old_workon:
        os.environ["WORKON_HOME"] = old_workon
    else:
        del os.environ["WORKON_HOME"]
    shutil.rmtree(str(tempdir), ignore_errors=True)

    if actual_virtualenvs.is_dir():
        new_envs = set(actual_virtualenvs.iterdir()) - set(old_virtualenvs)
        if new_envs:
            raise Exception(f"virtualenvs path mocking failed somewehere: {new_envs}, {tempdir}")


@pytest.fixture
def mock_subprocess():
    mock = Mock()
    with patch("subprocess.check_call") as mock_check_call:
        mock.check_call = mock_check_call
        with patch("subprocess.check_output") as mock_check_output:
            mock.check_output = mock_check_output
            yield mock


@pytest.fixture
def api_responses(monkeypatch):
    with responses.RequestsMock() as r:
        yield r


@pytest.fixture(scope="function")
def api_token():
    old_token = os.environ.get("API_TOKEN")
    token = "sekrit.token"
    os.environ["API_TOKEN"] = token

    yield token

    if old_token is None:
        del os.environ["API_TOKEN"]
    else:
        os.environ["API_TOKEN"] = old_token


@pytest.fixture(scope="function")
def no_api_token():
    if "API_TOKEN" not in os.environ:
        yield

    else:
        old_token = os.environ["API_TOKEN"]
        del os.environ["API_TOKEN"]
        yield
        os.environ["API_TOKEN"] = old_token


@pytest.fixture
def process_killer():
    to_kill = []
    yield to_kill
    for p in to_kill:
        for child in psutil.Process(p.pid).children():
            child.kill()
        p.kill()

@pytest.fixture
def running_python_version():
    return ".".join(python_version().split(".")[:2])

@pytest.fixture
def new_django_version(running_python_version):
    if running_python_version in ["3.10", "3.11", "3.12", "3.13"]:
        return "5.1.3"
    else:
        return "4.2.16"

@pytest.fixture
def old_django_version(running_python_version):
    if running_python_version in ["3.10", "3.11", "3.12", "3.13"]:
        return "5.1.2"
    else:
        return "4.2.15"
