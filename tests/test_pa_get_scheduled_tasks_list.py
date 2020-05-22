import getpass
from unittest.mock import call

import pytest
from scripts.pa_get_scheduled_tasks_list import main

from pythonanywhere.task import Task


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
        "id": 42,
        "interval": "daily",
        "logfile": "/user/{username}/files/var/log/tasklog-126708-daily-at-1600-echo_foo.log",
        "minute": 0,
        "printable_time": "16:00",
        "url": f"/api/v0/user/{username}/schedule/42",
        "user": username,
    }
    specs2 = {**specs1}
    specs2.update({"id": 43, "enabled": False})
    mock_task_list = mocker.patch("scripts.pa_get_scheduled_tasks_list.TaskList")
    mock_task_list.return_value.tasks = [Task.from_api_specs(specs) for specs in (specs1, specs2)]
    return mock_task_list


@pytest.mark.tasks
class TestGetScheduledTasksList:
    def test_logs_task_list_as_table(self, task_list, mocker):
        mock_tabulate = mocker.patch("scripts.pa_get_scheduled_tasks_list.tabulate")
        mock_logger = mocker.patch("scripts.pa_get_scheduled_tasks_list.get_logger")

        main(tablefmt="orgtbl")

        headers = "id", "interval", "at", "status", "command"
        attrs = "task_id", "interval", "printable_time", "enabled", "command"
        table = [[getattr(task, attr) for attr in attrs] for task in task_list.return_value.tasks]
        table = [
            ["enabled" if spec == True else "disabled" if spec == False else spec for spec in row]
            for row in table
        ]

        assert task_list.call_count == 1
        assert mock_tabulate.call_args == call(table, headers, tablefmt="orgtbl")
        assert mock_logger.call_args == call(set_info=True)
        assert mock_logger.return_value.info.call_count == 1

    def test_snakesays_when_no_active_tasks(self, task_list, mocker):
        mock_snake = mocker.patch("scripts.pa_get_scheduled_tasks_list.snakesay")
        task_list.return_value.tasks = []

        main(tablefmt="simple")

        assert mock_snake.call_args == call("No scheduled tasks")
