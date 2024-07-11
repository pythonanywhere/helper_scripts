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
    assert result.exit_code == 0
    assert "This is a new experimental PythonAnywhere cli client." in result.stdout
    assert "Makes Django Girls tutorial projects deployment easy" in result.stdout
    assert "Perform some operations on files" in result.stdout
    assert "Manage scheduled tasks" in result.stdout
    assert "Perform some operations on students" in result.stdout
    assert "Everything for web apps: use this if you're not using" in result.stdout
    assert "EXPERIMENTAL: create and manage ASGI websites" in result.stdout
