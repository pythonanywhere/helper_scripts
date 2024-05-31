import getpass
from unittest.mock import call, Mock

import pytest
from typer.testing import CliRunner

from cli.schedule import app, delete_app
from pythonanywhere.scripts_commons import tabulate_formats

runner = CliRunner()


@pytest.fixture
def task_list(mocker):
    username = getpass.getuser()
    specs1 = {
        "can_enable": False,
        "command": "echo foo",
        "enabled": True,
        "expiry": None,
        "extend_url": f"/user/{username}/schedule/task/42/extend",
        "hour": 16,
        "task_id": 42,
        "interval": "daily",
        "logfile": "/user/{username}/files/var/log/tasklog-126708-daily-at-1600-echo_foo.log",
        "minute": 0,
        "printable_time": "16:00",
        "url": f"/api/v0/user/{username}/schedule/42",
        "user": username,
    }
    specs2 = {**specs1}
    specs2.update({"task_id": 43, "enabled": False})
    mock_task_list = mocker.patch("cli.schedule.TaskList")
    mock_task_list.return_value.tasks = [Mock(**specs1), Mock(**specs2)]
    return mock_task_list


@pytest.fixture
def mock_confirm(mocker):
    return mocker.patch("cli.schedule.typer.confirm")


def test_main_subcommand_without_args_prints_help():
    result = runner.invoke(
        app,
        [],
    )
    assert result.exit_code == 0
    assert "Show this message and exit." in result.stdout


