import getpass
import json
import pytest
import responses
from unittest.mock import patch
from urllib.parse import urlencode

from pythonanywhere.api import (
    get_api_endpoint,
    PYTHON_VERSIONS,
    AuthenticationError,
    Webapp,
    call_api,
)
from pythonanywhere.exceptions import SanityException


class TestGetAPIEndpoint:

    def test_gets_domain_from_env_if_set(self, monkeypatch):
        assert get_api_endpoint() == 'https://www.pythonanywhere.com/api/v0/user/{username}/webapps/'
        monkeypatch.setenv('PYTHONANYWHERE_DOMAIN', 'foo.com')
        assert get_api_endpoint() == 'https://www.foo.com/api/v0/user/{username}/webapps/'


class TestCallAPI:

    def test_raises_on_401(self, api_token, api_responses):
        url = 'https://foo.com/'
        api_responses.add(responses.POST, url, status=401, body='nope')
        with pytest.raises(AuthenticationError) as e:
            call_api(url, 'post')
        assert str(e.value) == 'Authentication error 401 calling API: nope'


    def test_passes_verify_from_environment(self, api_token, monkeypatch):
        monkeypatch.setenv('PYTHONANYWHERE_INSECURE_API', 'true')
        with patch('pythonanywhere.api.requests') as mock_requests:
            call_api('url', 'post', foo='bar')
        args, kwargs = mock_requests.request.call_args
        assert kwargs["verify"] is False


    def test_verify_is_true_if_env_not_set(self, api_token):
        with patch('pythonanywhere.api.requests') as mock_requests:
            call_api('url', 'post', foo='bar')
        args, kwargs = mock_requests.request.call_args
        assert kwargs["verify"] is True


class TestWebapp:

    def test_init(self):
        app = Webapp('www.my-domain.com')
        assert app.domain == 'www.my-domain.com'


    def test_compare_equal(self):
        assert Webapp('www.my-domain.com') == Webapp('www.my-domain.com')


    def test_compare_not_equal(self):
        assert Webapp('www.my-domain.com') != Webapp('www.other-domain.com')



class TestWebappSanityChecks:
    domain = 'www.domain.com'
    expected_url = get_api_endpoint().format(username=getpass.getuser()) + domain + '/'

    def test_does_not_complain_if_api_token_exists(self, api_token, api_responses):
        webapp = Webapp(self.domain)
        api_responses.add(responses.GET, self.expected_url, status=404)
        webapp.sanity_checks(nuke=False)  # should not raise


    def test_raises_if_no_api_token_exists(self, api_responses, no_api_token):
        webapp = Webapp(self.domain)
        with pytest.raises(SanityException) as e:
            webapp.sanity_checks(nuke=False)
        assert "Could not find your API token" in str(e.value)


    def test_raises_if_webapp_already_exists(self, api_token, api_responses):
        webapp = Webapp(self.domain)
        api_responses.add(responses.GET, self.expected_url, status=200, body=json.dumps({
            'id': 1, 'domain_name': self.domain,
        }))

        with pytest.raises(SanityException) as e:
            webapp.sanity_checks(nuke=False)

        assert "You already have a webapp for " + self.domain in str(e.value)
        assert "nuke" in str(e.value)


    def test_does_not_raise_if_no_webapp(self, api_token, api_responses):
        webapp = Webapp(self.domain)
        api_responses.add(responses.GET, self.expected_url, status=404)
        webapp.sanity_checks(nuke=False)  # should not raise


    def test_nuke_option_overrides_all_but_token_check(
        self, api_token, api_responses, fake_home, virtualenvs_folder
    ):
        webapp = Webapp(self.domain)
        (fake_home / self.domain).mkdir()
        (virtualenvs_folder / self.domain).mkdir()

        webapp.sanity_checks(nuke=True)  # should not raise



