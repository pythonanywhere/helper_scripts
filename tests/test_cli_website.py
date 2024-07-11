import getpass
from unittest.mock import call

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
        "logfiles": {
            "access": f"/var/log/{domain_name}.access.log",
            "error": f"/var/log/{domain_name}.error.log",
            "server": f"/var/log/{domain_name}.server.log",
        },
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
    second_website_info = {"domain_name": "blah.com", "enabled": False}
    mock_website.return_value.list.return_value = [website_info, second_website_info]
    mock_tabulate = mocker.patch("cli.website.tabulate")
    mock_echo = mocker.patch("cli.website.typer.echo")

    result = runner.invoke(
        app,
        [
            "get",
        ],
    )

    assert result.exit_code == 0
    mock_website.return_value.list.assert_called_once()
    assert mock_tabulate.call_args == call(
        [
            [website_info["domain_name"], website_info["enabled"]],
            [second_website_info["domain_name"], second_website_info["enabled"]],
        ],
        headers=["domain name", "enabled"],
        tablefmt="simple",
    )
    mock_echo.assert_called_once_with(mock_tabulate.return_value)


def test_get_with_domain_gives_details_for_domain(mocker, website_info, domain_name):
    mock_website = mocker.patch("cli.website.Website")
    mock_website.return_value.get.return_value = website_info
    mock_tabulate = mocker.patch("cli.website.tabulate")
    mock_echo = mocker.patch("cli.website.typer.echo")

    result = runner.invoke(
        app,
        [
            "get",
            "-d",
            domain_name
        ],
    )

    assert result.exit_code == 0
    mock_website.return_value.get.assert_called_once_with(domain_name=domain_name)
    assert mock_tabulate.call_args == call(
        [
            ["domain name", website_info["domain_name"]],
            ["enabled", website_info["enabled"]],
            ["command", website_info["webapp"]["command"]],
            ["access log", website_info["logfiles"]["access"]],
            ["error log", website_info["logfiles"]["error"]],
            ["server log", website_info["logfiles"]["server"]],
        ],
        tablefmt="simple",
    )
    mock_echo.assert_called_once_with(mock_tabulate.return_value)


def test_get_with_domain_gives_details_for_domain_even_without_logfiles(
        mocker, domain_name, command
):
    website_info = {
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
    mock_website = mocker.patch("cli.website.Website")
    mock_website.return_value.get.return_value = website_info
    mock_tabulate = mocker.patch("cli.website.tabulate")
    mock_echo = mocker.patch("cli.website.typer.echo")

    result = runner.invoke(
        app,
        [
            "get",
            "-d",
            domain_name
        ],
    )

    assert result.exit_code == 0
    mock_website.return_value.get.assert_called_once_with(domain_name=domain_name)
    assert mock_tabulate.call_args == call(
        [
            ["domain name", website_info["domain_name"]],
            ["enabled", website_info["enabled"]],
            ["command", website_info["webapp"]["command"]],
        ],
        tablefmt="simple",
    )
    mock_echo.assert_called_once_with(mock_tabulate.return_value)


def test_reload_with_no_domain_barfs():
    result = runner.invoke(
        app,
        [
            "reload",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_reload_with_domain_reloads(mocker):
    mock_website = mocker.patch("cli.website.Website")
    mock_snakesay = mocker.patch("cli.website.snakesay")
    mock_echo = mocker.patch("cli.website.typer.echo")

    result = runner.invoke(
        app,
        [
            "reload",
            "-d",
            "www.domain.com",
        ],
    )

    assert result.exit_code == 0
    mock_website.return_value.reload.assert_called_once_with(domain_name="www.domain.com")
    mock_snakesay.assert_called_once_with(f"Website www.domain.com has been reloaded!")
    mock_echo.assert_called_once_with(mock_snakesay.return_value)


def test_delete_with_no_domain_barfs():
    result = runner.invoke(
        app,
        [
            "delete",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_delete_with_domain_deletes_it(mocker):
    mock_website = mocker.patch("cli.website.Website")
    mock_snakesay = mocker.patch("cli.website.snakesay")
    mock_echo = mocker.patch("cli.website.typer.echo")

    result = runner.invoke(
        app,
        [
            "delete",
            "-d",
            "www.domain.com",
        ],
    )

    assert result.exit_code == 0
    mock_website.return_value.delete.assert_called_once_with(domain_name="www.domain.com")
    mock_snakesay.assert_called_once_with(f"Website www.domain.com has been deleted!")
    mock_echo.assert_called_once_with(mock_snakesay.return_value)

