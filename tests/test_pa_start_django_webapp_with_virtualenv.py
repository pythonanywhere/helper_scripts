from unittest.mock import call, patch, Mock
import getpass
import json
import os
import pytest
import responses
import subprocess

from pythonanywhere.api import API_ENDPOINT
from scripts.pa_start_django_webapp_with_virtualenv import main

@pytest.fixture
def mock_main_functions():
    mocks = Mock()
    patchers = []
    functions = [
        'sanity_checks',
        'create_virtualenv',
        'start_django_project',
        'update_settings_file',
        'run_collectstatic',
        'create_webapp',
        'add_static_file_mappings',
        'update_wsgi_file',
        'reload_webapp',
    ]
    for function in functions:
        mock = getattr(mocks, function)
        patcher = patch(
            'scripts.pa_start_django_webapp_with_virtualenv.{}'.format(function),
            mock
        )
        patchers.append(patcher)
        patcher.start()

    yield mocks

    for patcher in patchers:
        patcher.stop()



class TestMain:

    def test_calls_all_the_right_stuff_in_order(self, mock_main_functions):
        main('www.domain.com', 'django.version', 'python.version', nuke='nuke option')
        assert mock_main_functions.method_calls == [
            call.sanity_checks('www.domain.com', nuke='nuke option'),
            call.create_virtualenv(
                'www.domain.com', 'python.version', 'django==django.version', nuke='nuke option'
            ),
            call.start_django_project(
                'www.domain.com', mock_main_functions.create_virtualenv.return_value, nuke='nuke option'
            ),
            call.update_settings_file(
                'www.domain.com', mock_main_functions.start_django_project.return_value
            ),
            call.run_collectstatic(
                mock_main_functions.create_virtualenv.return_value,
                mock_main_functions.start_django_project.return_value
            ),
            call.create_webapp(
                'www.domain.com',
                'python.version',
                mock_main_functions.create_virtualenv.return_value,
                mock_main_functions.start_django_project.return_value,
                nuke='nuke option',
            ),
            call.add_static_file_mappings(
                'www.domain.com',
                mock_main_functions.start_django_project.return_value
            ),
            call.update_wsgi_file(
                '/var/www/www_domain_com_wsgi.py',
                mock_main_functions.start_django_project.return_value
            ),
            call.reload_webapp(
                'www.domain.com'
            )
        ]


    def test_domain_defaults_to_using_current_username(self, mock_main_functions):
        username = getpass.getuser()
        main('your-username.pythonanywhere.com', 'django.version', 'python.version', nuke=False)
        assert mock_main_functions.create_virtualenv.call_args == call(
            username + '.pythonanywhere.com', 'python.version', 'django==django.version', nuke=False
        )
        assert mock_main_functions.reload_webapp.call_args == call(
            username + '.pythonanywhere.com',
        )


    def test_lowercases_username(self, mock_main_functions):
        with patch('scripts.pa_start_django_webapp_with_virtualenv.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'
            main('your-username.pythonanywhere.com', 'django.version', 'python.version', 'nukey')
            assert mock_main_functions.create_virtualenv.call_args == call(
                'username1.pythonanywhere.com', 'python.version', 'django==django.version', nuke='nukey'
            )
            assert mock_main_functions.reload_webapp.call_args == call(
                'username1.pythonanywhere.com',
            )


    def test_django_latest_is_just_django_for_virtualenv(self, mock_main_functions):
        main('www.domain.com', 'latest', 'python.version', nuke='nuke option')
        assert mock_main_functions.create_virtualenv.call_args == call(
            'www.domain.com', 'python.version', 'django', nuke='nuke option'
        )


    @pytest.mark.slowtest
    def test_creates_django_project_in_virtualenv_with_hacked_settings_and_static_files(
        self, fake_home, virtualenvs_folder, api_responses, api_token
    ):

        webapps_url = API_ENDPOINT.format(username=getpass.getuser())
        webapp_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        reload_url = webapp_url + 'reload/'
        static_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/static_files/'

        api_responses.add(responses.GET, webapp_url, status=404)
        api_responses.add(responses.POST, webapps_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, webapp_url, status=200)
        api_responses.add(responses.POST, reload_url, status=200, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.POST, static_url, status=201)
        api_responses.add(responses.POST, static_url, status=201)


        with patch('scripts.pa_start_django_webapp_with_virtualenv.update_wsgi_file'):
            main('mydomain.com', '1.9.2', '2.7', nuke=False)

        django_version = subprocess.check_output([
            virtualenvs_folder / 'mydomain.com/bin/python',
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == '1.9.2'

        with open(fake_home / 'mydomain.com/mysite/settings.py') as f:
            lines = f.read().split('\n')
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines
        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines

        assert 'base.css' in os.listdir(fake_home / 'mydomain.com/static/admin/css')


    @pytest.mark.slowtest
    def test_nuke_option_lets_you_run_twice(
        self, fake_home, virtualenvs_folder, api_responses, api_token
    ):

        webapps_url = API_ENDPOINT.format(username=getpass.getuser())
        webapp_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        reload_url = webapp_url + 'reload/'
        static_files_url = webapp_url + 'static_files/'

        api_responses.add(responses.GET, webapp_url, status=404)
        api_responses.add(responses.POST, webapps_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, webapp_url, status=200)
        api_responses.add(responses.POST, reload_url, status=200, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.POST, static_files_url, status=201)
        api_responses.add(responses.POST, static_files_url, status=201)

        with patch('scripts.pa_start_django_webapp_with_virtualenv.update_wsgi_file'):
            main('mydomain.com', '1.9.2', '2.7', nuke=False)

            api_responses.add(responses.DELETE, webapp_url, status=200)

            main('mydomain.com', '1.11.3', '3.6', nuke=True)

        django_version = subprocess.check_output([
            virtualenvs_folder / 'mydomain.com/bin/python',
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == '1.11.3'

