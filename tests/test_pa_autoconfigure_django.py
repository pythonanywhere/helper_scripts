from unittest.mock import call, patch
import getpass
import os
import pytest
import subprocess

from scripts.pa_autoconfigure_django import main



class TestMain:

    def test_calls_all_stuff_in_right_order(self):
        with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
            main('repo.url', 'www.domain.com', 'python.version', nuke='nuke option')
        assert mock_DjangoProject.call_args == call('www.domain.com')
        assert mock_DjangoProject.return_value.method_calls == [
            call.sanity_checks(nuke='nuke option'),
            call.download_repo('repo.url', nuke='nuke option'),
            call.create_virtualenv('python.version', nuke='nuke option'),
            call.update_settings_file(),
            call.run_collectstatic(),
            call.create_webapp(nuke='nuke option'),
            call.update_wsgi_file(),
            call.add_static_file_mappings(),
            call.webapp.reload()
        ]


    def test_domain_defaults_to_using_current_username(self):
        username = getpass.getuser()
        with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
            main('a-repo', 'your-username.pythonanywhere.com', 'python.version', nuke=False)
        assert mock_DjangoProject.call_args == call(
            username + '.pythonanywhere.com'
        )


    def test_lowercases_username(self):
        with patch('scripts.pa_autoconfigure_django.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'
            with patch('scripts.pa_autoconfigure_django.DjangoProject') as mock_DjangoProject:
                main('a-url', 'your-username.pythonanywhere.com', 'python.version', 'nukey')
            assert mock_DjangoProject.call_args == call(
                'username1.pythonanywhere.com',
            )


    @pytest.mark.slowtest
    def test_actually_works_against_example_repo(self, fake_home, virtualenvs_folder, api_token):
        with patch('scripts.pa_autoconfigure_django.DjangoProject.update_wsgi_file'):
            with patch('pythonanywhere.api.call_api'):
                main(
                    'https://github.com/hjwp/example-django-project.git',
                    'mydomain.com',
                    '2.7',
                    nuke=False,
                )

        django_version = subprocess.check_output([
            virtualenvs_folder / 'mydomain.com/bin/python',
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == '1.11.1'

        with open(fake_home / 'mydomain.com/mysite/settings.py') as f:
            lines = f.read().split('\n')
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines
        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines

        assert 'base.css' in os.listdir(fake_home / 'mydomain.com/static/admin/css')




def xtest_todos():
    assert not 'existing-project sanity checks eg settings.py not found, requirements empty'
    assert not 'nuke option shouldnt barf if nothing to nuke'
    assert not 'SECRET_KEY'
    assert not 'database stuff?'

