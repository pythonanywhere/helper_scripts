import getpass
import json
import tempfile
from unittest.mock import patch
from urllib.parse import urljoin

import pytest
import responses

from pythonanywhere.api.base import get_api_endpoint
from pythonanywhere.api.files_api import Files


class TestFiles:
    username = getpass.getuser()
    base_url = get_api_endpoint().format(username=username, flavor="files")
    home_dir_path = f"/home/{username}"
    default_home_dir_files = {
        ".bashrc": {"type": "file", "url": f"{base_url}path{home_dir_path}/.bashrc"},
        ".gitconfig": {"type": "file", "url": f"{base_url}path{home_dir_path}/.gitconfig"},
        ".local": {"type": "directory", "url": f"{base_url}path{home_dir_path}/.local"},
        ".profile": {"type": "file", "url": f"{base_url}path{home_dir_path}/.profile"},
        "README.txt": {"type": "file", "url": f"{base_url}path{home_dir_path}/README.txt"},
    }


@pytest.mark.files
class TestFilesPathGet(TestFiles):
    def test_returns_contents_of_directory_when_path_to_dir_provided(
        self, api_token, api_responses,
    ):
        dir_url = urljoin(self.base_url, f"path{self.home_dir_path}")
        api_responses.add(
            responses.GET,
            url=dir_url,
            status=200,
            body=json.dumps(self.default_home_dir_files),
            headers={"Content-Type": "application/json"},
        )

        assert Files().path_get(self.home_dir_path) == self.default_home_dir_files

    def test_returns_file_contents_when_file_path_provided(self, api_token, api_responses):
        filepath = urljoin(self.home_dir_path, "README.txt")
        file_url = urljoin(self.base_url, f"path{filepath}")
        body = (
            b"# vim: set ft=rst:\n\nSee https://help.pythonanywhere.com/ "
            b'(or click the "Help" link at the top\nright) '
            b"for help on how to use PythonAnywhere, including tips on copying and\n"
            b"pasting from consoles, and writing your own web applications.\n"
        )
        api_responses.add(
            responses.GET,
            url=file_url,
            status=200,
            body=body,
            headers={"Content-Type": "application/octet-stream; charset=utf-8"},
        )

        assert Files().path_get(filepath) == body

    def test_raises_because_wrong_path_provided(self, api_token, api_responses):
        wrong_path = "/foo"
        wrong_url = urljoin(self.base_url, f"path{wrong_path}")
        body = bytes(f'{{"detail": "No such file or directory: {wrong_path}"}}', "utf")
        api_responses.add(
            responses.GET,
            url=wrong_url,
            status=404,
            body=body,
            headers={"Content-Type": "application/json"},
        )

        with pytest.raises(Exception) as e:
            Files().path_get(wrong_path)

        expected_error_msg = (
            f"GET to fetch contents of {wrong_url} failed, got <Response [404]>: "
            f"No such file or directory: {wrong_path}"
        )
        assert str(e.value) == expected_error_msg


@pytest.mark.files
class TestFilesPathPost(TestFiles):
    def test_returns_200_when_file_updated(self, api_token, api_responses):
        existing_file_path = f"{self.home_dir_path}/README.txt"
        existing_file_url = self.default_home_dir_files["README.txt"]["url"]
        api_responses.add(
            responses.POST,
            url=existing_file_url,
            status=200,
        )

        result = Files().path_post(existing_file_path, "new contents\n", as_string=True)

        assert result == 200

    def test_returns_201_when_file_uploaded(self, api_token, api_responses):
        new_file_path = f"{self.home_dir_path}/new.txt"
        new_file_url = f"{self.base_url}path{self.home_dir_path}/new.txt"
        api_responses.add(
            responses.POST,
            url=new_file_url,
            status=201,
        )

        with tempfile.NamedTemporaryFile() as ntf:
            result = Files().path_post(new_file_path, ntf.name, as_string=False)

        assert result == 201

    def test_raises_when_wrong_path(self, api_token, api_responses):
        invalid_path = "foo"
        url_with_invalid_path = urljoin(self.base_url, f"path{invalid_path}")
        api_responses.add(
            responses.POST,
            url=url_with_invalid_path,
            status=404,
        )

        with pytest.raises(Exception) as e:
            Files().path_post(invalid_path, "contents", as_string=True)

        expected_error_msg = (
            f"POST to upload contents to {url_with_invalid_path} failed, got <Response [404]>"
        )
        assert str(e.value) == expected_error_msg

    @patch("os.path.isfile")
    def test_raises_if_source_is_not_a_file_when_not_using_string(self, mock_isfile):
        mock_isfile.return_value = False
        dest_filepath = urljoin(self.home_dir_path, "README.txt")
        valid_endpoint = urljoin(self.base_url, f"path{dest_filepath}")

        with pytest.raises(Exception) as e:
            Files().path_post(valid_endpoint, "/xyz/zyx", as_string=False)

        assert str(e.value) == "Source should be an existing file or a string"

    def test_raises_when_no_contents_provided(self, api_token, api_responses):
        valid_path = f"{self.home_dir_path}/README.txt"
        valid_url = urljoin(self.base_url, f"path{valid_path}")
        body = bytes('{"detail": "You must provide a file with the name \'content\'."}', "utf")
        api_responses.add(
            responses.POST,
            url=valid_url,
            status=400,
            body=body,
            headers={"Content-Type": "application/json"},
        )

        with pytest.raises(Exception) as e:
            Files().path_post(valid_path, None, as_string=True)

        expected_error_msg = (
            f"POST to upload contents to {valid_url} failed, got <Response [400]>: "
            "You must provide a file with the name 'content'."
        )
        assert str(e.value) == expected_error_msg


