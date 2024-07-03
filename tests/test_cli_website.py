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


def test_create_with_domain_and_command_creates_it():
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
    assert False, "TODO"


def test_get_with_no_domain_lists_websites():
    result = runner.invoke(
        app,
        [
            "get",
        ],
    )
    assert result.exit_code == 0
    assert False, "TODO"


def test_get_with_domain_gives_details_for_domain():
    result = runner.invoke(
        app,
        [
            "get",
            "-d",
            "www.domain.com",
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0
    assert False, "TODO"


def test_reload_with_no_domain_barfs():
    result = runner.invoke(
        app,
        [
            "reload",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_reload_with_domain_reloads():
    result = runner.invoke(
        app,
        [
            "reload",
            "-d",
            "www.domain.com",
        ],
    )
    assert result.exit_code == 0
    assert False, "TODO"


def test_delete_with_no_domain_barfs():
    result = runner.invoke(
        app,
        [
            "delete",
        ],
    )
    assert result.exit_code != 0
    assert "Missing option" in result.stdout


def test_delete_with_domain_deletes_it():
    result = runner.invoke(
        app,
        [
            "delete",
            "-d",
            "www.domain.com",
        ],
    )
    assert result.exit_code == 0
    assert False, "TODO"

