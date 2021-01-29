from unittest.mock import call, Mock

import pytest
from typer.testing import CliRunner

from cli.schedule import app, delete_app

runner = CliRunner()


@pytest.fixture
def task_list(mocker):
    mock_task_list = mocker.patch("cli.schedule.TaskList")
    mock_task_list.return_value.tasks = [Mock(task_id=1), Mock(task_id=2)]
    return mock_task_list


@pytest.fixture
def mock_confirm(mocker):
    return mocker.patch("cli.schedule.typer.confirm")


class TestCreate:
    def test_calls_all_stuff_in_right_order(self, mocker):
        mock_task_to_be_created = mocker.patch("cli.schedule.Task.to_be_created")

        runner.invoke(
            app,
            [
                "create",
                "--command",
                "echo foo",
                "--hour",
                "8",
                "--minute",
                "10",
            ],
        )

        assert mock_task_to_be_created.call_args == call(
            command="echo foo", hour=8, minute=10, disabled=False
        )
        assert mock_task_to_be_created.return_value.method_calls == [
            call.create_schedule()
        ]

    def test_validates_minutes(self):
        result = runner.invoke(app, ["create", "-c", "echo foo", "-h", "8", "-m", "66"])

        assert "Invalid value" in result.stdout
        assert "66 is not in the valid range of 0 to 59" in result.stdout

    def test_validates_hours(self):
        result = runner.invoke(app, ["create", "-c", "echo foo", "-h", "66", "-m", "1"])
        assert "Invalid value" in result.stdout
        assert "66 is not in the valid range of 0 to 23" in result.stdout


class TestDeleteAllTasks:
    def test_deletes_all_tasks_with_user_permission(self, task_list, mock_confirm):
        mock_confirm.return_value = True

        runner.invoke(delete_app, ["nuke"])

        assert mock_confirm.call_args == call(
            "This will irrevocably delete all your tasks, proceed?"
        )
        assert task_list.call_count == 1
        for task in task_list.return_value.tasks:
            assert task.method_calls == [call.delete_schedule()]

    def test_exits_when_user_changes_mind(self, task_list, mock_confirm):
        mock_confirm.return_value = False

        runner.invoke(
            delete_app,
            [
                "nuke",
            ],
        )

        assert task_list.call_count == 0

    def test_deletes_all_tasks_when_forced(self, task_list, mock_confirm):
        runner.invoke(delete_app, ["nuke", "--force"])

        assert mock_confirm.call_count == 0
        assert task_list.call_count == 1
        for task in task_list.return_value.tasks:
            assert task.method_calls == [call.delete_schedule()]


class TestDeleteTaskById:
    def test_deletes_one_task(self, mocker):
        mock_task_from_id = mocker.patch("cli.schedule.get_task_from_id")

        runner.invoke(delete_app, ["id", "42"])

        assert mock_task_from_id.call_args == call(42, no_exit=True)
        assert mock_task_from_id.return_value.method_calls == [call.delete_schedule()]

    def test_deletes_some_tasks(self, mocker):
        mock_task_from_id = mocker.patch("cli.schedule.get_task_from_id")

        runner.invoke(delete_app, ["id", "24", "42"])

        assert mock_task_from_id.call_args_list == [
            call(24, no_exit=True),
            call(42, no_exit=True),
        ]
        assert mock_task_from_id.return_value.method_calls == [
            call.delete_schedule(),
            call.delete_schedule(),
        ]
