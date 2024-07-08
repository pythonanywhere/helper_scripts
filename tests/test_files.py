from getpass import getuser
from unittest.mock import call

import pytest
from pythonanywhere_core.base import get_api_endpoint

from pythonanywhere_core.files import Files
from pythonanywhere.files import PAPath


class TestFiles:
    username = getuser()
    base_url = get_api_endpoint(username=username, flavor="files")
    home_dir_path = f"/home/{username}"
    default_home_dir_files = {
        ".bashrc": {"type": "file", "url": f"{base_url}path{home_dir_path}/.bashrc"},
        ".gitconfig": {"type": "file", "url": f"{base_url}path{home_dir_path}/.gitconfig"},
        ".local": {"type": "directory", "url": f"{base_url}path{home_dir_path}/.local"},
        ".profile": {"type": "file", "url": f"{base_url}path{home_dir_path}/.profile"},
        "README.txt": {"type": "file", "url": f"{base_url}path{home_dir_path}/README.txt"},
    }
    readme_contents = (
        b"# vim: set ft=rst:\n\nSee https://help.pythonanywhere.com/ "
        b'(or click the "Help" link at the top\nright) '
        b"for help on how to use PythonAnywhere, including tips on copying and\n"
        b"pasting from consoles, and writing your own web applications.\n"
    )


@pytest.mark.files
class TestPAPathInit(TestFiles):
    def test_instantiates_correctly(self, mocker):
        mock_standarize_path = mocker.patch("pythonanywhere.files.PAPath._standarize_path")

        pa_path = PAPath("path")

        assert pa_path.path == mock_standarize_path.return_value
        assert type(pa_path.api) == Files

    def test_url_property_contains_correct_pythonanywhere_resource_url_for_instantiated_path(self):
        path = self.home_dir_path

        url = PAPath(path).__repr__()

        assert url == f"{self.base_url.replace('/api/v0', '')}{path[1:]}"

    def test_repr_returns_url_property_value(self, mocker):
        mock_url = mocker.patch("pythonanywhere.files.PAPath.url")

        assert PAPath("path").__repr__() == mock_url

    def test_sanitizes_path(self):
        pa_path = PAPath("~")

        assert pa_path.path == f"/home/{getuser()}"


@pytest.mark.files
class TestPAPathContents(TestFiles):
    def test_returns_file_contents_as_string_if_path_points_to_a_file(self, mocker):
        path = f"{self.home_dir_path}README.txt"
        mock_path_get = mocker.patch("pythonanywhere_core.files.Files.path_get")
        mock_path_get.return_value = self.readme_contents

        result = PAPath(path).contents

        assert mock_path_get.call_args == call(path)
        assert result == self.readme_contents.decode()

    def test_returns_directory_contents_if_path_points_to_a_directory(self, mocker):
        mock_path_get = mocker.patch("pythonanywhere_core.files.Files.path_get")
        mock_path_get.return_value = self.default_home_dir_files

        result = PAPath(self.home_dir_path).contents

        assert result == self.default_home_dir_files

    def test_warns_when_path_unavailable(self, mocker):
        mock_path_get = mocker.patch("pythonanywhere_core.files.Files.path_get")
        mock_path_get.side_effect = Exception("error msg")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_warning = mocker.patch("pythonanywhere.files.logger.warning")

        result = PAPath("/home/different_user").contents

        assert mock_snake.call_args == call("error msg")
        assert mock_warning.call_args == call(mock_snake.return_value)
        assert result is None


@pytest.mark.files
class TestPAPathTree():
    def test_returns_list_of_regular_dirs_and_files(self, mocker):
        mock_tree_get = mocker.patch("pythonanywhere_core.files.Files.tree_get")
        path = "/home/user"
        tree = [f"{path}/README.txt"]
        mock_tree_get.return_value = tree

        result = PAPath(path).tree

        assert result == tree
        assert mock_tree_get.call_args == call(path)

    def test_warns_if_fetching_of_tree_unsuccessful(self, mocker):
        mock_tree_get = mocker.patch("pythonanywhere_core.files.Files.tree_get")
        mock_tree_get.side_effect = Exception("failed")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_warning = mocker.patch("pythonanywhere.files.logger.warning")
        path = "/home/another_user"

        result = PAPath(path).tree

        assert result is None
        assert mock_tree_get.call_args == call(path)
        assert mock_snake.call_args == call("failed")
        assert mock_warning.call_args == call(mock_snake.return_value)


