from unittest.mock import call, patch
import getpass
import json
import os
import pytest
import responses
import subprocess

from pythonanywhere.api import API_ENDPOINT
from scripts.pa_start_django_webapp_with_virtualenv import (
    SanityException,
    main,
    sanity_checks,
)


class TestMain:

    def test_calls_all_the_right_stuff_in_order(self, mock_main_functions):
        main('www.domain.com', 'django.version', 'python.version', nuke='nuke option')
        assert mock_main_functions.method_calls == [
            call.sanity_checks('www.domain.com', nuke='nuke option'),
            call.create_virtualenv(
                'www.domain.com', 'python.version', 'django.version', nuke='nuke option'
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
            username + '.pythonanywhere.com', 'python.version', 'django.version', nuke=False
        )
        assert mock_main_functions.reload_webapp.call_args == call(
            username + '.pythonanywhere.com',
        )


    def test_lowercases_username(self, mock_main_functions):
        with patch('scripts.pa_start_django_webapp_with_virtualenv.getpass') as mock_getpass:
            mock_getpass.getuser.return_value = 'UserName1'
            main('your-username.pythonanywhere.com', 'django.version', 'python.version', 'nukey')
            assert mock_main_functions.create_virtualenv.call_args == call(
                'username1.pythonanywhere.com', 'python.version', 'django.version', nuke='nukey'
            )
            assert mock_main_functions.reload_webapp.call_args == call(
                'username1.pythonanywhere.com',
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
            os.path.join(virtualenvs_folder, 'mydomain.com/bin/python'),
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == '1.9.2'

        with open(os.path.join(fake_home, 'mydomain.com/mysite/settings.py')) as f:
            lines = f.read().split('\n')
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines
        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines

        assert 'base.css' in os.listdir(os.path.join(fake_home, 'mydomain.com/static/admin/css'))


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
            api_responses.add(responses.POST, webapps_url, status=201, body=json.dumps({'status': 'OK'}))
            api_responses.add(responses.PATCH, webapp_url, status=200)
            api_responses.add(responses.POST, reload_url, status=200, body=json.dumps({'status': 'OK'}))
            api_responses.add(responses.POST, static_files_url, status=201)
            api_responses.add(responses.POST, static_files_url, status=201)

            main('mydomain.com', '1.9.2', '2.7', nuke=True)


class TestSanityChecks:
    domain = 'www.domain.com'
    expected_url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/'

    def test_does_not_complain_if_api_token_exists(self, api_token, api_responses):
        api_responses.add(responses.GET, self.expected_url, status=404)
        sanity_checks(self.domain, nuke=False)  # should not raise


    def test_raises_if_no_api_token_exists(self, api_responses, no_api_token):
        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain, nuke=False)
        assert "Could not find your API token" in str(e.value)


    def test_raises_if_webapp_already_exists(self, api_token, api_responses):
        api_responses.add(responses.GET, self.expected_url, status=200, body=json.dumps({
            'id': 1, 'domain_name': self.domain,
        }))

        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain, nuke=False)

        assert "You already have a webapp for " + self.domain in str(e.value)
        assert "nuke" in str(e.value)


    def test_does_not_raise_if_no_webapp(self, api_token, api_responses):
        api_responses.add(responses.GET, self.expected_url, status=404)
        sanity_checks(self.domain, nuke=False)  # should not raise


    def test_raises_if_virtualenv_exists(self, api_token, api_responses, virtualenvs_folder):
        os.mkdir(os.path.join(virtualenvs_folder, self.domain))
        api_responses.add(responses.GET, self.expected_url, status=404)

        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain, nuke=False)  # should not raise

        assert "You already have a virtualenv for " + self.domain in str(e.value)
        assert "nuke" in str(e.value)


    def test_raises_if_project_path_exists(self, api_token, api_responses, fake_home):
        api_responses.add(responses.GET, self.expected_url, status=404)
        os.mkdir(os.path.join(fake_home, self.domain))

        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain, nuke=False)  # should not raise

        expected_msg = f"You already have a project folder at {fake_home}/{self.domain}"
        assert expected_msg in str(e.value)
        assert "nuke" in str(e.value)



    def test_nuke_option_overrides_all_but_token_check(
        self, api_token, api_responses, fake_home, virtualenvs_folder
    ):
        os.mkdir(os.path.join(fake_home, self.domain))
        os.mkdir(os.path.join(virtualenvs_folder, self.domain))

        sanity_checks(self.domain, nuke=True)  # should not raise

