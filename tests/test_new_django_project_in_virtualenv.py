from unittest.mock import call, patch
import getpass
import json
import os
import pytest
import responses
import subprocess
import tempfile
from textwrap import dedent
from urllib.parse import urlencode

import new_django_project_in_virtualenv
from new_django_project_in_virtualenv import (
    API_ENDPOINT,
    PYTHON_VERSIONS,
    SanityException,
    add_static_file_mappings,
    create_virtualenv,
    create_webapp,
    main,
    sanity_checks,
    start_django_project,
    update_settings_file,
    update_wsgi_file,
    reload_webapp,
)


class TestMain:

    def test_calls_all_the_right_stuff_in_order(self, mock_main_functions):
        main('www.domain.com', 'django.version', 'python.version')
        assert mock_main_functions.method_calls == [
            call.sanity_checks('www.domain.com'),
            call.create_virtualenv(
                'www.domain.com', 'python.version', 'django.version'
            ),
            call.start_django_project(
                'www.domain.com', mock_main_functions.create_virtualenv.return_value
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
                mock_main_functions.start_django_project.return_value
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
        main('your-username.pythonanywhere.com', 'django.version', 'python.version')
        assert mock_main_functions.create_virtualenv.call_args == call(
            username + '.pythonanywhere.com', 'python.version', 'django.version'
        )
        assert mock_main_functions.reload_webapp.call_args == call(
            username + '.pythonanywhere.com',
        )



    @pytest.mark.slowtest
    def test_creates_django_project_in_virtualenv_with_hacked_settings_and_static_files(
        self, fake_home, virtualenvs_folder, api_responses, api_token
    ):

        webapps_url = API_ENDPOINT.format(username=getpass.getuser())
        webapp_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        reload_url = webapp_url + 'reload'
        static_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/static_files/'

        api_responses.add(responses.GET, webapp_url, status=404)
        api_responses.add(responses.POST, webapps_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, webapp_url, status=200)
        api_responses.add(responses.POST, reload_url, status=200, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.POST, static_url, status=201)
        api_responses.add(responses.POST, static_url, status=201)


        with patch('new_django_project_in_virtualenv.update_wsgi_file'):
            main('mydomain.com', '1.9.2', '2.7')

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



class TestSanityChecks:
    domain = 'www.domain.com'
    expected_url = API_ENDPOINT.format(username=getpass.getuser()) + domain + '/'

    def test_does_not_complain_if_api_token_exists(self, api_token, api_responses):
        api_responses.add(responses.GET, self.expected_url, status=404)
        sanity_checks(self.domain)  # should not raise


    def test_raises_if_no_api_token_exists(self, api_responses):
        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain)
        assert "Could not find your API token" in str(e.value)


    def test_raises_if_webapp_already_exists(self, api_token, api_responses):
        api_responses.add(responses.GET, self.expected_url, status=200, body=json.dumps({
            'id': 1, 'domain_name': self.domain,
        }))

        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain)

        assert "You already have a webapp for " + self.domain in str(e.value)
        assert "nuke" in str(e.value)


    def test_does_not_raise_if_no_webapp(self, api_token, api_responses):
        api_responses.add(responses.GET, self.expected_url, status=404)
        sanity_checks(self.domain)  # should not raise


    def test_raises_if_virtualenv_exists(self, api_token, api_responses, virtualenvs_folder):
        os.mkdir(os.path.join(virtualenvs_folder, self.domain))
        api_responses.add(responses.GET, self.expected_url, status=404)

        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain)  # should not raise

        assert "You already have a virtualenv for " + self.domain in str(e.value)
        assert "nuke" in str(e.value)


    def test_raises_if_project_path_exists(self, api_token, api_responses, fake_home):
        api_responses.add(responses.GET, self.expected_url, status=404)
        os.mkdir(os.path.join(fake_home, self.domain))

        with pytest.raises(SanityException) as e:
            sanity_checks(self.domain)  # should not raise

        expected_msg = "You already have a project folder at {home}/{domain}".format(
            home=fake_home, domain=self.domain
        )
        assert expected_msg in str(e.value)
        assert "nuke" in str(e.value)



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





class TestStartDjangoProject:


    def test_creates_folder(self, mock_subprocess, fake_home):
        start_django_project('mydomain.com', '/path/to/virtualenv')
        expected_path = os.path.join(fake_home, 'mydomain.com')
        assert os.path.isdir(expected_path)


    def test_calls_startproject(self, mock_subprocess, fake_home):
        start_django_project('mydomain.com', '/path/to/virtualenv')
        expected_path = os.path.join(fake_home, 'mydomain.com')
        assert mock_subprocess.check_call.call_args == call([
            '/path/to/virtualenv/bin/django-admin.py',
            'startproject',
            'mysite',
            expected_path
        ])


    def test_returns_project_path(self, mock_subprocess, fake_home):
        with patch('new_django_project_in_virtualenv.update_settings_file'):
            response = start_django_project('mydomain.com', '/path/to/virtualenv')
        assert response == os.path.join(fake_home, 'mydomain.com')



