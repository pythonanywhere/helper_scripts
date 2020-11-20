from unittest.mock import Mock, call

from typer.testing import CliRunner

from cli.webapp import app

runner = CliRunner()


def test_reload(mocker):
    mock_webapp = mocker.patch("cli.webapp.Webapp")
    mocker.patch("cli.webapp.ensure_domain", Mock(side_effect=lambda x: x))
    domain_name = "foo.bar.baz"

    result = runner.invoke(app, ["reload", "-d", domain_name])

    assert f"{domain_name} has been reloaded" in result.stdout
    mock_webapp.assert_called_once_with(domain_name)
    assert mock_webapp.return_value.method_calls == [call.reload()]
