from unittest.mock import call

from typer.testing import CliRunner

from cli.scheduled_task import app

runner = CliRunner()


def test_create_calls_all_stuff_in_right_order(mocker):
    mock_task_to_be_created = mocker.patch("cli.scheduled_task.Task.to_be_created")

    runner.invoke(
        app,
        [
            "create",
            "--command",
            "echo foo",
            "--hour",
            8,
            "--minute",
            10,
        ],
    )

    assert mock_task_to_be_created.call_args == call(
        command="echo foo", hour=8, minute=10, disabled=False
    )
    assert mock_task_to_be_created.return_value.method_calls == [call.create_schedule()]


def test_create_validates_minutes():
    result = runner.invoke(app, ["create", "-c", "echo foo", "-h", 8, "-m", 66])
    assert "Invalid value" in result.stdout
    assert "66 is not in the valid range of 0 to 59" in result.stdout


def test_create_validates_hours():
    result = runner.invoke(app, ["create", "-c", "echo foo", "-h", 66, "-m", 1])
    assert "Invalid value" in result.stdout
    assert "66 is not in the valid range of 0 to 23" in result.stdout
