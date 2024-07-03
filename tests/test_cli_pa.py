from typer.testing import CliRunner

from cli.pa import app

runner = CliRunner()


def test_main_command_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 0
    tidied_output = " ".join([line.replace("│", "").strip() for line in result.stdout.split("\n")])
    assert "This is a new experimental PythonAnywhere cli client." in tidied_output
    assert "Makes Django Girls tutorial projects deployment easy" in tidied_output
    assert "Perform some operations on files" in tidied_output
    assert "Manage scheduled tasks" in tidied_output
    assert "Perform some operations on students" in tidied_output
    assert "Everything for web apps: use this if you're not using our experimental features" in tidied_output
    assert "EXPERIMENTAL: create and manage ASGI websites" in tidied_output