@pytest.mark.files
class TestFilesPathDelete(TestFiles):
    def test_returns_204_on_successful_file_deletion(self, api_token, api_responses):
        valid_path = f"{self.home_dir_path}/README.txt"
        valid_url = urljoin(self.base_url, f"path{valid_path}")
        api_responses.add(
            responses.DELETE,
            url=valid_url,
            status=204,
        )

        result = Files().path_delete(valid_path)

        assert result == 204

    def test_raises_when_permission_denied(self, api_token, api_responses):
        home_dir_url = urljoin(self.base_url, f"path{self.home_dir_path}")
        body = bytes(
            '{"message":"You do not have permission to delete this","code":"forbidden"}',
            "utf"
        )
        api_responses.add(
            responses.DELETE,
            url=home_dir_url,
            status=403,
            body=body,
            headers={"Content-Type": "application/json"},
        )

        with pytest.raises(Exception) as e:
            Files().path_delete(self.home_dir_path)

        expected_error_msg = (
            f"DELETE on {home_dir_url} failed, got <Response [403]>: "
            "You do not have permission to delete this"
        )
        assert str(e.value) == expected_error_msg

    def test_raises_when_wrong_path_provided(self, api_token, api_responses):
        invalid_path = "/home/some_other_user/"
        invalid_url = urljoin(self.base_url, f"path{invalid_path}")
        body = bytes('{"message":"File does not exist","code":"not_found"}', "utf")
        api_responses.add(
            responses.DELETE,
            url=invalid_url,
            status=404,
            body=body,
            headers={"Content-Type": "application/json"},
        )

        with pytest.raises(Exception) as e:
            Files().path_delete(invalid_path)

        expected_error_msg = (
            f"DELETE on {invalid_url} failed, got <Response [404]>: "
            "File does not exist"
        )
        assert str(e.value) == expected_error_msg


@pytest.mark.files
class TestFilesSharingPost(TestFiles):
    def test_returns_url_when_path_successfully_shared_or_has_been_shared_before(
        self, api_token, api_responses
    ):
        valid_path = f"{self.home_dir_path}/README.txt"
        shared_url = f"/user/{self.username}/shares/asdf1234/"
        partial_response = dict(
            method=responses.POST,
            url=urljoin(self.base_url, "sharing/"),
            body=bytes(f'{{"url": "{shared_url}"}}', "utf"),
            headers={"Content-Type": "application/json"},
        )
        api_responses.add(**partial_response, status=201)
        api_responses.add(**partial_response, status=200)

        files = Files()
        first_share = files.sharing_post(valid_path)

        assert first_share[0] == 201
        assert first_share[1] == shared_url

        second_share = files.sharing_post(valid_path)

        assert second_share[0] == 200
        assert second_share[1] == shared_url

    @pytest.mark.skip(reason="not implemented in the api yet")
    def test_raises_exception_when_path_not_provided(self, api_token, api_responses):
        url = urljoin(self.base_url, "sharing/")
        api_responses.add(
            responses.POST,
            url=url,
            status=400,
            body=bytes('{"error": "required field (path) not found"}', "utf"),
            headers={"Content-Type": "application/json"},
        )

        with pytest.raises(Exception) as e:
            Files().sharing_post("")

        expected_error_msg = (
            f"POST to {url} to share '' failed, got <Response [400]>: "
            "provided path is not valid"  # or similar
        )
        assert str(e.value) == expected_error_msg


@pytest.mark.files
class TestFilesSharingGet(TestFiles):
    def test_returns_sharing_url_when_path_is_shared(self, api_token, api_responses):
        valid_path = f"{self.home_dir_path}/README.txt"
        sharing_url = urljoin(self.base_url, f"sharing/")
        get_url = urljoin(self.base_url, f"sharing/?path={valid_path}")
        shared_url = f"/user/{self.username}/shares/asdf1234/"
        partial_response = dict(
            body=bytes(f'{{"url": "{shared_url}"}}', "utf"),
            headers={"Content-Type": "application/json"},
        )
        api_responses.add(**partial_response, method=responses.POST, url=sharing_url, status=201)
        api_responses.add(**partial_response, method=responses.GET, url=get_url, status=200)
        files = Files()
        files.sharing_post(valid_path)

        assert files.sharing_get(valid_path) == shared_url

    def test_returns_empty_string_when_path_not_shared(self, api_token, api_responses):
        valid_path = f"{self.home_dir_path}/README.txt"
        url = urljoin(self.base_url, f"sharing/?path={valid_path}")
        api_responses.add(method=responses.GET, url=url, status=404)

        assert Files().sharing_get(valid_path) == ""


@pytest.mark.files
class TestFilesSharingDelete(TestFiles):
    def test_returns_204_on_sucessful_unshare(self, api_token, api_responses):
        valid_path = f"{self.home_dir_path}/README.txt"
        url = urljoin(self.base_url, f"sharing/?path={valid_path}")
        shared_url = f"/user/{self.username}/shares/asdf1234/"
        api_responses.add(method=responses.DELETE, url=url, status=204)

        assert Files().sharing_delete(valid_path) == 204