@pytest.mark.files
class TestPAPathDelete():
    def test_informes_about_successful_file_deletion(self, mocker):
        mock_delete = mocker.patch("pythonanywhere_core.files.Files.path_delete")
        mock_delete.return_value.status_code = 204
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        path = "/valid/path"

        PAPath(path).delete()

        assert mock_delete.call_args == call(path)
        assert mock_snake.call_args == call(f"{path} deleted!")
        assert mock_info.call_args == call(mock_snake.return_value)

    def test_warns_about_failed_deletion(self, mocker):
        mock_delete = mocker.patch("pythonanywhere_core.files.Files.path_delete")
        mock_delete.side_effect = Exception("error msg")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_warning = mocker.patch("pythonanywhere.files.logger.warning")
        undeletable_path = "/home/"

        PAPath(undeletable_path).delete()

        assert mock_snake.call_args == call("error msg")
        assert mock_warning.call_args == call(mock_snake.return_value)


@pytest.mark.files
class TestPAPathUpload():
    def test_informs_about_successful_upload_of_a_file(self, mocker):
        mock_post = mocker.patch("pythonanywhere_core.files.Files.path_post")
        mock_post.return_value = 201
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        destination_path = "/home/user/"
        content = "content".encode()

        result = PAPath(destination_path).upload(content)

        assert mock_post.call_args == call(destination_path, content)
        assert mock_snake.call_args == call(f"Content successfully uploaded to {destination_path}!")
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result is True

    def test_informs_about_successful_update_of_existing_file_with_provided_stream(self, mocker):
        mock_post = mocker.patch("pythonanywhere_core.files.Files.path_post")
        mock_post.return_value = 200
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        destination_path = "/home/user/"
        content = "content".encode()

        result = PAPath(destination_path).upload(content)

        assert mock_post.call_args == call(destination_path, content)
        assert mock_snake.call_args == call(f"{destination_path} successfully updated!")
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result is True

    def test_warns_when_file_has_not_been_uploaded(self, mocker):
        mock_post = mocker.patch("pythonanywhere_core.files.Files.path_post")
        mock_post.side_effect = Exception("sth went wrong")
        mock_warning = mocker.patch("pythonanywhere.files.logger.warning")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        destination_path = "wrong/path"
        content = "content".encode()

        result = PAPath(destination_path).upload(content)

        assert mock_post.call_args == call(destination_path, content)
        assert mock_snake.call_args == call("sth went wrong")
        assert mock_warning.call_args == call(mock_snake.return_value)
        assert result is False


