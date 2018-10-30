import getpass
import os
import subprocess
from platform import python_version
from unittest.mock import call, patch

import pytest
from scripts.pa_start_django_webapp_with_virtualenv import main


class TestMain:
    def test_calls_all_stuff_in_right_order(self):
        with patch("scripts.pa_start_django_webapp_with_virtualenv.DjangoProject") as mock_DjangoProject:
            main("www.domain.com", "django.version", "python.version", nuke="nuke option")
        assert mock_DjangoProject.call_args == call("www.domain.com", "python.version")
        assert mock_DjangoProject.return_value.method_calls == [
            call.sanity_checks(nuke="nuke option"),
            call.create_virtualenv("django.version", nuke="nuke option"),
            call.run_startproject(nuke="nuke option"),
            call.find_django_files(),
            call.update_settings_file(),
            call.run_collectstatic(),
            call.create_webapp(nuke="nuke option"),
            call.add_static_file_mappings(),
            call.update_wsgi_file(),
            call.webapp.reload(),
        ]

    def test_domain_defaults_to_using_current_username_and_domain_from_env(self, monkeypatch):
        username = getpass.getuser()
        monkeypatch.setenv("PYTHONANYWHERE_DOMAIN", "pythonanywhere.domain")
        with patch("scripts.pa_start_django_webapp_with_virtualenv.DjangoProject") as mock_DjangoProject:
            main("your-username.pythonanywhere.com", "django.version", "python.version", nuke=False)
        assert mock_DjangoProject.call_args == call(username + ".pythonanywhere.domain", "python.version")

    def test_lowercases_username(self):
        with patch("scripts.pa_start_django_webapp_with_virtualenv.getpass") as mock_getpass:
            mock_getpass.getuser.return_value = "UserName1"
            with patch("scripts.pa_start_django_webapp_with_virtualenv.DjangoProject") as mock_DjangoProject:
                main("your-username.pythonanywhere.com", "django.version", "python.version", "nukey")
            assert mock_DjangoProject.call_args == call("username1.pythonanywhere.com", "python.version")

    @pytest.mark.slowtest
    def test_actually_creates_django_project_in_virtualenv_with_hacked_settings_and_static_files(
        self, fake_home, virtualenvs_folder, api_token
    ):

        with patch("scripts.pa_start_django_webapp_with_virtualenv.DjangoProject.update_wsgi_file"):
            with patch("pythonanywhere.api.call_api"):
                main("mydomain.com", "1.9.2", "2.7", nuke=False)

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
        assert django_version == "1.9.2"

        with (fake_home / "mydomain.com/mysite/settings.py").open() as f:
            lines = f.read().split("\n")
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines
        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines

        assert "base.css" in os.listdir(str(fake_home / "mydomain.com/static/admin/css"))

    @pytest.mark.slowtest
    def test_nuke_option_lets_you_run_twice(self, fake_home, virtualenvs_folder, api_token):

        with patch("scripts.pa_start_django_webapp_with_virtualenv.DjangoProject.update_wsgi_file"):
            with patch("pythonanywhere.api.call_api"):
                version = ".".join(python_version().split(".")[:2])
                main("mydomain.com", "1.9.2", version, nuke=False)
                main("mydomain.com", "1.11.3", version, nuke=True)

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
        assert django_version == "1.11.3"
