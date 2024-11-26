import os
import subprocess
import time
from platform import python_version
from unittest.mock import call

import pytest
import requests
from typer.testing import CliRunner

from cli.django import app

runner = CliRunner()


@pytest.fixture
def mock_django_project(mocker):
    return mocker.patch("cli.django.DjangoProject")


@pytest.fixture
def mock_update_wsgi_file(mocker):
    return mocker.patch("cli.django.DjangoProject.update_wsgi_file")


@pytest.fixture
def mock_call_api(mocker):
    return mocker.patch("pythonanywhere_core.webapp.call_api")


@pytest.fixture
def running_python_version():
    return ".".join(python_version().split(".")[:2])


def test_main_subcommand_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 0
    assert "Show this message and exit." in result.stdout


def test_autoconfigure_calls_all_stuff_in_right_order(mock_django_project):
    result = runner.invoke(
        app,
        [
            "autoconfigure",
            "repo.url",
            "-d",
            "www.domain.com",
            "-p",
            "python.version",
            "--nuke",
        ],
    )
    mock_django_project.assert_called_once_with("www.domain.com", "python.version")
    assert mock_django_project.return_value.method_calls == [
        call.sanity_checks(nuke=True),
        call.download_repo("repo.url", nuke=True),
        call.ensure_branch("None"),
        call.create_virtualenv(nuke=True),
        call.create_webapp(nuke=True),
        call.add_static_file_mappings(),
        call.find_django_files(),
        call.update_wsgi_file(),
        call.update_settings_file(),
        call.run_collectstatic(),
        call.run_migrate(),
        call.webapp.reload(),
        call.start_bash(),
    ]
    assert (
        f"All done!  Your site is now live at https://www.domain.com" in result.stdout
    )


@pytest.mark.slowtest
def test_autoconfigure_actually_works_against_example_repo(
    mocker,
    mock_call_api,
    mock_update_wsgi_file,
    fake_home,
    virtualenvs_folder,
    api_token,
    process_killer,
    running_python_version,
):
    git_ref = "non-nested-old" if running_python_version in ["3.8", "3.9"] else "master"
    expected_django_version = "4.2.16" if running_python_version in ["3.8", "3.9"] else "5.1.3"
    mocker.patch("cli.django.DjangoProject.start_bash")
    repo = "https://github.com/pythonanywhere/example-django-project.git"
    domain = "mydomain.com"

    runner.invoke(
        app,
        [
            "autoconfigure",
            repo,
            "-d",
            domain,
            "-p",
            running_python_version,
            "--branch",
            git_ref,
        ],
    )

    expected_virtualenv = virtualenvs_folder / domain
    expected_project_path = fake_home / domain
    django_project_name = "myproject"
    expected_settings_path = expected_project_path / django_project_name / "settings.py"

    django_version = (
        subprocess.check_output(
            [
                str(expected_virtualenv / "bin/python"),
                "-c" "import django; print(django.get_version())",
            ]
        )
        .decode()
        .strip()
    )
    assert django_version == expected_django_version

    with expected_settings_path.open() as f:
        lines = f.read().split("\n")
    assert "MEDIA_ROOT = Path(BASE_DIR / 'media')" in lines
    assert "ALLOWED_HOSTS = ['mydomain.com']  # type: List[str]" in lines

    assert "base.css" in os.listdir(str(fake_home / domain / "static/admin/css"))
    server = subprocess.Popen(
        [
            str(expected_virtualenv / "bin/python"),
            str(expected_project_path / "manage.py"),
            "runserver",
        ]
    )
    process_killer.append(server)
    time.sleep(2)
    response = requests.get("http://localhost:8000/", headers={"HOST": "mydomain.com"})
    assert "Hello from an example django project" in response.text


def test_start_calls_all_stuff_in_right_order(mock_django_project):
    result = runner.invoke(
        app,
        [
            "start",
            "-d",
            "www.domain.com",
            "-j",
            "django.version",
            "-p",
            "python.version",
            "--nuke",
        ],
    )

    assert mock_django_project.call_args == call("www.domain.com", "python.version")
    assert mock_django_project.return_value.method_calls == [
        call.sanity_checks(nuke=True),
        call.create_virtualenv("django.version", nuke=True),
        call.run_startproject(nuke=True),
        call.find_django_files(),
        call.update_settings_file(),
        call.run_collectstatic(),
        call.create_webapp(nuke=True),
        call.add_static_file_mappings(),
        call.update_wsgi_file(),
        call.webapp.reload(),
    ]
    assert (
        f"All done!  Your site is now live at https://www.domain.com" in result.stdout
    )


@pytest.mark.slowtest
def test_start_actually_creates_django_project_in_virtualenv_with_hacked_settings_and_static_files(
    mock_call_api,
    mock_update_wsgi_file,
    fake_home,
    virtualenvs_folder,
    api_token,
    running_python_version,
    new_django_version,
):
    runner.invoke(
        app,
        [
            "start",
            "-d",
            "mydomain.com",
            "-j",
            new_django_version,
            "-p",
            running_python_version,
        ],
    )

    django_version = (
        subprocess.check_output(
            [
                str(virtualenvs_folder / "mydomain.com/bin/python"),
                "-c" "import django; print(django.get_version())",
            ]
        )
        .decode()
        .strip()
    )
    assert django_version == new_django_version

    with (fake_home / "mydomain.com/mysite/settings.py").open() as f:
        lines = f.read().split("\n")
    assert "MEDIA_ROOT = Path(BASE_DIR / 'media')" in lines
    assert "ALLOWED_HOSTS = ['mydomain.com']" in lines

    assert "base.css" in os.listdir(str(fake_home / "mydomain.com/static/admin/css"))


@pytest.mark.slowtest
def test_nuke_option_lets_you_run_twice(
    mock_call_api,
    mock_update_wsgi_file,
    fake_home,
    virtualenvs_folder,
    api_token,
    running_python_version,
    old_django_version,
    new_django_version,
):
    runner.invoke(
        app,
        [
            "start",
            "-d",
            "mydomain.com",
            "-j",
            old_django_version,
            "-p",
            running_python_version,
        ],
    )
    runner.invoke(
        app,
        [
            "start",
            "-d",
            "mydomain.com",
            "-j",
            new_django_version,
            "-p",
            running_python_version,
            "--nuke",
        ],
    )

    django_version = (
        subprocess.check_output(
            [
                str(virtualenvs_folder / "mydomain.com/bin/python"),
                "-c" "import django; print(django.get_version())",
            ]
        )
        .decode()
        .strip()
    )
    assert django_version == new_django_version