@pytest.mark.files
class TestPAPathShare():
    def test_returns_full_url_for_shared_file(self, mocker):
        mock_sharing_get = mocker.patch("pythonanywhere_core.files.Files.sharing_get")
        mock_sharing_get.return_value = "url"
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        query_path = "/pa/path/to/a/file"

        result = PAPath(query_path).get_sharing_url()

        assert mock_sharing_get.call_args == call(query_path)
        assert mock_snake.call_args == call(f"{query_path} is shared at {mock_sharing_get.return_value}")
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result.endswith("url")

    def test_returns_empty_string_when_file_not_shared(self, mocker):
        mock_sharing_get = mocker.patch("pythonanywhere_core.files.Files.sharing_get")
        mock_sharing_get.return_value = ""
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        query_path = "/pa/path/to/a/file"

        result = PAPath(query_path).get_sharing_url()

        assert mock_sharing_get.call_args == call(query_path)
        assert mock_snake.call_args == call(f"{query_path} has not been shared")
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result == ""

    def test_path_already_shared(self, mocker):
        mock_sharing_post = mocker.patch("pythonanywhere_core.files.Files.sharing_post")
        mock_sharing_post.return_value = ("was already shared", "url")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        path_to_share = "/pa/path/to/a/file"

        result = PAPath(path_to_share).share()

        assert mock_sharing_post.call_args == call(path_to_share)
        assert mock_snake.call_args == call(f"{path_to_share} was already shared at {mock_sharing_post.return_value[1]}")
        assert mock_info.call_args == call(mock_snake.return_value)

    def test_path_successfully_shared(self, mocker):
        mock_sharing_post = mocker.patch("pythonanywhere_core.files.Files.sharing_post")
        mock_sharing_post.return_value = ("successfully shared", "url")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        path_to_share = "/pa/path/to/a/file"

        result = PAPath(path_to_share).share()

        assert mock_sharing_post.call_args == call(path_to_share)
        assert mock_snake.call_args == call(f"{path_to_share} successfully shared at {mock_sharing_post.return_value[1]}")
        assert mock_info.call_args == call(mock_snake.return_value)

    def test_warns_if_share_fails(self, mocker):
        mock_sharing_post = mocker.patch("pythonanywhere_core.files.Files.sharing_post")
        mock_sharing_post.side_effect = Exception("failed")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_warning = mocker.patch("pythonanywhere.files.logger.warning")
        path_to_share = "/invalid/path"

        result = PAPath(path_to_share).share()

        assert mock_sharing_post.call_args == call(path_to_share)
        assert mock_snake.call_args == call("failed")
        assert mock_warning.call_args == call(mock_snake.return_value)
        assert result == ""

    def test_path_is_not_shared_so_cannot_be_unshared(self, mocker):
        mock_sharing_get = mocker.patch("pythonanywhere_core.files.Files.sharing_get")
        mock_sharing_get.return_value = ""
        mock_sharing_delete = mocker.patch("pythonanywhere_core.files.Files.sharing_delete")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        path_to_unshare = "/pa/path/to/a/file"

        result = PAPath(path_to_unshare).unshare()

        assert mock_sharing_get.call_args == call(path_to_unshare)
        assert mock_sharing_delete.call_count == 0
        assert mock_snake.call_args == call(
            f"{path_to_unshare} is not being shared, no need to stop sharing..."
        )
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result is True

    def test_path_successfully_unshared(self, mocker):
        mock_sharing_get = mocker.patch("pythonanywhere_core.files.Files.sharing_get")
        mock_sharing_get.return_value = "url"
        mock_sharing_delete = mocker.patch("pythonanywhere_core.files.Files.sharing_delete")
        mock_sharing_delete.return_value = 204
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        path_to_shared_file = "/pa/path/to/a/file"

        result = PAPath(path_to_shared_file).unshare()

        assert mock_sharing_get.call_args == call(path_to_shared_file)
        assert mock_sharing_delete.call_args == call(path_to_shared_file)
        assert mock_snake.call_args == call(f"{path_to_shared_file} is no longer shared!")
        assert mock_info.call_args == call(mock_snake.return_value)
        assert result is True

    def test_warns_if_unshare_not_successful(self, mocker):
        mock_sharing_get = mocker.patch("pythonanywhere_core.files.Files.sharing_get")
        mock_sharing_get.return_value = "url"
        mock_sharing_delete = mocker.patch("pythonanywhere_core.files.Files.sharing_delete")
        mock_sharing_delete.return_value = 999
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_warning = mocker.patch("pythonanywhere.files.logger.warning")
        path_to_shared_file = "/pa/path/to/a/file"

        result = PAPath(path_to_shared_file).unshare()

        assert mock_sharing_get.call_args == call(path_to_shared_file)
        assert mock_sharing_delete.call_args == call(path_to_shared_file)
        assert mock_snake.call_args == call(f"Could not unshare {path_to_shared_file}... :(")
        assert mock_warning.call_args == call(mock_snake.return_value)
        assert result is False
