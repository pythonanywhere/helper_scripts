import typer.core

from typer.testing import CliRunner

from cli.pa import app

typer.core.rich = None  # Workaround to disable rich output to make testing on github actions easier
# TODO: remove this workaround
runner = CliRunner()


def test_main_command_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 2
    assert "This is a new experimental PythonAnywhere cli client." in result.stderr
    assert "Makes Django Girls tutorial projects deployment easy" in result.stderr
    assert "Perform some operations on files" in result.stderr
    assert "Manage scheduled tasks" in result.stderr
    assert "Perform some operations on students" in result.stderr
    assert "Everything for web apps: use this if you're not using" in result.stderr
    assert "EXPERIMENTAL: create and manage ASGI websites" in result.stderr
