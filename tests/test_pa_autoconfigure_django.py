from unittest.mock import call, patch
import os
import pytest
import subprocess
import requests
import time

from scripts.pa_autoconfigure_django import main
from tests.conftest import new_django_version


class TestMain:

    def test_calls_all_stuff_in_right_order(self):
        with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
            main('repo.url', 'foo', 'www.domain.com', 'python.version',  nuke='nuke option')
        assert mock_DjangoProject.call_args == call('www.domain.com', 'python.version')
        assert mock_DjangoProject.return_value.method_calls == [
            call.sanity_checks(nuke='nuke option'),
            call.download_repo('repo.url', nuke='nuke option'),
            call.ensure_branch("foo"),
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

    @pytest.mark.slowtest
    def test_actually_works_against_example_repo(
        self, fake_home, virtualenvs_folder, api_token, process_killer, running_python_version, new_django_version
    ):
        git_ref = "non-nested-old" if running_python_version in ["3.8", "3.9"] else "master"
        repo = 'https://github.com/pythonanywhere/example-django-project.git'
        domain = 'mydomain.com'
        with patch('scripts.pa_autoconfigure_django.DjangoProject.update_wsgi_file'):
            with patch('scripts.pa_autoconfigure_django.DjangoProject.start_bash'):
                with patch('pythonanywhere_core.webapp.call_api'):
                    main(
                        repo_url=repo,
                        branch=git_ref,
                        domain=domain,
                        python_version=running_python_version,
                        nuke=False
                    )

        expected_virtualenv = virtualenvs_folder / domain
        expected_project_path = fake_home / domain
        django_project_name = 'myproject'
        expected_settings_path = expected_project_path / django_project_name / 'settings.py'

        django_version = subprocess.check_output([
            str(expected_virtualenv / 'bin/python'),
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == new_django_version

        with expected_settings_path.open() as f:
            lines = f.read().split('\n')
        assert "MEDIA_ROOT = Path(BASE_DIR / 'media')" in lines
        assert "ALLOWED_HOSTS = ['mydomain.com']  # type: List[str]" in lines

        assert 'base.css' in os.listdir(str(fake_home / domain / 'static/admin/css'))
        server = subprocess.Popen([
            str(expected_virtualenv / 'bin/python'),
            str(expected_project_path / 'manage.py'),
            'runserver'
        ])
        process_killer.append(server)
        time.sleep(2)
        response = requests.get('http://localhost:8000/', headers={'HOST': 'mydomain.com'})
        assert 'Hello from an example django project' in response.text




def xtest_todos():
    assert not 'existing-project sanity checks eg requirements empty'
    assert not 'find better-hidden requirements files?'
    assert not 'what happens if eg collecstatic barfs bc they need to set env vars. shld fail gracefully'
    assert not 'nuke option shouldnt barf if nothing to nuke'
    assert not 'detect use of env vars??'
    assert not 'SECRET_KEY?'
    assert not 'database stuff?'
