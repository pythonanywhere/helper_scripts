import getpass
from textwrap import dedent

import pytest
from typer.testing import CliRunner

from cli.path import app

runner = CliRunner()


@pytest.fixture
def home_dir():
    return f"/home/{getpass.getuser()}"


@pytest.fixture
def mock_path(mocker):
    return mocker.patch("cli.path.PAPath", autospec=True)


@pytest.fixture
def mock_homedir_path(mock_path):
    contents = {
        '.bashrc': {'type': 'file', 'url': 'bashrc_file_url'},
        'A_file': {'type': 'file', 'url': 'A_file_url'},
        'a_dir': {'type': 'directory', 'url': 'dir_one_url'},
        'a_file': {'type': 'file', 'url': 'a_file_url'},
        'b_file': {'type': 'file', 'url': 'b_file_url'},
        'dir_two': {'type': 'directory', 'url': 'dir_two_url'},
    }

    mock_path.return_value.contents = contents
    return mock_path


@pytest.fixture
def mock_file_path(mock_path):
    mock_path.return_value.contents = "file contents"
    return mock_path


class TestGet:
    def test_replaces_tilde_in_path(self, mock_path, home_dir):
        runner.invoke(app, ["get", '~'])

        mock_path.assert_called_once_with(home_dir)

    def test_exits_early_when_no_contents_for_given_path(self, mock_path, mocker):
        mock_exit = mocker.patch("cli.path.sys.exit")
        mock_path.return_value.contents = None

        runner.invoke(app, ["get", '~/nonexistent.file'])

        mock_exit.assert_called_once_with(1)

    def test_prints_file_contents_and_exits_when_path_is_file(self, mock_file_path, home_dir):
        result = runner.invoke(app, ["get", "~/some-file"])

        mock_file_path.assert_called_once_with(f"{home_dir}/some-file")
        assert "file contents\n" == result.stdout

    def test_prints_api_contents_and_exits_when_raw_option_set(self, mock_homedir_path):
        result = runner.invoke(app, ["get", "~", "--raw"])

        assert "'.bashrc': {'type': 'file', 'url': 'bashrc_file_url'}" in result.stdout

    def test_lists_only_directories_when_dirs_option_set(self, mock_homedir_path, home_dir):
        result = runner.invoke(app, ["get", "~", "--dirs"])

        assert result.stdout.startswith(home_dir)
        for item, value in mock_homedir_path.return_value.contents.items():
            if value['type'] == 'file':
                assert item not in result.stdout
            elif value['type'] == 'directory':
                assert item in result.stdout

    def test_lists_only_files_when_files_option_set(self, mock_homedir_path, home_dir):
        result = runner.invoke(app, ["get", "~", "--files"])

        assert result.stdout.startswith(home_dir)
        for item, value in mock_homedir_path.return_value.contents.items():
            if value['type'] == 'file':
                assert item in result.stdout
            elif value['type'] == 'directory':
                assert item not in result.stdout

    def test_reverses_directory_content_list_when_reverse_option_set(self, mock_homedir_path):
        result = runner.invoke(app, ["get", "~", "--reverse"])

        expected = dedent(
            """\
            /home/piotr:
            D  dir_two
            F  b_file
            F  a_file
            D  a_dir
            F  A_file
            F  .bashrc
            """
        )

        assert expected == result.stdout

    def test_sorts_directory_content_list_by_type_when_type_option_set(self, mock_homedir_path):
        result = runner.invoke(app, ["get", "~", "--type"])

        expected = dedent(
            """\
            /home/piotr:
            D  a_dir
            D  dir_two
            F  .bashrc
            F  A_file
            F  a_file
            F  b_file
            """
        )

        assert expected == result.stdout

    def test_ignores_options_when_path_is_file(self, mock_file_path):
        result = runner.invoke(app, ["get", "~/some-file", "--type", "--reverse"])

        assert "file contents\n" == result.stdout


class TestTree:
    def test_prints_formatted_tree_when_successfull_api_call(self, mock_path, home_dir):
        mock_path.return_value.tree = [
            f'{home_dir}/README.txt',
            f'{home_dir}/dir_one/',
            f'{home_dir}/dir_one/bar.txt',
            f'{home_dir}/dir_one/nested_one/',
            f'{home_dir}/dir_one/nested_one/foo.txt',
            f'{home_dir}/dir_one/nested_two/',
            f'{home_dir}/empty/',
            f'{home_dir}/dir_two/',
            f'{home_dir}/dir_two/quux',
            f'{home_dir}/dir_two/baz/',
            f'{home_dir}/dir_three/',
            f'{home_dir}/dir_three/last.txt',
        ]

        result = runner.invoke(app, ["tree", "~"])

        print(result.stdout)
        expected = dedent(f"""\
            {home_dir}:
            .
            ├── README.txt
            ├── dir_one/
            │   ├── bar.txt
            │   ├── nested_one/
            │   │   └── foo.txt
            │   └── nested_two/
            ├── empty/
            ├── dir_two/
            │   ├── quux
            │   └── baz/
            └── dir_three/
                └── last.txt
        """)

        assert result.stdout == expected

    def test_does_not_print_tree_when_path_is_incorrect(self, mock_path):
        mock_path.return_value.tree = None

        result = runner.invoke(app, ["tree", "/wrong/path"])

        assert result.stdout == ""

    def test_prints_tree_for_empty_directory(self, mock_path, home_dir):
        mock_path.return_value.tree = []

        result = runner.invoke(app, ["tree", "~/empty_dir"])

        expected = dedent(f"""\
            {home_dir}/empty_dir:
            .

            """)
        assert result.stdout == expected
