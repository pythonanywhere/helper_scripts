import os
import subprocess
from unittest.mock import call, patch, sentinel

import pytest
from scripts.pa_start_django_webapp_with_virtualenv import main


def test_calls_all_stuff_in_right_order(mocker):
    mock_DjangoProject = mocker.patch(
        "scripts.pa_start_django_webapp_with_virtualenv.DjangoProject"
    )

    main(
        sentinel.domain, sentinel.django_version, sentinel.python_version, nuke=sentinel.nuke
    )
    assert mock_DjangoProject.call_args == call(sentinel.domain, sentinel.python_version)
    assert mock_DjangoProject.return_value.method_calls == [
        call.sanity_checks(nuke=sentinel.nuke),
        call.create_virtualenv(sentinel.django_version, nuke=sentinel.nuke),
        call.run_startproject(nuke=sentinel.nuke),
        call.find_django_files(),
        call.update_settings_file(),
        call.run_collectstatic(),
        call.create_webapp(nuke=sentinel.nuke),
        call.add_static_file_mappings(),
        call.update_wsgi_file(),
        call.webapp.reload(),
    ]

@pytest.mark.slowtest
def test_actually_creates_django_project_in_virtualenv_with_hacked_settings_and_static_files(
    fake_home, virtualenvs_folder, api_token, running_python_version, new_django_version
):
    with patch("scripts.pa_start_django_webapp_with_virtualenv.DjangoProject.update_wsgi_file"):
        with patch("pythonanywhere_core.webapp.call_api"):
            main("mydomain.com", new_django_version, running_python_version, nuke=False)

    output_django_version = (
        subprocess.check_output(
            [
                str(virtualenvs_folder / "mydomain.com/bin/python"),
                "-c" "import django; print(django.get_version())",
            ]
        )
        .decode()
        .strip()
    )
    assert output_django_version == new_django_version

    with (fake_home / "mydomain.com/mysite/settings.py").open() as f:
        lines = f.read().split("\n")
    assert "MEDIA_ROOT = Path(BASE_DIR / 'media')" in lines
    assert "ALLOWED_HOSTS = ['mydomain.com']" in lines

    assert "base.css" in os.listdir(str(fake_home / "mydomain.com/static/admin/css"))

@pytest.mark.slowtest
def test_nuke_option_lets_you_run_twice(
        fake_home, virtualenvs_folder, api_token, running_python_version, new_django_version, old_django_version
):

    with patch("scripts.pa_start_django_webapp_with_virtualenv.DjangoProject.update_wsgi_file"):
        with patch("pythonanywhere_core.webapp.call_api"):
            main("mydomain.com", old_django_version, running_python_version, nuke=False)
            main("mydomain.com", new_django_version, running_python_version, nuke=True)

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
