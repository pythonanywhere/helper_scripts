import getpass
import json
from urllib.parse import urljoin

import pytest
import responses

from pythonanywhere.api.base import get_api_endpoint
from pythonanywhere.api.files_api import Files


@pytest.fixture
def files_base_url():
    return get_api_endpoint().format(username=getpass.getuser(), flavor="files")


@pytest.fixture
def home_dir_path(files_base_url):
    return urljoin(files_base_url, f"path/home/{getpass.getuser()}/")


@pytest.fixture
def default_home_dir_files(home_dir_path):
    return {
        ".bashrc": {"type": "file", "url": urljoin(home_dir_path, ".bashrc")},
        ".gitconfig": {"type": "file", "url": urljoin(home_dir_path, ".gitconfig")},
        ".local": {"type": "directory", "url": urljoin(home_dir_path, ".local")},
        ".profile": {"type": "file", "url": urljoin(home_dir_path, ".profile")},
        "README.txt": {"type": "file", "url": urljoin(home_dir_path, "README.txt")},
    }


@pytest.mark.files
class TestFilesPath:
    def test_returns_contents_of_directory_when_path_to_dir_provided(
        self, api_token, api_responses, home_dir_path, default_home_dir_files
    ):
        api_responses.add(
            responses.GET,
            url=home_dir_path,
            status=200,
            body=json.dumps(default_home_dir_files),
            headers={"Content-Type": "application/json"},
        )

        assert Files().get_path(home_dir_path) == default_home_dir_files

    def test_returns_file_contents_when_file_path_provided(
        self, api_token, api_responses, home_dir_path
    ):
        filepath = urljoin(home_dir_path, "README.txt")
        body = (
            b'# vim: set ft=rst:\n\nSee https://help.pythonanywhere.com/ '
            b'(or click the "Help" link at the top\nright) '
            b'for help on how to use PythonAnywhere, including tips on copying and\n'
            b'pasting from consoles, and writing your own web applications.\n'
        )
        api_responses.add(
            responses.GET,
            url=filepath,
            status=200,
            body=body,
            headers={"Content-Type": "application/octet-stream; charset=utf-8"},
        )

        assert Files().get_path(filepath) == body

    def test_raises_because_wrong_path_provided(
        self, api_token, api_responses, home_dir_path, default_home_dir_files
    ):
        wrong_path = urljoin(home_dir_path, "foo")
        body = f"{{'detail':'No such file or directory: {wrong_path}'}}"
        api_responses.add(
            responses.GET,
            url=wrong_path,
            status=404,
            body=body,
        )

        with pytest.raises(Exception) as e:
            Files().get_path(wrong_path)

        expected_error_msg = (
            f"GET to fetch contents of {wrong_path} failed, got <Response [404]>: {body}"
        )
        assert str(e.value) == expected_error_msg

