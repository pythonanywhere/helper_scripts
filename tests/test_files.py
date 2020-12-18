import getpass
from urllib.parse import urljoin
from unittest.mock import call

import pytest

from pythonanywhere.api.base import get_api_endpoint
from pythonanywhere.files import Path
from tests.test_api_files import TestFiles


@pytest.mark.files
class TestPathRepr(TestFiles):
    def test_contains_correct_pythonanywhere_resource_url_for_instantiated_path(self):
        path = self.home_dir_path

        user_path = self.base_url.replace('/api/v0', '')
        assert Path(path).__repr__() == f"{user_path}{path[1:]}"


@pytest.mark.files
class TestPathContents(TestFiles):
    def test_returns_file_contents_as_string_if_path_points_to_a_file(self, mocker):
        path = f"{self.home_dir_path}README.txt"
        mock_path_get = mocker.patch("pythonanywhere.api.files_api.Files.path_get")
        mock_path_get.return_value = self.readme_contents

        result = Path(path).contents()

        assert mock_path_get.call_args == call(path)
        assert result == self.readme_contents.decode()

    def test_returns_directory_contents_if_path_points_to_a_directory(self, mocker):
        mock_path_get = mocker.patch("pythonanywhere.api.files_api.Files.path_get")
        mock_path_get.return_value = self.default_home_dir_files

        result = Path(self.home_dir_path).contents()

        assert result == self.default_home_dir_files

    def test_raises_when_path_unavailable(self, mocker):
        mock_path_get = mocker.patch("pythonanywhere.api.files_api.Files.path_get")
        mock_path_get.side_effect = Exception("error msg")

        with pytest.raises(Exception) as e:
            Path('/home/different_user').contents()

        assert str(e.value) == "error msg"


@pytest.mark.files
class TestPathDelete(TestFiles):
    def test_informes_about_successful_file_deletion(self, mocker):
        mock_delete = mocker.patch("pythonanywhere.api.files_api.Files.path_delete")
        mock_delete.return_value.status_code = 204
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_info = mocker.patch("pythonanywhere.files.logger.info")
        path = "/valid/path"

        Path(path).delete()

        assert mock_delete.call_args == call(path)
        assert mock_snake.call_args == call(f"{path} deleted!")
        assert mock_info.call_args == call(mock_snake.return_value)

    def test_warns_about_failed_deletion(self, mocker):
        mock_delete = mocker.patch("pythonanywhere.api.files_api.Files.path_delete")
        mock_delete.side_effect = Exception("error msg")
        mock_snake = mocker.patch("pythonanywhere.files.snakesay")
        mock_warning = mocker.patch("pythonanywhere.files.logger.warning")
        undeletable_path = "/home/"

        Path(undeletable_path).delete()

        assert mock_snake.call_args == call("error msg")
