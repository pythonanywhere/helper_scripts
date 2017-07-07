import getpass
import json
import pytest
import responses
from urllib.parse import urlencode

from pythonanywhere.api import (
    API_ENDPOINT,
    PYTHON_VERSIONS,
    AuthenticationError,
    add_static_file_mappings,
    call_api,
    create_webapp,
    reload_webapp,
)

class TestCallAPI:

    def test_raises_on_401(self, api_token, api_responses):
        url = 'https://foo.com/'
        api_responses.add(responses.POST, url, status=401, body='nope')
        with pytest.raises(AuthenticationError) as e:
            call_api(url, 'post')
        assert str(e.value) == 'Authentication error 401 calling API: nope'




class TestCreateWebapp:

    def test_does_post_to_create_webapp(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path', nuke=False)

        post = api_responses.calls[0]
        assert post.request.url == expected_post_url
        assert post.request.body == urlencode({
            'domain_name': 'mydomain.com',
            'python_version': PYTHON_VERSIONS['2.7'],
        })
        assert post.request.headers['Authorization'] == f'Token {api_token}'


    def test_does_patch_to_update_virtualenv_path(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path', nuke=False)

        patch = api_responses.calls[1]
        assert patch.request.url == expected_patch_url
        assert patch.request.body == urlencode({
            'virtualenv_path': '/virtualenv/path'
        })
        assert patch.request.headers['Authorization'] == f'Token {api_token}'


    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        api_responses.add(responses.POST, expected_post_url, status=500, body='an error')

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path', nuke=False)

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'an error' in str(e.value)


    def test_raises_if_post_returns_a_200_with_status_error(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        api_responses.add(responses.POST, expected_post_url, status=200, body=json.dumps({
            "status": "ERROR", "error_type": "bad", "error_message": "bad things happened"
        }))

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path', nuke=False)

        assert 'POST to create webapp via API failed' in str(e.value)
        assert 'bad things happened' in str(e.value)


    def test_raises_if_patch_does_not_20x(self, api_responses, api_token):
        expected_post_url = API_ENDPOINT.format(username=getpass.getuser())
        expected_patch_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.POST, expected_post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, expected_patch_url, status=400, json={'message': 'an error'})

        with pytest.raises(Exception) as e:
            create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path', nuke=False)

        assert 'PATCH to set virtualenv path via API failed' in str(e.value)
        assert 'an error' in str(e.value)


    def test_does_delete_first_for_nuke_call(self, api_responses, api_token):
        post_url = API_ENDPOINT.format(username=getpass.getuser())
        webapp_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.DELETE, webapp_url, status=200)
        api_responses.add(responses.POST, post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, webapp_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path', nuke=True)

        delete = api_responses.calls[0]
        assert delete.request.method == 'DELETE'
        assert delete.request.url == webapp_url
        assert delete.request.headers['Authorization'] == f'Token {api_token}'


    def test_ignores_404_from_delete_call_when_nuking(self, api_responses, api_token):
        post_url = API_ENDPOINT.format(username=getpass.getuser())
        webapp_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/'
        api_responses.add(responses.DELETE, webapp_url, status=404)
        api_responses.add(responses.POST, post_url, status=201, body=json.dumps({'status': 'OK'}))
        api_responses.add(responses.PATCH, webapp_url, status=200)

        create_webapp('mydomain.com', '2.7', '/virtualenv/path', '/project/path', nuke=True)



class TestAddStaticFilesMapping:

    def test_does_two_posts_to_static_files_endpoint(self, api_token, api_responses):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/static_files/'
        api_responses.add(responses.POST, expected_url, status=201)
        api_responses.add(responses.POST, expected_url, status=201)

        add_static_file_mappings('mydomain.com', '/project/path')

        post1 = api_responses.calls[0]
        assert post1.request.url == expected_url
        assert post1.request.headers['content-type'] == 'application/json'
        assert post1.request.headers['Authorization'] == f'Token {api_token}'
        assert json.loads(post1.request.body.decode('utf8')) == {
            'url': '/static/', 'path': '/project/path/static'
        }
        post2 = api_responses.calls[1]
        assert post2.request.url == expected_url
        assert post2.request.headers['content-type'] == 'application/json'
        assert post2.request.headers['Authorization'] == f'Token {api_token}'
        assert json.loads(post2.request.body.decode('utf8')) == {
            'url': '/media/', 'path': '/project/path/media'
        }



class TestReloadWebapp:

    def test_does_post_to_reload_url(self, api_responses, api_token):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/reload/'
        api_responses.add(responses.POST, expected_url, status=200)

        reload_webapp('mydomain.com')

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.body is None
        assert post.request.headers['Authorization'] == f'Token {api_token}'


    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_url = API_ENDPOINT.format(username=getpass.getuser()) + 'mydomain.com/reload/'
        api_responses.add(responses.POST, expected_url, status=404, body='nope')

        with pytest.raises(Exception) as e:
            reload_webapp('mydomain.com')

        assert 'POST to reload webapp via API failed' in str(e.value)
        assert 'nope' in str(e.value)



