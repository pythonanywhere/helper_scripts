import getpass
import json
import os
import pytest
import responses

from pythonanywhere.api import API_ENDPOINT
from pythonanywhere.sanity_checks import SanityException, sanity_checks



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

