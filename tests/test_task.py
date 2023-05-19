import getpass
from unittest.mock import call

import pytest

from pythonanywhere.task import Task, TaskList


@pytest.fixture
def task_specs():
    username = getpass.getuser()
    return {
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


@pytest.fixture
def example_task(task_specs):
    task = Task()
    for spec, value in task_specs.items():
        setattr(task, spec, value)
    return task


@pytest.mark.tasks
class TestTaskToBeCreated:
    def test_instantiates_new_daily_enabled(self):
        task = Task.to_be_created(command="myscript.py", hour=8, minute=10, disabled=False)
        assert task.command == "myscript.py"
        assert task.hour == 8
        assert task.minute == 10
        assert task.interval == "daily"
        assert task.enabled is True
        assert task.__repr__() == "Daily task 'myscript.py' ready to be created"

    def test_instantiates_new_hourly_disabled(self):
        task = Task.to_be_created(command="myscript.py", hour=None, minute=10, disabled=True)
        assert task.command == "myscript.py"
        assert task.hour is None
        assert task.minute == 10
        assert task.interval == "hourly"
        assert task.enabled is False
        assert task.__repr__() == "Hourly task 'myscript.py' ready to be created"

    def test_raises_when_to_be_created_gets_wrong_hour(self):
        with pytest.raises(ValueError) as e:
            Task.to_be_created(command="echo foo", hour=25, minute=1)
        assert str(e.value) == "Hour has to be in 0..23"

    def test_raises_when_to_be_created_gets_wrong_minute(self):
        with pytest.raises(ValueError) as e:
            Task.to_be_created(command="echo foo", hour=12, minute=78)
        assert str(e.value) == "Minute has to be in 0..59"


@pytest.mark.tasks
class TestTaskFromId:
    def test_updates_specs(self, task_specs, mocker):
        mock_get_specs = mocker.patch("pythonanywhere.task.Schedule.get_specs")
        mock_get_specs.return_value = task_specs

        task = Task.from_id(task_id=42)

        for spec, expected_value in task_specs.items():
            assert getattr(task, spec) == expected_value
        assert task.__repr__() == "Daily task <42>: 'echo foo' enabled at 16:00"


@pytest.mark.tasks
class TestTaskCreateSchedule:
    def test_creates_daily_task(self, mocker, task_specs):
        mock_create = mocker.patch("pythonanywhere.task.Schedule.create")
        mock_create.return_value = task_specs
        mock_update_specs = mocker.patch("pythonanywhere.task.Task.update_specs")
        task = Task.to_be_created(command="echo foo", hour=16, minute=0, disabled=False)

        task.create_schedule()

        assert mock_update_specs.call_args == call(task_specs)
        assert mock_create.call_count == 1
        assert mock_create.call_args == call(
            {"command": "echo foo", "hour": 16, "minute": 0, "enabled": True, "interval": "daily"}
        )
    def test_creates_daily_midnight_task(self, mocker, task_specs):
        mock_create = mocker.patch("pythonanywhere.task.Schedule.create")
        mock_create.return_value = task_specs
        mock_update_specs = mocker.patch("pythonanywhere.task.Task.update_specs")
        task = Task.to_be_created(command="echo foo", hour=0, minute=0, disabled=False)

        task.create_schedule()

        assert mock_update_specs.call_args == call(task_specs)
        assert mock_create.call_count == 1
        assert mock_create.call_args == call(
            {"command": "echo foo", "hour": 0, "minute": 0, "enabled": True, "interval": "daily"}
        )


@pytest.mark.tasks
class TestTaskDeleteSchedule:
    def test_calls_schedule_delete(self, example_task, mocker):
        mock_delete = mocker.patch("pythonanywhere.task.Schedule.delete")
        mock_delete.return_value = True
        mock_snake = mocker.patch("pythonanywhere.task.snakesay")
        mock_logger = mocker.patch("pythonanywhere.task.logger.info")

        example_task.delete_schedule()

        assert mock_delete.call_args == call(42)
        assert mock_snake.call_args == call("Task 42 deleted!")
        assert mock_logger.call_args == call(mock_snake.return_value)

    def test_raises_when_schedule_delete_fails(self, mocker):
        mock_delete = mocker.patch("pythonanywhere.task.Schedule.delete")
        mock_delete.side_effect = Exception("error msg")

        with pytest.raises(Exception) as e:
            Task().delete_schedule()

        assert str(e.value) == "error msg"
        assert mock_delete.call_count == 1


@pytest.mark.tasks
class TestTaskUpdateSchedule:
    def test_updates_specs_and_prints_porcelain(self, mocker, example_task, task_specs):
        mock_schedule_update = mocker.patch("pythonanywhere.task.Schedule.update")
        mock_info = mocker.patch("pythonanywhere.task.logger.info")
        mock_update_specs = mocker.patch("pythonanywhere.task.Task.update_specs")
        params = {"enabled": False}
        task_specs.update(params)
        mock_schedule_update.return_value = task_specs

        example_task.update_schedule(params, porcelain=True)

        assert mock_schedule_update.call_args == call(
            42,
            {
                "hour": 16,
                "minute": 0,
                "enabled": False,
                "interval": "daily",
                "command": "echo foo",
            },
        )
        assert mock_info.call_args == call("Task 42 updated:\n<enabled> from 'True' to 'False'")
        assert mock_update_specs.call_args == call(task_specs)

    def test_updates_specs_and_snakesays(self, mocker, example_task, task_specs):
        mock_schedule_update = mocker.patch("pythonanywhere.task.Schedule.update")
        mock_info = mocker.patch("pythonanywhere.task.logger.info")
        mock_snake = mocker.patch("pythonanywhere.task.snakesay")
        mock_update_specs = mocker.patch("pythonanywhere.task.Task.update_specs")
        params = {"enabled": False}
        task_specs.update(params)
        mock_schedule_update.return_value = task_specs

        example_task.update_schedule(params, porcelain=False)

        assert mock_info.call_args == call(mock_snake.return_value)
        assert mock_snake.call_args == call("Task 42 updated: <enabled> from 'True' to 'False'")
        assert mock_update_specs.call_args == call(task_specs)

    def test_changes_daily_to_hourly(self, example_task, task_specs, mocker):
        mock_schedule_update = mocker.patch("pythonanywhere.task.Schedule.update")
        mock_update_specs = mocker.patch("pythonanywhere.task.Task.update_specs")
        params = {"interval": "hourly"}
        task_specs.update({**params, "hour": None})
        mock_schedule_update.return_value = task_specs

        example_task.update_schedule(params, porcelain=False)

        assert mock_update_specs.call_args == call(task_specs)

    def test_warns_when_nothing_to_update(self, mocker, example_task, task_specs):
        mock_schedule_update = mocker.patch("pythonanywhere.task.Schedule.update")
        mock_snake = mocker.patch("pythonanywhere.task.snakesay")
        mock_warning = mocker.patch("pythonanywhere.task.logger.warning")
        mock_update_specs = mocker.patch("pythonanywhere.task.Task.update_specs")
        mock_schedule_update.return_value = task_specs
        params = {"enabled": True, "minute": 0}

        example_task.update_schedule(params)

        assert mock_snake.call_args == call("Nothing to update!")
        assert mock_warning.call_args == call(mock_snake.return_value)
        assert mock_update_specs.call_count == 0
        assert mock_schedule_update.call_args == call(
            42, {"hour": 16, "enabled": True, "interval": "daily", "command": "echo foo"},
        )


@pytest.mark.tasks
class TestTaskList:
    def test_instatiates_task_list_calling_proper_methods(self, task_specs, mocker):
        mock_get_list = mocker.patch("pythonanywhere.task.Schedule.get_list")
        mock_get_list.return_value = [task_specs]
        mock_from_specs = mocker.patch("pythonanywhere.task.Task.from_api_specs")

        TaskList()

        assert mock_from_specs.call_args == call(task_specs)
        assert mock_from_specs.call_count == len(mock_get_list.return_value)
        assert mock_get_list.call_count == 1
