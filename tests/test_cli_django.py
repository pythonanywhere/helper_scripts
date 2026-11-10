import os
import subprocess
import time
from platform import python_version
from unittest.mock import call

import pytest
import requests
import responses
from typer.testing import CliRunner
from pythonanywhere_core.exceptions import (
    AuthenticationError,
    PythonAnywhereApiException,
    SlowStartupException,
)

from cli.django import app
from pythonanywhere.project import Project

runner = CliRunner()


@pytest.fixture
def mock_django_project(mocker):
    return mocker.patch("cli.django.DjangoProject")


@pytest.fixture
def mock_update_wsgi_file(mocker):
    return mocker.patch("cli.django.DjangoProject.update_wsgi_file")


@pytest.fixture
def running_python_version():
    return ".".join(python_version().split(".")[:2])


def test_main_subcommand_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 2
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
        call.reload_webapp(),
        call.start_bash(),
    ]
    assert result.exit_code == 0, result.exception
    assert "Running sanity checks" in result.stdout
    assert "All done! Django configuration completed for https://www.domain.com" in result.stdout
    assert "Your site is now live" not in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize("nuke", [False, True])
def test_autoconfigure_warns_and_opens_project_shell_when_startup_is_unconfirmed(
    mock_django_project, nuke
):
    project = mock_django_project.return_value
    project.reload_webapp.side_effect = SlowStartupException()
    args = ["autoconfigure", "repo.url", "--domain", "www.domain.com"]
    if nuke:
        args.append("--nuke")

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.exception
    assert (
        "Warning: Website startup could not be confirmed after the reload attempt."
        in result.stderr
    )
    assert "server and error logs" in result.stderr
    assert "All done! Django configuration completed for https://www.domain.com" in result.stdout
    assert "Your site is now live" not in result.output
    project.reload_webapp.assert_called_once_with()
    project.start_bash.assert_called_once_with()
    assert project.method_calls[-2:] == [call.reload_webapp(), call.start_bash()]


@pytest.mark.parametrize("slow_startup", [False, True])
def test_autoconfigure_completion_uses_the_resolved_default_domain(
    mock_django_project, monkeypatch, slow_startup
):
    monkeypatch.setattr("pythonanywhere.utils.getpass.getuser", lambda: "Florence")
    monkeypatch.setenv("PYTHONANYWHERE_DOMAIN", "test.pythonanywhere.com")
    if slow_startup:
        mock_django_project.return_value.reload_webapp.side_effect = SlowStartupException()

    result = runner.invoke(app, ["autoconfigure", "repo.url"])

    assert result.exit_code == 0, result.exception
    assert "https://florence.test.pythonanywhere.com" in result.stdout
    assert "your-username" not in result.stdout


@pytest.mark.parametrize(
    "failure",
    [
        PythonAnywhereApiException("virtualenv_error"),
        PythonAnywhereApiException("unexpected API response"),
        AuthenticationError("invalid token"),
        requests.exceptions.Timeout("reload response timed out"),
    ],
)
def test_autoconfigure_does_not_report_completion_or_open_shell_after_reload_failure(
    mock_django_project, failure
):
    project = mock_django_project.return_value
    project.reload_webapp.side_effect = failure

    result = runner.invoke(app, ["autoconfigure", "repo.url", "--domain", "www.domain.com"])

    assert result.exit_code != 0
    assert result.exception is failure
    assert "All done!" not in result.stdout
    assert "configuration completed" not in result.stdout
    assert "Warning:" not in result.output
    project.start_bash.assert_not_called()
    project.reload_webapp.assert_called_once_with()


@pytest.mark.parametrize(
    "status_code, error_code, opens_shell, warns",
    [
        (200, None, True, False),
        (409, "slow_startup_error", True, True),
        (409, "cname_error", True, False),
        (409, "virtualenv_error", False, False),
        (401, "slow_startup_error", False, False),
        (403, "slow_startup_error", False, False),
        (500, "slow_startup_error", False, False),
    ],
)
def test_autoconfigure_handles_the_core_reload_response(
    mock_django_project,
    virtualenvs_folder,
    api_token,
    api_responses,
    status_code,
    error_code,
    opens_shell,
    warns,
):
    real_project = Project("www.domain.com", "3.13")
    project = mock_django_project.return_value
    project.reload_webapp.side_effect = real_project.reload_webapp
    api_responses.add(
        responses.POST,
        f"{real_project.webapp.domain_url}reload/",
        status=status_code,
        json={"status": "error", "error": error_code} if error_code else {"status": "OK"},
    )

    result = runner.invoke(app, ["autoconfigure", "repo.url", "--domain", "www.domain.com"])

    assert (result.exit_code == 0) is opens_shell
    assert project.start_bash.called is opens_shell
    assert ("Django configuration completed" in result.stdout) is opens_shell
    assert ("Warning:" in result.stderr) is warns
    assert "Your site is now live" not in result.output
    assert len(api_responses.calls) == 1


def test_autoconfigure_does_not_handle_slow_startup_before_reload(mock_django_project):
    failure = SlowStartupException()
    project = mock_django_project.return_value
    project.create_webapp.side_effect = failure

    result = runner.invoke(app, ["autoconfigure", "repo.url"])

    assert result.exception is failure
    assert result.exit_code != 0
    assert "configuration completed" not in result.stdout
    project.reload_webapp.assert_not_called()
    project.start_bash.assert_not_called()


def test_django_start_still_fails_on_unconfirmed_startup(mock_django_project):
    mock_django_project.return_value.reload_webapp.side_effect = SlowStartupException()

    result = runner.invoke(app, ["start", "--domain", "www.domain.com"])

    assert isinstance(result.exception, SlowStartupException)
    assert result.exit_code != 0
    assert "All done!" not in result.stdout


@pytest.mark.slowtest
def test_autoconfigure_actually_works_against_example_repo(
    mocker,
    webapp_api,
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

    result = runner.invoke(
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

    assert result.exit_code == 0, result.exception

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
        call.reload_webapp(),
    ]
    assert "Running sanity checks" in result.stdout
    assert (
        f"All done!  Your site is now live at https://www.domain.com" in result.stdout
    )


@pytest.mark.slowtest
def test_start_actually_creates_django_project_in_virtualenv_with_hacked_settings_and_static_files(
    webapp_api,
    mock_update_wsgi_file,
    fake_home,
    virtualenvs_folder,
    api_token,
    running_python_version,
    new_django_version,
):
    result = runner.invoke(
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
    assert result.exit_code == 0, result.exception

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
    webapp_api,
    mock_update_wsgi_file,
    fake_home,
    virtualenvs_folder,
    api_token,
    running_python_version,
    old_django_version,
    new_django_version,
):
    result = runner.invoke(
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
    assert result.exit_code == 0, result.exception
    result = runner.invoke(
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
    assert result.exit_code == 0, result.exception

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
