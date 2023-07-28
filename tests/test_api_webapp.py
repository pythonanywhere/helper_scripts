import getpass
import json
from datetime import datetime
from urllib.parse import urlencode

from dateutil.tz import tzutc
import pytest
import responses
from pythonanywhere.api.base import PYTHON_VERSIONS, get_api_endpoint
from pythonanywhere.api.webapp import Webapp
from pythonanywhere.exceptions import SanityException


class TestWebapp:
    def test_init(self):
        app = Webapp("www.my-domain.com")
        assert app.domain == "www.my-domain.com"

    def test_compare_equal(self):
        assert Webapp("www.my-domain.com") == Webapp("www.my-domain.com")

    def test_compare_not_equal(self):
        assert Webapp("www.my-domain.com") != Webapp("www.other-domain.com")


class TestWebappSanityChecks:
    domain = "www.domain.com"
    expected_url = (
        get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
        + domain
        + "/"
    )

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
        api_responses.add(
            responses.GET,
            self.expected_url,
            status=200,
            body=json.dumps({"id": 1, "domain_name": self.domain}),
        )

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
        expected_post_url = get_api_endpoint().format(
            username=getpass.getuser(), flavor="webapps"
        )
        expected_patch_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/"
        )
        api_responses.add(
            responses.POST,
            expected_post_url,
            status=201,
            body=json.dumps({"status": "OK"}),
        )
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        Webapp("mydomain.com").create(
            "3.8", "/virtualenv/path", "/project/path", nuke=False
        )

        post = api_responses.calls[0]
        assert post.request.url == expected_post_url
        assert post.request.body == urlencode(
            {"domain_name": "mydomain.com", "python_version": PYTHON_VERSIONS["3.8"]}
        )
        assert post.request.headers["Authorization"] == f"Token {api_token}"

    def test_does_patch_to_update_virtualenv_path_and_source_directory(
        self, api_responses, api_token
    ):
        expected_post_url = get_api_endpoint().format(
            username=getpass.getuser(), flavor="webapps"
        )
        expected_patch_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/"
        )
        api_responses.add(
            responses.POST,
            expected_post_url,
            status=201,
            body=json.dumps({"status": "OK"}),
        )
        api_responses.add(responses.PATCH, expected_patch_url, status=200)

        Webapp("mydomain.com").create(
            "3.8", "/virtualenv/path", "/project/path", nuke=False
        )

        patch = api_responses.calls[1]
        assert patch.request.url == expected_patch_url
        assert patch.request.body == urlencode(
            {"virtualenv_path": "/virtualenv/path", "source_directory": "/project/path"}
        )
        assert patch.request.headers["Authorization"] == f"Token {api_token}"

    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_post_url = get_api_endpoint().format(
            username=getpass.getuser(), flavor="webapps"
        )
        api_responses.add(
            responses.POST, expected_post_url, status=500, body="an error"
        )

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").create(
                "3.8", "/virtualenv/path", "/project/path", nuke=False
            )

        assert "POST to create webapp via API failed" in str(e.value)
        assert "an error" in str(e.value)

    def test_raises_if_post_returns_a_200_with_status_error(
        self, api_responses, api_token
    ):
        expected_post_url = get_api_endpoint().format(
            username=getpass.getuser(), flavor="webapps"
        )
        api_responses.add(
            responses.POST,
            expected_post_url,
            status=200,
            body=json.dumps(
                {
                    "status": "ERROR",
                    "error_type": "bad",
                    "error_message": "bad things happened",
                }
            ),
        )

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").create(
                "3.8", "/virtualenv/path", "/project/path", nuke=False
            )

        assert "POST to create webapp via API failed" in str(e.value)
        assert "bad things happened" in str(e.value)

    def test_raises_if_patch_does_not_20x(self, api_responses, api_token):
        expected_post_url = get_api_endpoint().format(
            username=getpass.getuser(), flavor="webapps"
        )
        expected_patch_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/"
        )
        api_responses.add(
            responses.POST,
            expected_post_url,
            status=201,
            body=json.dumps({"status": "OK"}),
        )
        api_responses.add(
            responses.PATCH,
            expected_patch_url,
            status=400,
            json={"message": "an error"},
        )

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").create(
                "3.8", "/virtualenv/path", "/project/path", nuke=False
            )

        assert (
            "PATCH to set virtualenv path and source directory via API failed"
            in str(e.value)
        )
        assert "an error" in str(e.value)

    def test_does_delete_first_for_nuke_call(self, api_responses, api_token):
        post_url = get_api_endpoint().format(
            username=getpass.getuser(), flavor="webapps"
        )
        webapp_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/"
        )
        api_responses.add(responses.DELETE, webapp_url, status=200)
        api_responses.add(
            responses.POST, post_url, status=201, body=json.dumps({"status": "OK"})
        )
        api_responses.add(responses.PATCH, webapp_url, status=200)

        Webapp("mydomain.com").create(
            "3.8", "/virtualenv/path", "/project/path", nuke=True
        )

        delete = api_responses.calls[0]
        assert delete.request.method == "DELETE"
        assert delete.request.url == webapp_url
        assert delete.request.headers["Authorization"] == f"Token {api_token}"

    def test_ignores_404_from_delete_call_when_nuking(self, api_responses, api_token):
        post_url = get_api_endpoint().format(
            username=getpass.getuser(), flavor="webapps"
        )
        webapp_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/"
        )
        api_responses.add(responses.DELETE, webapp_url, status=404)
        api_responses.add(
            responses.POST, post_url, status=201, body=json.dumps({"status": "OK"})
        )
        api_responses.add(responses.PATCH, webapp_url, status=200)

        Webapp("mydomain.com").create(
            "3.8", "/virtualenv/path", "/project/path", nuke=True
        )