class TestUpdateSettingsFile:

    def test_adds_STATIC_and_MEDIA_config_to_settings(self):
        test_folder = tempfile.mkdtemp()
        os.makedirs(os.path.join(test_folder, 'mysite'))
        with open(os.path.join(test_folder, 'mysite/settings.py'), 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        update_settings_file('mydomain.com', test_folder)
        with open(os.path.join(test_folder, 'mysite/settings.py')) as f:
            contents = f.read()

        lines = contents.split('\n')
        assert "STATIC_URL = '/static/'" in lines
        assert "MEDIA_URL = '/media/'" in lines
        assert "STATIC_ROOT = os.path.join(BASE_DIR, 'static')" in lines
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines


    def test_adds_domain_to_ALLOWED_HOSTS(self):
        test_folder = tempfile.mkdtemp()
        os.makedirs(os.path.join(test_folder, 'mysite'))
        with open(os.path.join(test_folder, 'mysite/settings.py'), 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        update_settings_file('mydomain.com', test_folder)
        with open(os.path.join(test_folder, 'mysite/settings.py')) as f:
            contents = f.read()

        lines = contents.split('\n')

        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines



class TestCreateWebapp:

    def test_does_post_to_create_webapp(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        post = api_responses.calls[0]
        assert post.request.url == expected_post_url
        assert post.request.body == urlencode({
            'domain_name': 'mydomain.com',
            'python_version': PYTHON_VERSIONS['2.7'],
        })
        assert post.request.headers['Authorization'] == 'Token {}'.format(api_token)


    def test_does_patch_to_update_virtualenv_path(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        patch = api_responses.calls[1]
        assert patch.request.url == expected_patch_url
        assert patch.request.body == urlencode({
            'virtualenv_path': '/virtualenv/path'
        })
        assert patch.request.headers['Authorization'] == 'Token {}'.format(api_token)


    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        api_responses.add(responses.POST, expected_post_url, status=500, body='an error')

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'an error' in str(e.value)


    def test_raises_if_post_returns_a_200_with_status_error(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        api_responses.add(responses.POST, expected_post_url, status=200, body=json.dumps({
            "status": "ERROR", "error_type": "bad", "error_message": "bad things happened"
        }))

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'bad things happened' in str(e.value)


    def test_raises_if_patch_does_not_20x(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=400, json={'message': 'an error'})

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path')

        assert 'PATCH to set virtualenv path via API failed' in str(e.value)
        assert 'an error' in str(e.value)



class TestAddStaticFilesMapping:

    def test_does_two_posts_to_static_files_endpoint(self, api_token, api_responses):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/static_files/'
        api_responses.add(responses.POST, expected_url, status=201)
        api_responses.add(responses.POST, expected_url, status=201)

        add_static_file_mappings('mydomain.com', '/project/path')

        post1 = api_responses.calls[0]
        assert post1.request.url == expected_url
        assert post1.request.headers['content-type'] == 'application/json'
        assert post1.request.headers['Authorization'] == 'Token {}'.format(api_token)
        assert json.loads(post1.request.body.decode('utf8')) == {
            'url': '/static/', 'path': '/project/path/static'
        }
        post2 = api_responses.calls[1]
        assert post2.request.url == expected_url
        assert post2.request.headers['content-type'] == 'application/json'
        assert post2.request.headers['Authorization'] == 'Token {}'.format(api_token)
        assert json.loads(post2.request.body.decode('utf8')) == {
            'url': '/media/', 'path': '/project/path/media'
        }



class TestUpdateWsgiFile:

    def test_updates_wsgi_file_from_template(self):
        wsgi_file = tempfile.NamedTemporaryFile().name
        template = open(os.path.join(os.path.dirname(new_django_project_in_virtualenv.__file__), 'wsgi_file_template.py')).read()

        update_wsgi_file(wsgi_file, '/project/path')

        with open(wsgi_file) as f:
            contents = f.read()
        assert contents == template.format(project_path='/project/path')



class TestReloadWebapp:

    def test_does_post_to_reload_url(self, api_responses):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/reload'
        api_responses.add(responses.POST, expected_url, status=200)

        reload_webapp('mydomain.com')

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.body is None


    def test_raises_if_post_does_not_20x(self, api_responses):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/reload'
        api_responses.add(responses.POST, expected_url, status=404, body='nope')

        with pytest.raises(Exception) as e:
            reload_webapp('mydomain.com')

        assert 'POST to reload webapp via API failed' in str(e.value)
        assert 'nope' in str(e.value)

