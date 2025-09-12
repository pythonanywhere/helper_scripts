from unittest.mock import call, patch, Mock
import pytest
from pathlib import Path

from pythonanywhere_core.webapp import Webapp

from pythonanywhere.project import Project
from pythonanywhere.exceptions import SanityException
from pythonanywhere.virtualenvs import Virtualenv


def test_project_domain_and_python_version(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    assert project.domain == 'mydomain.com'
    assert project.python_version == 'python.version'

def test_project_path(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    assert project.project_path == fake_home / 'mydomain.com'

def test_project_wsgi_file_path(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    assert project.wsgi_file_path == Path('/var/www/mydomain_com_wsgi.py')

def test_project_webapp(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    assert project.webapp == Webapp('mydomain.com')

def test_project_virtualenv(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    assert project.virtualenv == Virtualenv('mydomain.com', 'python.version')


def test_sanity_checks_calls_webapp_sanity_checks(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    project.webapp.sanity_checks = Mock()
    project.sanity_checks(nuke='nuke.option')
    assert project.webapp.sanity_checks.call_args == call(nuke='nuke.option')

def test_sanity_checks_raises_if_virtualenv_exists(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    project.webapp.sanity_checks = Mock()
    project.virtualenv.path.mkdir()

    with pytest.raises(SanityException) as e:
        project.sanity_checks(nuke=False)

    assert "You already have a virtualenv for mydomain.com" in str(e.value)
    assert "nuke" in str(e.value)

def test_sanity_checks_raises_if_project_path_exists(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    project.webapp.sanity_checks = Mock()
    project.project_path.mkdir()

    with pytest.raises(SanityException) as e:
        project.sanity_checks(nuke=False)

    expected_msg = f"You already have a project folder at {fake_home}/mydomain.com"
    assert expected_msg in str(e.value)
    assert "nuke" in str(e.value)

def test_sanity_checks_nuke_option_overrides_directory_checks(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    project.webapp.sanity_checks = Mock()
    project.project_path.mkdir()
    project.virtualenv.path.mkdir()

    project.sanity_checks(nuke=True)  # should not raise


def test_create_webapp_calls_webapp_create(virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    project.webapp.create = Mock()
    project.python_version = 'python.version'

    project.create_webapp(nuke=True)
    assert project.webapp.create.call_args == call(
        'python.version', project.virtualenv.path, project.project_path, nuke=True
    )


def test_add_static_file_mappings_calls_webapp_add_default_static_files_mappings(virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    project.webapp.add_default_static_files_mappings = Mock()
    project.add_static_file_mappings()
    assert project.webapp.add_default_static_files_mappings.call_args == call(
        project.project_path,
    )


def test_reload_webapp_calls_webapp_reload(virtualenvs_folder, mocker):
    mock_webapp_class = mocker.patch('pythonanywhere.project.Webapp', autospec=True)
    project = Project('mydomain.com', 'python.version')
    project.reload_webapp()
    mock_webapp_class.return_value.reload.assert_called_once()


def test_start_bash_calls_launch_bash_in_virtualenv_with_virtualenv_and_project_path(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    with patch('pythonanywhere.project.launch_bash_in_virtualenv') as mock_launch_bash_in_virtualenv:
        project.start_bash()
    args, kwargs = mock_launch_bash_in_virtualenv.call_args
    assert args[0] == project.virtualenv.path
    assert args[2] == project.project_path

def test_start_bash_calls_launch_bash_in_virtualenv_with_unique_id(fake_home, virtualenvs_folder):
    project = Project('mydomain.com', 'python.version')
    with patch('pythonanywhere.project.launch_bash_in_virtualenv') as mock_launch_bash_in_virtualenv:
        for _ in range(100):
            project.start_bash()
    unique_ids = [args[1] for args, kwargs in mock_launch_bash_in_virtualenv.call_args_list]
    assert len(set(unique_ids)) == len(unique_ids)