class TestAddDefaultStaticFilesMapping:
    def test_does_two_posts_to_static_files_endpoint(self, api_token, api_responses):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/static_files/"
        )
        api_responses.add(responses.POST, expected_url, status=201)
        api_responses.add(responses.POST, expected_url, status=201)

        Webapp("mydomain.com").add_default_static_files_mappings("/project/path")

        post1 = api_responses.calls[0]
        assert post1.request.url == expected_url
        assert post1.request.headers["content-type"] == "application/json"
        assert post1.request.headers["Authorization"] == f"Token {api_token}"
        assert json.loads(post1.request.body.decode("utf8")) == {
            "url": "/static/",
            "path": "/project/path/static",
        }
        post2 = api_responses.calls[1]
        assert post2.request.url == expected_url
        assert post2.request.headers["content-type"] == "application/json"
        assert post2.request.headers["Authorization"] == f"Token {api_token}"
        assert json.loads(post2.request.body.decode("utf8")) == {
            "url": "/media/",
            "path": "/project/path/media",
        }


class TestReloadWebapp:
    def test_does_post_to_reload_url(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/reload/"
        )
        api_responses.add(responses.POST, expected_url, status=200)

        Webapp("mydomain.com").reload()

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.body is None
        assert post.request.headers["Authorization"] == f"Token {api_token}"

    def test_raises_if_post_does_not_20x_that_is_not_a_cname_error(
        self, api_responses, api_token
    ):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/reload/"
        )
        api_responses.add(responses.POST, expected_url, status=404, body="nope")

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").reload()

        assert "POST to reload webapp via API failed" in str(e.value)
        assert "nope" in str(e.value)

    def test_does_not_raise_if_post_responds_with_a_cname_error(
        self, api_responses, api_token
    ):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/reload/"
        )
        api_responses.add(
            responses.POST,
            expected_url,
            status=409,
            json={"status": "error", "error": "cname_error"},
        )

        ## Should not raise
        Webapp("mydomain.com").reload()


class TestSetWebappSSL:
    def test_does_post_to_ssl_url(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/ssl/"
        )
        api_responses.add(responses.POST, expected_url, status=200)
        certificate = "certificate data"
        private_key = "private key data"

        Webapp("mydomain.com").set_ssl(certificate, private_key)

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert json.loads(post.request.body.decode("utf8")) == {
            "private_key": "private key data",
            "cert": "certificate data",
        }
        assert post.request.headers["Authorization"] == f"Token {api_token}"

    def test_raises_if_post_does_not_20x(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/ssl/"
        )
        api_responses.add(responses.POST, expected_url, status=404, body="nope")

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").set_ssl("foo", "bar")

        assert "POST to set SSL details via API failed" in str(e.value)
        assert "nope" in str(e.value)


