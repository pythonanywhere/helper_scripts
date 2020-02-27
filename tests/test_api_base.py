from unittest.mock import patch

import pytest
import responses

from pythonanywhere.api.base import AuthenticationError, call_api, get_api_endpoint


class TestGetAPIEndpoint:

    def test_defaults_to_pythonanywhere_dot_com_if_no_environment_variables(self):
        assert get_api_endpoint() == "https://www.pythonanywhere.com/api/v0/user/{username}/{flavor}/"

    def test_gets_domain_from_pythonanywhere_site_and_ignores_pythonanywhere_domain_if_both_set(self, monkeypatch):
        monkeypatch.setenv("PYTHONANYWHERE_SITE", "www.foo.com")
        monkeypatch.setenv("PYTHONANYWHERE_DOMAIN", "wibble.com")
        assert get_api_endpoint() == "https://www.foo.com/api/v0/user/{username}/{flavor}/"

    def test_gets_domain_from_pythonanywhere_domain_and_adds_on_www_if_set_but_no_pythonanywhere_site(
        self, monkeypatch
    ):
        monkeypatch.setenv("PYTHONANYWHERE_DOMAIN", "foo.com")
        assert get_api_endpoint() == "https://www.foo.com/api/v0/user/{username}/{flavor}/"


class TestCallAPI:
    def test_raises_on_401(self, api_token, api_responses):
        url = "https://foo.com/"
        api_responses.add(responses.POST, url, status=401, body="nope")
        with pytest.raises(AuthenticationError) as e:
            call_api(url, "post")
        assert str(e.value) == "Authentication error 401 calling API: nope"

    def test_passes_verify_from_environment(self, api_token, monkeypatch):
        monkeypatch.setenv("PYTHONANYWHERE_INSECURE_API", "true")
        with patch("pythonanywhere.api.base.requests") as mock_requests:
            call_api("url", "post", foo="bar")
        args, kwargs = mock_requests.request.call_args
        assert kwargs["verify"] is False

    def test_verify_is_true_if_env_not_set(self, api_token):
        with patch("pythonanywhere.api.base.requests") as mock_requests:
            call_api("url", "post", foo="bar")
        args, kwargs = mock_requests.request.call_args
        assert kwargs["verify"] is True
