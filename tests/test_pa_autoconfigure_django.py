from unittest.mock import call, patch
import getpass
import os
import pytest
import subprocess
import requests
import time
from pathlib import Path
import shutil

from scripts.pa_autoconfigure_django import main



class TestMain:

    def test_calls_all_stuff_in_right_order(self):
        with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
            main('repo.url', 'www.domain.com', 'python.version', nuke='nuke option')
        assert mock_DjangoProject.call_args == call('www.domain.com', 'python.version')
        assert mock_DjangoProject.return_value.method_calls == [
            call.sanity_checks(nuke='nuke option'),
            call.download_repo('repo.url', nuke='nuke option'),
            call.create_virtualenv(nuke='nuke option'),
            call.create_webapp(nuke='nuke option'),
            call.add_static_file_mappings(),
            call.find_django_files(),
            call.update_wsgi_file(),
            call.update_settings_file(),
            call.run_collectstatic(),
            call.run_migrate(),
            call.webapp.reload(),
            call.start_bash(),
        ]


    def test_domain_defaults_to_using_current_username_and_domain_from_env(self, monkeypatch):
        username = getpass.getuser()
        monkeypatch.setenv('PYTHONANYWHERE_DOMAIN', 'pythonanywhere.domain')
        with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
            main('a-repo', 'your-username.pythonanywhere.com', 'python.version', nuke=False)
        assert mock_DjangoProject.call_args == call(
            username + '.pythonanywhere.domain', 'python.version'
        )


    def test_lowercases_username(self):
        with patch('scripts.pa_autoconfigure_django.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'
            with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
                main('a-url', 'your-username.pythonanywhere.com', 'python.version', 'nukey')
            assert mock_DjangoProject.call_args == call(
                'username1.pythonanywhere.com', 'python.version'
            )


    @pytest.mark.slowtest
    def test_actually_works_against_example_repo(
        self, fake_home, virtualenvs_folder, api_token, process_killer
    ):
        repo = 'https://github.com/hjwp/example-django-project.git'
        domain = 'mydomain.com'
        with patch('scripts.pa_autoconfigure_django.DjangoProject.update_wsgi_file'):
            with patch('scripts.pa_autoconfigure_django.DjangoProject.start_bash'):
                with patch('pythonanywhere.api.call_api'):
                    main(repo, domain, '2.7', nuke=False)

        expected_django_version = '1.11.1'
        expected_virtualenv = virtualenvs_folder / domain
        expected_project_path = fake_home / domain
        django_project_name = 'myproject'
        expected_settings_path = expected_project_path / django_project_name / 'settings.py'

        django_version = subprocess.check_output([
            expected_virtualenv / 'bin/python',
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == expected_django_version

        with open(expected_settings_path) as f:
            lines = f.read().split('\n')
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines
        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines

        assert 'base.css' in os.listdir(fake_home / domain / 'static/admin/css')
        server = subprocess.Popen([
            expected_virtualenv / 'bin/python',
            expected_project_path / 'manage.py',
            'runserver'
        ])
        process_killer.append(server)
        time.sleep(1)
        response = requests.get('http://localhost:8000/', headers={'HOST': 'mydomain.com'})
        assert 'Hello from an example django project' in response.text


    @pytest.mark.slowtest
    def test_cookiecutter(
        self, fake_home, virtualenvs_folder, api_token,
    ):
        submodule_path = Path(__file__).parents[1] / 'submodules' / 'cookiecutter-example-project'
        repo = 'https://github.com/hjwp/example-django-project.git'
        domain = 'www.domainy.com'
        expected_project_path = fake_home / domain
        with patch('scripts.pa_autoconfigure_django.DjangoProject.download_repo') as mock_download_repo:
            mock_download_repo.side_effect = lambda *a, **kw: shutil.copytree(submodule_path, expected_project_path)
            with patch('scripts.pa_autoconfigure_django.DjangoProject.update_wsgi_file'):
                with patch('scripts.pa_autoconfigure_django.DjangoProject.start_bash'):
                    with patch('pythonanywhere.api.call_api'):
                        main(repo, domain, '2.7', nuke=False)

        expected_django_version = '1.11.1'
        expected_virtualenv = virtualenvs_folder / domain

        django_version = subprocess.check_output([
            expected_virtualenv / 'bin/python',
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == expected_django_version

        expected_settings_path = expected_project_path / 'config/settings/local.py'
        lines = expected_settings_path.read_text().split('\n')
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines
        assert f"ALLOWED_HOSTS = ['{domain}']" in lines

        stuff = subprocess.check_output([
            expected_virtualenv / 'bin/python',
            expected_project_path / 'manage.py',
            'check'
        ])
        assert stuff == 'weee'



def xtest_todos():
    assert not 'existing-project sanity checks eg requirements empty'
    assert not 'find better-hidden requirements files?'
    assert not 'what happens if eg collecstatic barfs bc they need to set env vars. shld fail gracefully'
    assert not 'nuke option shouldnt barf if nothing to nuke'
    assert not 'detect use of env vars??'
    assert not 'SECRET_KEY?'
    assert not 'database stuff?'