class TestGetWebappSSLInfo:
    def test_returns_json_from_server_having_parsed_expiry_with_z_for_utc_and_no_separators(
        self, api_responses, api_token
    ):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/ssl/"
        )
        api_responses.add(
            responses.GET,
            expected_url,
            status=200,
            body=json.dumps(
                {
                    "not_after": "20180824T171623Z",
                    "issuer_name": "PythonAnywhere test CA",
                    "subject_name": "www.mycoolsite.com",
                    "subject_alternate_names": ["www.mycoolsite.com", "mycoolsite.com"],
                }
            ),
        )

        assert Webapp("mydomain.com").get_ssl_info() == {
            "not_after": datetime(2018, 8, 24, 17, 16, 23, tzinfo=tzutc()),
            "issuer_name": "PythonAnywhere test CA",
            "subject_name": "www.mycoolsite.com",
            "subject_alternate_names": ["www.mycoolsite.com", "mycoolsite.com"],
        }

        get = api_responses.calls[0]
        assert get.request.method == "GET"
        assert get.request.url == expected_url
        assert get.request.headers["Authorization"] == f"Token {api_token}"

    def test_returns_json_from_server_having_parsed_expiry_with_timezone_offset_and_separators(
        self, api_responses, api_token
    ):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/ssl/"
        )
        api_responses.add(
            responses.GET,
            expected_url,
            status=200,
            body=json.dumps(
                {
                    "not_after": "2018-08-24T17:16:23+00:00",
                    "issuer_name": "PythonAnywhere test CA",
                    "subject_name": "www.mycoolsite.com",
                    "subject_alternate_names": ["www.mycoolsite.com", "mycoolsite.com"],
                }
            ),
        )

        assert Webapp("mydomain.com").get_ssl_info() == {
            "not_after": datetime(2018, 8, 24, 17, 16, 23, tzinfo=tzutc()),
            "issuer_name": "PythonAnywhere test CA",
            "subject_name": "www.mycoolsite.com",
            "subject_alternate_names": ["www.mycoolsite.com", "mycoolsite.com"],
        }

        get = api_responses.calls[0]
        assert get.request.method == "GET"
        assert get.request.url == expected_url
        assert get.request.headers["Authorization"] == f"Token {api_token}"

    def test_raises_if_get_does_not_return_200(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="webapps")
            + "mydomain.com/ssl/"
        )
        api_responses.add(responses.GET, expected_url, status=404, body="nope")

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").get_ssl_info()

        assert "GET SSL details via API failed, got" in str(e.value)
        assert "nope" in str(e.value)


class TestDeleteWebappLog:
    def test_delete_current_access_log(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="files")
            + "path/var/log/mydomain.com.access.log/"
        )
        api_responses.add(responses.DELETE, expected_url, status=200)

        Webapp("mydomain.com").delete_log(log_type="access")

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.body is None
        assert post.request.headers["Authorization"] == f"Token {api_token}"

    def test_delete_old_access_log(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="files")
            + "path/var/log/mydomain.com.access.log.1/"
        )
        api_responses.add(responses.DELETE, expected_url, status=200)

        Webapp("mydomain.com").delete_log(log_type="access", index=1)

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.body is None
        assert post.request.headers["Authorization"] == f"Token {api_token}"

    def test_raises_if_delete_does_not_20x(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="files")
            + "path/var/log/mydomain.com.access.log/"
        )
        api_responses.add(responses.DELETE, expected_url, status=404, body="nope")

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").delete_log(log_type="access")

        assert "DELETE log file via API failed" in str(e.value)
        assert "nope" in str(e.value)


class TestGetWebappLogs:
    def test_get_list_of_logs(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="files")
            + "tree/?path=/var/log/"
        )
        api_responses.add(
            responses.GET,
            expected_url,
            status=200,
            body=json.dumps(
                [
                    "/var/log/blah",
                    "/var/log/mydomain.com.access.log",
                    "/var/log/mydomain.com.access.log.1",
                    "/var/log/mydomain.com.access.log.2.gz",
                    "/var/log/mydomain.com.error.log",
                    "/var/log/mydomain.com.error.log.1",
                    "/var/log/mydomain.com.error.log.2.gz",
                    "/var/log/mydomain.com.server.log",
                    "/var/log/mydomain.com.server.log.1",
                    "/var/log/mydomain.com.server.log.2.gz",
                ]
            ),
        )

        logs = Webapp("mydomain.com").get_log_info()

        post = api_responses.calls[0]
        assert post.request.url == expected_url
        assert post.request.headers["Authorization"] == f"Token {api_token}"
        assert logs == {"access": [0, 1, 2], "error": [0, 1, 2], "server": [0, 1, 2]}

    def test_raises_if_get_does_not_20x(self, api_responses, api_token):
        expected_url = (
            get_api_endpoint().format(username=getpass.getuser(), flavor="files")
            + "tree/?path=/var/log/"
        )
        api_responses.add(responses.GET, expected_url, status=404, body="nope")

        with pytest.raises(Exception) as e:
            Webapp("mydomain.com").get_log_info()

        assert "GET log files info via API failed" in str(e.value)
        assert "nope" in str(e.value)
