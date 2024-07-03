from typer.testing import CliRunner

from cli.website import app

runner = CliRunner()


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


def test_create_with_domain_and_command_does_something():
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


