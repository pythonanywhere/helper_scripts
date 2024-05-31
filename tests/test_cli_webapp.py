import getpass
import tempfile
from datetime import datetime
from unittest.mock import call

import pytest
from dateutil.tz import tzutc
from typer.testing import CliRunner

from cli.webapp import app

runner = CliRunner()


@pytest.fixture
def mock_webapp(mocker):
    mock_webapp = mocker.patch("cli.webapp.Webapp")
    mock_webapp.return_value.get_log_info.return_value = {
        "access": [0, 1, 2],
        "error": [0, 1, 2],
        "server": [0, 1, 2],
    }
    return mock_webapp


@pytest.fixture
def domain_name():
    return "foo.bar.baz"


@pytest.fixture(name="file_with_content")
def fixture_file_with_content():
    def file_with_content(content):
        filename = tempfile.NamedTemporaryFile(mode="w", encoding="utf8").name
        with open(filename, "w") as f:
            f.write(content)
        return filename

    return file_with_content


def test_main_subcommand_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 0
    assert "Show this message and exit." in result.stdout


def test_create_calls_all_stuff_in_right_order(mocker):
    mock_project = mocker.patch("cli.webapp.Project")

    result = runner.invoke(
        app,
        [
            "create",
            "-d",
            "www.domain.com",
            "-p",
            "python.version",
            "--nuke",
        ],
    )

    assert mock_project.call_args == call("www.domain.com", "python.version")
    assert mock_project.return_value.method_calls == [
        call.sanity_checks(nuke=True),
        call.virtualenv.create(nuke=True),
        call.create_webapp(nuke=True),
        call.add_static_file_mappings(),
        call.webapp.reload(),
    ]
    assert "All done! Your site is now live at https://www.domain.com" in result.stdout
    assert (
        f"https://www.pythonanywhere.com/user/{getpass.getuser().lower()}/webapps/www_domain_com"
        in result.stdout
    )


def test_delete_all_logs(mock_webapp, domain_name):
    result = runner.invoke(
        app,
        [
            "delete-logs",
            "-d",
            domain_name,
        ],
    )

    mock_webapp.assert_called_once_with(domain_name)
    assert mock_webapp.return_value.delete_log.call_args_list == [
        call("access", 0),
        call("access", 1),
        call("access", 2),
        call("error", 0),
        call("error", 1),
        call("error", 2),
        call("server", 0),
        call("server", 1),
        call("server", 2),
    ]
    assert "All done!" in result.stdout


def test_delete_all_server_logs(mock_webapp, domain_name):
    result = runner.invoke(
        app,
        [
            "delete-logs",
            "-d",
            domain_name,
            "-t",
            "server",
        ],
    )

    mock_webapp.assert_called_once_with(domain_name)
    assert mock_webapp.return_value.delete_log.call_args_list == [
        call("server", 0),
        call("server", 1),
        call("server", 2),
    ]
    assert "All done!" in result.stdout


def test_delete_one_server_logs(mock_webapp, domain_name):
    result = runner.invoke(
        app, ["delete-logs", "-d", "foo.bar.baz", "-t", "server", "-i", "2"]
    )

    mock_webapp.assert_called_once_with(domain_name)
    mock_webapp.return_value.delete_log.assert_called_once_with("server", 2)
    assert "All done!" in result.stdout


def test_delete_all_current_logs(mock_webapp, domain_name):
    result = runner.invoke(app, ["delete-logs", "-d", "foo.bar.baz", "-i", "0"])

    mock_webapp.assert_called_once_with(domain_name)
    assert mock_webapp.return_value.delete_log.call_args_list == [
        call("access", 0),
        call("error", 0),
        call("server", 0),
    ]
    assert "All done!" in result.stdout


def test_validates_log_number(mock_webapp):
    result = runner.invoke(
        app, ["delete-logs", "-d", "foo.bar.baz", "-t", "server", "-i", "10"]
    )
    assert "Invalid value" in result.stdout
    assert "log_index has to be 0 for current" in result.stdout


def test_install_ssl_with_default_reload(mock_webapp, domain_name, file_with_content):
    mock_webapp.return_value.get_ssl_info.return_value = {
        "not_after": datetime(2018, 8, 24, 17, 16, 23, tzinfo=tzutc())
    }
    certificate = "certificate"
    certificate_file = file_with_content(certificate)
    private_key = "private_key"
    private_key_file = file_with_content(private_key)

    result = runner.invoke(
        app,
        ["install-ssl", domain_name, certificate_file, private_key_file],
    )

    mock_webapp.assert_called_once_with(domain_name)
    mock_webapp.return_value.set_ssl.assert_called_once_with(certificate, private_key)
    mock_webapp.return_value.reload.assert_called_once()
    assert f"for {domain_name}" in result.stdout
    assert "2018-08-24," in result.stdout


def test_install_ssl_with_reload_suppressed(
    mock_webapp, domain_name, file_with_content
):
    certificate = "certificate"
    certificate_file = file_with_content(certificate)
    private_key = "private_key"
    private_key_file = file_with_content(private_key)

    runner.invoke(
        app,
        [
            "install-ssl",
            domain_name,
            certificate_file,
            private_key_file,
            "--suppress-reload",
        ],
    )

    mock_webapp.assert_called_once_with(domain_name)
    mock_webapp.return_value.set_ssl.assert_called_once_with(certificate, private_key)
    mock_webapp.return_value.reload.assert_not_called()


def test_reload(mock_webapp, domain_name):
    result = runner.invoke(app, ["reload", "-d", domain_name])

    assert f"{domain_name} has been reloaded" in result.stdout
    mock_webapp.assert_called_once_with(domain_name)
    assert mock_webapp.return_value.method_calls == [call.reload()]