class TestSet:
    def test_calls_all_stuff_in_right_order(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger")
        mock_task_to_be_created = mocker.patch("cli.schedule.Task.to_be_created")

        runner.invoke(
            app,
            [
                "set",
                "--command",
                "echo foo",
                "--hour",
                "8",
                "--minute",
                "10",
            ],
        )

        assert mock_logger.call_args == call(set_info=True)
        assert mock_task_to_be_created.call_args == call(
            command="echo foo", hour=8, minute=10, disabled=False
        )
        assert mock_task_to_be_created.return_value.method_calls == [
            call.create_schedule()
        ]

    def test_validates_minutes(self):
        result = runner.invoke(app, ["set", "-c", "echo foo", "-h", "8", "-m", "66"])

        assert "Invalid value" in result.stdout
        assert "66 is not in the range 0<=x<=59" in result.stdout

    def test_validates_hours(self):
        result = runner.invoke(app, ["set", "-c", "echo foo", "-h", "66", "-m", "1"])
        assert "Invalid value" in result.stdout
        assert "66 is not in the range 0<=x<=23" in result.stdout

    def test_logs_warning_when_create_schedule_raises(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger").return_value
        mock_snakesay = mocker.patch("cli.schedule.snakesay")
        mock_task_to_be_created = mocker.patch("cli.schedule.Task.to_be_created")
        error_msg = (
            "POST to set new task via API failed, got <Response [403]>: "
            '{"detail":"You have reached your maximum number of scheduled tasks"}'
        )
        mock_task_to_be_created.return_value.create_schedule.side_effect = Exception(error_msg)

        runner.invoke(app, ["set", "--command", "echo foo", "--minute", "13"])

        assert mock_snakesay.call_args == call(error_msg)
        assert mock_logger.warning.call_args == call(mock_snakesay.return_value)


class TestDeleteAllTasks:
    def test_deletes_all_tasks_with_user_permission(self, task_list, mock_confirm):
        mock_confirm.return_value = True

        runner.invoke(delete_app, ["all"])

        assert mock_confirm.call_args == call(
            "This will irrevocably delete all your tasks, proceed?"
        )
        assert task_list.call_count == 1
        for task in task_list.return_value.tasks:
            assert task.method_calls == [call.delete_schedule()]

    def test_exits_when_user_changes_mind(self, task_list, mock_confirm):
        mock_confirm.return_value = False

        runner.invoke(delete_app, ["all"])

        assert task_list.call_count == 0

    def test_deletes_all_tasks_when_forced(self, task_list, mock_confirm):
        runner.invoke(delete_app, ["all", "--force"])

        assert mock_confirm.call_count == 0
        assert task_list.call_count == 1
        for task in task_list.return_value.tasks:
            assert task.method_calls == [call.delete_schedule()]

    def test_sets_logging_to_info(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger")

        runner.invoke(delete_app, ["all"])

        assert mock_logger.call_args == call(set_info=True)


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

    def test_sets_logging_to_info(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger")

        runner.invoke(delete_app, ["id", "24", "42"])

        assert mock_logger.call_args == call(set_info=True)


@pytest.fixture()
def task_from_id(mocker):
    user = getpass.getuser()
    specs = {
        "can_enable": False,
        "command": "echo foo",
        "enabled": True,
        "expiry": "2999-01-13",
        "hour": 10,
        "interval": "daily",
        "logfile": f"/user/{user}/files/foo",
        "minute": 23,
        "printable_time": "10:23",
        "task_id": 42,
        "username": user,
    }
    task = mocker.patch("cli.schedule.get_task_from_id")
    for spec, value in specs.items():
        setattr(task.return_value, spec, value)
    yield task


class TestGet:
    def test_logs_all_task_specs_using_tabulate(self, mocker, task_from_id):
        mock_tabulate = mocker.patch("cli.schedule.tabulate")
        mock_snakesay = mocker.patch("cli.schedule.snakesay")
        mock_logger = mocker.patch("cli.schedule.get_logger").return_value

        runner.invoke(app, ["get", "42"])

        assert task_from_id.call_args == call(42)
        assert mock_snakesay.call_count == 0
        assert mock_tabulate.call_args == call(
            [
                ["command", "echo foo"],
                ["enabled", True],
                ["expiry", "2999-01-13"],
                ["hour", 10],
                ["interval", "daily"],
                ["logfile", f"/user/{getpass.getuser()}/files/foo"],
                ["minute", 23],
                ["printable_time", "10:23"],
            ],
            tablefmt="simple",
        )
        assert mock_logger.info.call_args_list == [
            call("Task 42 specs: "),
            call(mock_tabulate.return_value)
        ]

    def test_logs_all_task_specs_using_snakesay(self, mocker, task_from_id):
        mock_tabulate = mocker.patch("cli.schedule.tabulate")
        mock_snakesay = mocker.patch("cli.schedule.snakesay")
        mock_logger = mocker.patch("cli.schedule.get_logger").return_value

        runner.invoke(app, ["get", "42", "--snakesay"])

        assert task_from_id.call_args == call(42)
        snake_args = (
            "Task 42 specs: <command>: echo foo, <enabled>: True, <expiry>: 2999-01-13, "
            f"<hour>: 10, <interval>: daily, <logfile>: /user/{getpass.getuser()}/files/foo, "
            "<minute>: 23, <printable_time>: 10:23"
        )
        assert mock_snakesay.call_args == call(snake_args)
        assert mock_tabulate.call_count == 0
        assert mock_logger.info.call_args == call(mock_snakesay.return_value)

    def test_logs_requested_task_spec(self, mocker, task_from_id):
        mock_tabulate = mocker.patch("cli.schedule.tabulate")

        runner.invoke(app, ["get", "42", "--command"])

        assert task_from_id.call_args == call(42)
        assert mock_tabulate.call_args == call([["command", "echo foo"]], tablefmt="simple")

    def test_logs_only_value_of_requested_task_spec(self, mocker, task_from_id):
        mock_tabulate = mocker.patch("cli.schedule.tabulate")
        mock_snakesay = mocker.patch("cli.schedule.snakesay")
        mock_logger = mocker.patch("cli.schedule.get_logger")

        runner.invoke(app, ["get", "42", "--printable-time", "--no-spec"])

        assert mock_tabulate.call_count == 0
        assert mock_snakesay.call_count == 0
        assert task_from_id.call_args == call(42)
        assert mock_logger.call_args == call(set_info=True)
        assert mock_logger.return_value.info.call_args == call("10:23")

    def test_complains_when_no_id_provided(self):
        result = runner.invoke(app, ["get", "--command"])
        assert "Missing argument 'id'" in result.stdout


class TestList:
    def test_logs_table_with_correct_headers_and_values(self, mocker, task_list):
        mock_logger = mocker.patch("cli.schedule.get_logger")
        mock_tabulate = mocker.patch("cli.schedule.tabulate")

        result = runner.invoke(app, ["list", "--format", "orgtbl"])

        headers = "id", "interval", "at", "status", "command"
        attrs = "task_id", "interval", "printable_time", "enabled", "command"
        table = [[getattr(task, attr) for attr in attrs] for task in task_list.return_value.tasks]
        table = [
            ["enabled" if spec == True else "disabled" if spec == False else spec for spec in row]
            for row in table
        ]
        assert mock_logger.call_args == call(set_info=True)
        assert task_list.call_count == 1
        assert mock_tabulate.call_args == call(table, headers, tablefmt="orgtbl")
        assert mock_logger.return_value.info.call_args == call(mock_tabulate.return_value)

    def test_snakesays_when_no_scheduled_tasks(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger").return_value
        mock_tabulate = mocker.patch("cli.schedule.tabulate")
        mock_snakesay = mocker.patch("cli.schedule.snakesay")
        mock_tasks = mocker.patch("cli.schedule.TaskList")
        mock_tasks.return_value.tasks = []

        runner.invoke(app, ["list"])

        assert mock_tabulate.call_count == 0
        assert mock_snakesay.call_args == call("No scheduled tasks")
        assert mock_logger.info.call_args == call(mock_snakesay.return_value)

    def test_warns_when_wrong_format_provided(self, mocker, task_list):
        mock_tabulate = mocker.patch("cli.schedule.tabulate")
        wrong_format = "excel"

        result = runner.invoke(app, ["list", "--format", "excel"])

        assert mock_tabulate.call_count == 0
        assert wrong_format not in tabulate_formats
        assert "Table format has to be one of" in result.stdout


class TestUpdate:
    def test_enables_task_and_sets_porcelain(self, mocker):
        mock_task_from_id = mocker.patch("cli.schedule.get_task_from_id")

        runner.invoke(app, ["update", "42", "--enable", "--porcelain"])

        assert mock_task_from_id.call_args == call(42)
        assert mock_task_from_id.return_value.method_calls == [
            call.update_schedule({"enabled": True}, porcelain=True)
        ]

    def test_turns_off_snakesay(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger")

        runner.invoke(app, ["update", "42", "--quiet"])

        assert mock_logger.return_value.setLevel.call_count == 0

    def test_warns_when_task_update_schedule_raises(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger")
        mock_task_from_id = mocker.patch("cli.schedule.get_task_from_id")
        mock_task_from_id.return_value.update_schedule.side_effect = Exception("error")
        mock_snake = mocker.patch("cli.schedule.snakesay")

        runner.invoke(app, ["update", "42", "--disable"])

        assert mock_snake.call_args == call("error")
        assert mock_logger.return_value.warning.call_args == call(mock_snake.return_value)

    def test_ensures_proper_daily_params(self, mocker):
        mock_task_from_id = mocker.patch("cli.schedule.get_task_from_id")

        result = runner.invoke(app, ["update", "42", "--hourly"])

        assert mock_task_from_id.return_value.update_schedule.call_args == call(
            {"interval": "hourly"}, porcelain=False
        )

    def test_ensures_proper_hourly_params(self, mocker):
        mock_task_from_id = mocker.patch("cli.schedule.get_task_from_id")
        mock_datetime = mocker.patch("cli.schedule.datetime")

        runner.invoke(app, ["update", "42", "--daily"])

        assert mock_task_from_id.return_value.update_schedule.call_args == call(
            {"interval": "daily", "hour": mock_datetime.now.return_value.hour},
            porcelain=False
        )

    def test_validates_minute(self):
        result = runner.invoke(app, ["update", "42", "--minute", "88"])
        assert "88 is not in the range 0<=x<=59" in result.stdout

    def test_validates_hour(self):
        result = runner.invoke(app, ["update", "42", "--daily", "--hour", "33"])
        assert "33 is not in the range 0<=x<=23" in result.stdout

    def test_complains_when_no_id_provided(self):
        result = runner.invoke(app, ["update"])
        assert "Missing argument 'id'" in result.stdout

    def test_exits_early_when_nothing_to_update(self, mocker):
        mock_logger = mocker.patch("cli.schedule.get_logger").return_value
        mock_snakesay = mocker.patch("cli.schedule.snakesay")

        result = runner.invoke(app, ["update", "42"])

        assert mock_snakesay.call_args == call("Nothing to update!")
        assert mock_logger.warning.call_args == call(mock_snakesay.return_value)
        assert result.exit_code == 1