class TestCreateWebapp:

    def test_does_post_to_create_webapp(self, api_responses, api_token):
        expected_post_url = get_api_endpoint().format(username=getpass.getuser())
        expected_patch_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        Webapp('mydomain.com').create('2.7', '/virtualenv/path', '/project/path', nuke=False)

        post = api_responses.calls[0]
        assert post.request.url == expected_post_url
        assert post.request.body == urlencode({
            'domain_name': 'mydomain.com',
            'python_version': PYTHON_VERSIONS['2.7'],
        })
        assert post.request.headers['Authorization'] == 'Token {api_token}'.format(api_token=api_token)


    def test_does_patch_to_update_virtualenv_path_and_source_directory(self, api_responses, api_token):
        expected_post_url = get_api_endpoint().format(username=getpass.getuser())
        expected_patch_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        Webapp('mydomain.com').create('2.7', '/virtualenv/path', '/project/path', nuke=False)

        patch = api_responses.calls[1]
        assert patch.request.url == expected_patch_url
        assert patch.request.body == urlencode({
            'virtualenv_path': '/virtualenv/path',
            'source_directory': '/project/path'
        })
        assert patch.request.headers['Authorization'] == 'Token {api_token}'.format(api_token=api_token)


    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_post_url = get_api_endpoint().format(username=getpass.getuser())
        api_responses.add(responses.POST, expected_post_url, status=500, body='an error')

        with pytest.raises(Exception) as e:
            Webapp('mydomain.com').create('2.7', '/virtualenv/path', '/project/path', nuke=False)

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'an error' in str(e.value)


    def test_raises_if_post_returns_a_200_with_status_error(self, api_responses, api_token):
        expected_post_url = get_api_endpoint().format(username=getpass.getuser())
        api_responses.add(responses.POST, expected_post_url, status=200, body=json.dumps({
            "status": "ERROR", "error_type": "bad", "error_message": "bad things happened"
        }))

        with pytest.raises(Exception) as e:
            Webapp('mydomain.com').create('2.7', '/virtualenv/path', '/project/path', nuke=False)

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'bad things happened' in str(e.value)


    def test_raises_if_patch_does_not_20x(self, api_responses, api_token):
        expected_post_url = get_api_endpoint().format(username=getpass.getuser())
        expected_patch_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=400, json={'message': 'an error'})

        with pytest.raises(Exception) as e:
            Webapp('mydomain.com').create('2.7', '/virtualenv/path', '/project/path', nuke=False)

        assert 'PATCH to set virtualenv path and source directory via API failed' in str(e.value)
        assert 'an error' in str(e.value)


    def test_does_delete_first_for_nuke_call(self, api_responses, api_token):
        post_url = get_api_endpoint().format(username=getpass.getuser())
        webapp_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.DELETE, webapp_url, status=200)
        api_responses.add(responses.POST, post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, webapp_url, status=200)

        Webapp('mydomain.com').create('2.7', '/virtualenv/path', '/project/path', nuke=True)

        delete = api_responses.calls[0]
        assert delete.request.method == 'DELETE'
        assert delete.request.url == webapp_url
        assert delete.request.headers['Authorization'] == 'Token {api_token}'.format(api_token=api_token)


    def test_ignores_404_from_delete_call_when_nuking(self, api_responses, api_token):
        post_url = get_api_endpoint().format(username=getpass.getuser())
        webapp_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.DELETE, webapp_url, status=404)
        api_responses.add(responses.POST, post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, webapp_url, status=200)

        Webapp('mydomain.com').create('2.7', '/virtualenv/path', '/project/path', nuke=True)



class TestAddDefaultStaticFilesMapping:

    def test_does_two_posts_to_static_files_endpoint(self, api_token, api_responses):
        expected_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/static_files/'
        api_responses.add(responses.POST, expected_url, status=201)
        api_responses.add(responses.POST, expected_url, status=201)

        Webapp('mydomain.com').add_default_static_files_mappings('/project/path')

        post1 = api_responses.calls[0]
        assert post1.request.url == expected_url
        assert post1.request.headers['content-type'] == 'application/json'
        assert post1.request.headers['Authorization'] == 'Token {api_token}'.format(api_token=api_token)
        assert json.loads(post1.request.body.decode('utf8')) == {
            'url': '/static/', 'path': '/project/path/static'
        }
        post2 = api_responses.calls[1]
        assert post2.request.url == expected_url
        assert post2.request.headers['content-type'] == 'application/json'
        assert post2.request.headers['Authorization'] == 'Token {api_token}'.format(api_token=api_token)
        assert json.loads(post2.request.body.decode('utf8')) == {
            'url': '/media/', 'path': '/project/path/media'
        }



class TestReloadWebapp:

    def test_does_post_to_reload_url(self, api_responses, api_token):
        expected_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/reload/'
        api_responses.add(responses.POST, expected_url, status=200)

        Webapp('mydomain.com').reload()

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.body is None
        assert post.request.headers['Authorization'] == 'Token {api_token}'.format(api_token=api_token)


    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/reload/'
        api_responses.add(responses.POST, expected_url, status=404, body='nope')

        with pytest.raises(Exception) as e:
            Webapp('mydomain.com').reload()

        assert 'POST to reload webapp via API failed' in str(e.value)
        assert 'nope' in str(e.value)


class TestSetWebappSSL:

    def test_does_post_to_ssl_url(self, api_responses, api_token):
        expected_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/ssl/'
        api_responses.add(responses.POST, expected_url, status=200)
        certificate = "certificate data"
        private_key = "private key data"

        Webapp('mydomain.com').set_ssl(certificate, private_key)

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert json.loads(post.request.body.decode('utf8')) == {
            'private_key': 'private key data', 'cert': 'certificate data'
        }
        assert post.request.headers['Authorization'] == 'Token {api_token}'.format(api_token=api_token)


    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_url = get_api_endpoint().format(username=getpass.getuser()) + 'mydomain.com/ssl/'
        api_responses.add(responses.POST, expected_url, status=404, body='nope')

        with pytest.raises(Exception) as e:
            Webapp('mydomain.com').set_ssl("foo", "bar")

        assert 'POST to set SSL details via API failed' in str(e.value)
        assert 'nope' in str(e.value)
