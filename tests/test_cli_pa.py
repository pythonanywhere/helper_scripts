from typer.testing import CliRunner

from cli.pa import app

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
    assert "Everything for web apps" in result.stdout


