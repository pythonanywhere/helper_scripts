import getpass
import pytest
from typer.testing import CliRunner

from cli.website import app

runner = CliRunner()

@pytest.fixture
def domain_name():
    return "foo.bar.com"


@pytest.fixture
def command():
    return "/usr/local/bin/uvicorn --uds $DOMAIN_SOCKET main:app"


@pytest.fixture
def website_info(domain_name, command):
    return {
        "domain_name": domain_name,
        "enabled": True,
        "id": 42,
        "user": getpass.getuser(),
        "webapp": {
            "command": command,
            "domains": [
                {
                    "domain_name": domain_name,
                    "enabled": True
                }
            ],
            "id": 42
        }
    }


def test_main_subcommand_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 0
    assert "Show this message and exit." in result.stdout


def test_create_without_domain_barfs():
    result = runner.invoke(
        app,
        [
            "create",
            "-c",
            "some kind of server",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_create_without_command_barfs():
    result = runner.invoke(
        app,
        [
            "create",
            "-d",
            "www.something.com",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_create_with_domain_and_command_creates_it(mocker):
    mock_website = mocker.patch("cli.website.Website")
    result = runner.invoke(
        app,
        [
            "create",
            "-d",
            "www.something.com",
            "-c",
            "some kind of server",
        ],
    )
    assert result.exit_code == 0
    mock_website.return_value.create.assert_called_once_with(
        domain_name="www.something.com",
        command="some kind of server"
    )
    assert "All done!" in result.stdout


def test_get_with_no_domain_lists_websites(mocker, website_info):
    mock_website = mocker.patch("cli.website.Website")
    mock_website.return_value.list.return_value = [website_info]

    result = runner.invoke(
        app,
        [
            "get",
        ],
    )
    assert result.exit_code == 0
    mock_website.return_value.list.assert_called_once()
    assert "You have 1 website(s). " in result.stdout
    assert "foo.bar.com" in result.stdout


def test_get_with_domain_gives_details_for_domain():
    result = runner.invoke(
        app,
        [
            "get",
            "-d",
            "www.domain.com",
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0
    assert False, "TODO"


def test_reload_with_no_domain_barfs():
    result = runner.invoke(
        app,
        [
            "reload",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_reload_with_domain_reloads():
    result = runner.invoke(
        app,
        [
            "reload",
            "-d",
            "www.domain.com",
        ],
    )
    assert result.exit_code == 0
    assert False, "TODO"


def test_delete_with_no_domain_barfs():
    result = runner.invoke(
        app,
        [
            "delete",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_delete_with_domain_deletes_it():
    result = runner.invoke(
        app,
        [
            "delete",
            "-d",
            "www.domain.com",
        ],
    )
    assert result.exit_code == 0
    assert False, "TODO"

