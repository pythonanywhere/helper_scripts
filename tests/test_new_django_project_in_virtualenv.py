from unittest.mock import call
import getpass
import json
import os
import pytest
import responses
import subprocess
import tempfile
from urllib.parse import urlencode

import new_django_project_in_virtualenv
from new_django_project_in_virtualenv import (
    API_ENDPOINT,
    create_virtualenv,
    create_webapp,
    main,
    start_django_project,
    update_wsgi_file,
    reload_webapp,
)


class TestMain:

    def test_calls_create_virtualenv(self, mock_main_functions):
        main('domain', 'django.version', 'python.version')
        assert mock_main_functions.create_virtualenv.call_args == call(
            'domain', 'python.version', 'django.version'
        )


    def test_domain_defaults_to_using_current_username(self, mock_main_functions):
        username = getpass.getuser()
        main('your-username.pythonanywhere.com', 'django.version', 'python.version')
        assert mock_main_functions.create_virtualenv.call_args == call(
            username + '.pythonanywhere.com', 'python.version', 'django.version'
        )


    def test_calls_start_django_project_with_virtualenv(self, mock_main_functions):
        main('domain', 'django.version', 'python.version')
        assert mock_main_functions.start_django_project.call_args == call(
            'domain', mock_main_functions.create_virtualenv.return_value
        )


    def test_calls_create_webapp_with_virtualenv_and_python_version(self, mock_main_functions):
        main('domain', 'django.version', 'python.version')
        assert mock_main_functions.create_webapp.call_args == call(
            'domain',
            'python.version',
            mock_main_functions.create_virtualenv.return_value,
            mock_main_functions.start_django_project.return_value
        )


    def test_calls_update_wsgi_file(self, mock_main_functions):
        main('www.domain.com', 'django.version', 'python.version')
        assert mock_main_functions.update_wsgi_file.call_args == call(
            '/var/www/www_domain_com_wsgi.py',
            mock_main_functions.start_django_project.return_value
        )


    def test_calls_reload_webapp(self, mock_main_functions):
        main('domain', 'django.version', 'python.version')
        assert mock_main_functions.reload_webapp.call_args == call(
            'domain',
        )



class TestCreateVirtualenv:

    def test_uses_bash_and_sources_virtualenvwrapper(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'latest')
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[:2] == ['bash', '-c']
        assert command_list[2].startswith('source virtualenvwrapper.sh && mkvirtualenv')


    def test_calls_mkvirtualenv_with_python_version_and_domain(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'latest')
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        bash_command = command_list[2]
        assert 'mkvirtualenv --python=/usr/bin/python2.7 domain.com' in bash_command


    def test_django_version_for_latest(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'latest')
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[2].endswith('pip install django')


    def test_returns_virtualenv_path(self, mock_subprocess, virtualenvs_folder):
        response = create_virtualenv('domain.com', '2.7', 'latest')
        assert response == os.path.join(virtualenvs_folder, 'domain.com')


    @pytest.mark.slowtest
    def test_actually_creates_a_virtualenv_with_right_django_version_in(self, virtualenvs_folder):
        domain = 'mydomain.com'
        create_virtualenv(domain, '2.7', '1.9')

        assert domain in os.listdir(virtualenvs_folder)
        django_version = subprocess.check_output([
            os.path.join(virtualenvs_folder, domain, 'bin/python'),
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == '1.9'



class TestStartDjangoProject:

    @pytest.mark.slowtest
    def test_actually_creates_a_django_project(self, test_virtualenv, fake_home):
        start_django_project('mydomain.com', test_virtualenv)
        assert 'mydomain.com' in os.listdir(fake_home)
        assert 'settings.py' in os.listdir(os.path.join(fake_home, 'mydomain.com/mysite'))


    @pytest.mark.slowtest
    def test_adds_STATIC_and_MEDIA_config_to_settings(self, test_virtualenv, fake_home):
        start_django_project('mydomain.com', test_virtualenv)
        with open(os.path.join(fake_home, 'mydomain.com/mysite/settings.py')) as f:
            contents = f.read()

        print(contents)
        lines = contents.split('\n')
        assert "STATIC_URL = '/static/'" in lines
        assert "MEDIA_URL = '/media/'" in lines
        assert "STATIC_ROOT = os.path.join(BASE_DIR, 'static')" in lines
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines


    @pytest.mark.slowtest
    def test_has_run_collectstatic(self, test_virtualenv, fake_home):
        start_django_project('mydomain.com', test_virtualenv)
        assert 'base.css' in os.listdir(os.path.join(fake_home, 'mydomain.com/static/admin/css'))



class TestCreateWebapp:

    @responses.activate
    def test_does_post_to_create_webapp(self, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        responses.add(responses.PATCH, expected_patch_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        post = responses.calls[0]
        assert post.request.url == expected_post_url
        assert post.request.body == urlencode({
            'domain_name': 'mydomain.com',
            'python_version': '2.7',
        })
        assert post.request.headers['Authorization'] == 'Token {}'.format(api_token)


    @responses.activate
    def test_does_patch_to_update_virtualenv_path(self, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        responses.add(responses.PATCH, expected_patch_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        patch = responses.calls[1]
        assert patch.request.url == expected_patch_url
        assert patch.request.body == urlencode({
            'virtualenv_path': '/virtualenv/path'
        })
        assert patch.request.headers['Authorization'] == 'Token {}'.format(api_token)


    @responses.activate
    def test_raises_if_post_does_not_20x(self):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        responses.add(responses.POST, expected_post_url, status=500, body='an error')
        responses.add(responses.PATCH, expected_patch_url, status=200)

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'an error' in str(e.value)


    @responses.activate
    def test_raises_if_post_returns_a_200_with_status_error(self):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        responses.add(responses.POST, expected_post_url, status=200, body=json.dumps({
            "status": "ERROR", "error_type": "bad", "error_message": "bad things happened"
        }))
        responses.add(responses.PATCH, expected_patch_url, status=200)

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'bad things happened' in str(e.value)


    @responses.activate
    def test_raises_if_patch_does_not_20x(self):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        responses.add(responses.PATCH, expected_patch_url, status=400, json={'message': 'an error'})

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        assert 'PATCH to set virtualenv path via API failed' in str(e.value)
        assert 'an error' in str(e.value)


class TestUpdateWsgiFileTest:

    def test_updates_wsgi_file_from_template(self):
        wsgi_file = tempfile.NamedTemporaryFile().name
        template = open(os.path.join(os.path.dirname(new_django_project_in_virtualenv.__file__), 'wsgi_file_template.py')).read()

        update_wsgi_file(wsgi_file, '/project/path')

        with open(wsgi_file) as f:
            contents = f.read()
        assert contents == template.format(project_path='/project/path')


class TestReloadWebapp:


    @responses.activate
    def test_does_post_to_reload_url(self):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/reload'
        responses.add(responses.POST, expected_url, status=200)

        reload_webapp('mydomain.com')

        post = responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.body is None


    @responses.activate
    def test_raises_if_post_does_not_20x(self):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/reload'
        responses.add(responses.POST, expected_url, status=404, body='nope')

        with pytest.raises(Exception) as e:
            reload_webapp('mydomain.com')

        assert 'POST to reload webapp via API failed' in str(e.value)
        assert 'nope' in str(e.value)

