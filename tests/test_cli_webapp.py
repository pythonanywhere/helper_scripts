import getpass
from unittest.mock import Mock, call

from typer.testing import CliRunner

from cli.webapp import app

runner = CliRunner()


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


def test_reload(mocker):
    mock_webapp = mocker.patch("cli.webapp.Webapp")
    mocker.patch("cli.webapp.ensure_domain", Mock(side_effect=lambda x: x))
    domain_name = "foo.bar.baz"

    result = runner.invoke(app, ["reload", "-d", domain_name])

    assert f"{domain_name} has been reloaded" in result.stdout
    mock_webapp.assert_called_once_with(domain_name)
    assert mock_webapp.return_value.method_calls == [call.reload()]
