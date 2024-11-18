import getpass
from unittest.mock import call

import pytest
from typer.testing import CliRunner

from cli.website import app
from pythonanywhere_core.exceptions import PythonAnywhereApiException, DomainAlreadyExistsException


runner = CliRunner()


@pytest.fixture
def domain_name():
    return "foo.bar.com"


@pytest.fixture
def command():
    return "/usr/local/bin/uvicorn --uds $DOMAIN_SOCKET main:app"


@pytest.fixture
def mock_echo(mocker):
    return mocker.patch("cli.website.typer.echo")


@pytest.fixture
def mock_tabulate(mocker):
    return mocker.patch("cli.website.tabulate")


@pytest.fixture
def mock_website(mocker):
    return mocker.patch("cli.website.Website")


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


def test_create_with_domain_and_command_creates_it(mock_website):
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


def test_create_with_existing_domain(mock_website):
    mock_website.return_value.create.side_effect = DomainAlreadyExistsException
    domain_name = "www.something.com"
    result = runner.invoke(
        app,
        [
            "create",
            "-d",
            domain_name,
            "-c",
            "some kind of server",
        ],
    )
    assert result.exit_code != 0
    mock_website.return_value.create.assert_called_once_with(
        domain_name="www.something.com",
        command="some kind of server"
    )
    assert "You already have a website for www.something.com." in result.stdout


def test_create_with_existing_domain(mock_website):
    mock_website.return_value.create.side_effect = PythonAnywhereApiException("Something terrible has happened.")
    domain_name = "www.something.com"
    result = runner.invoke(
        app,
        [
            "create",
            "-d",
            domain_name,
            "-c",
            "some kind of server",
        ],
    )
    assert result.exit_code != 0
    mock_website.return_value.create.assert_called_once_with(
        domain_name="www.something.com",
        command="some kind of server"
    )
    assert "Something terrible has happened." in result.stdout


def test_get_with_no_domain_lists_websites(mock_echo, mock_tabulate, mock_website, website_info):
    second_website_info = {"domain_name": "blah.com", "enabled": False}
    mock_website.return_value.list.return_value = [website_info, second_website_info]

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


def test_get_with_domain_gives_details_for_domain(
        mock_echo, mock_tabulate, mock_website, website_info, domain_name
):
    mock_website.return_value.get.return_value = website_info

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
        domain_name, command, mock_echo, mock_tabulate, mock_website
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
    mock_website.return_value.get.return_value = website_info

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


def test_get_includes_cname_if_cname_is_present_in_domain(
        domain_name, command, mock_echo, mock_tabulate, mock_website
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
                    "enabled": True,
                    "cname": "the-cname"
                }
            ],
            "id": 42
        }
    }
    mock_website.return_value.get.return_value = website_info

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
            ["cname", website_info["webapp"]["domains"][0]["cname"]],
            ["enabled", website_info["enabled"]],
            ["command", website_info["webapp"]["command"]],
        ],
        tablefmt="simple",
    )
    mock_echo.assert_called_once_with(mock_tabulate.return_value)


def test_get_does_not_include_cname_if_cname_is_not_present_in_domain(
        domain_name, command, mock_echo, mock_tabulate, mock_website
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
                    "enabled": True,
                }
            ],
            "id": 42
        }
    }
    mock_website.return_value.get.return_value = website_info

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


def test_reload_with_domain_reloads(mocker, mock_echo, mock_website):
    mock_snakesay = mocker.patch("cli.website.snakesay")

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


def test_delete_with_domain_deletes_it(mocker, mock_echo, mock_website):
    mock_snakesay = mocker.patch("cli.website.snakesay")

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


def test_create_le_autorenew_cert(mocker, mock_echo, mock_website):
    mock_snakesay = mocker.patch("cli.website.snakesay")

    result = runner.invoke(
        app,
        [
            "create-autorenew-cert",
            "-d",
            "www.domain.com",
        ],
    )

    assert result.exit_code == 0
    mock_website.return_value.auto_ssl.assert_called_once_with(domain_name="www.domain.com")
    mock_snakesay.assert_called_once_with(f"Applied auto-renewing SSL certificate for www.domain.com!")
    mock_echo.assert_called_once_with(mock_snakesay.return_value)

