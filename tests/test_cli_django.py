import os
import subprocess
import time
from platform import python_version
from unittest.mock import Mock, call

import pytest
import requests
from typer.testing import CliRunner

from cli.django import app

runner = CliRunner()


def test_autoconfigure_calls_all_stuff_in_right_order(mocker):
    mock_project = mocker.patch("cli.django.DjangoProject")
    mocker.patch("cli.webapp.ensure_domain", Mock(side_effect=lambda x: x))

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
    print(result.stdout)
    mock_project.assert_called_once_with("www.domain.com", "python.version")
    assert mock_project.return_value.method_calls == [
        call.sanity_checks(nuke=True),
        call.download_repo("repo.url", nuke=True),
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
    mocker, fake_home, virtualenvs_folder, api_token, process_killer
):
    mocker.patch("cli.django.DjangoProject.update_wsgi_file")
    mocker.patch("cli.django.DjangoProject.start_bash")
    mocker.patch("pythonanywhere.api.webapp.call_api")
    running_python_version = ".".join(python_version().split(".")[:2])
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
        ],
    )

    expected_django_version = "3.0.6"
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
    assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines
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
