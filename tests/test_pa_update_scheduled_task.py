import getpass
from datetime import datetime
from unittest.mock import call

import pytest
from scripts.pa_update_scheduled_task import main


@pytest.fixture()
def args():
    yield {
        "task_id": 42,
        "command": None,
        "daily": None,
        "disable": None,
        "enable": None,
        "hour": None,
        "hourly": None,
        "minute": None,
        "porcelain": None,
        "quiet": None,
        "toggle": None,
    }


@pytest.fixture()
def task_from_id(mocker):
    user = getpass.getuser()
    specs = {
        "can_enable": False,
        "command": "echo foo",
        "enabled": False,
        "hour": 10,
        "interval": "daily",
        "logfile": f"/user/{user}/files/foo",
        "minute": 23,
        "printable_time": "10:23",
        "task_id": 42,
        "username": user,
    }
    task = mocker.patch("scripts.pa_update_scheduled_task.get_task_from_id")
    for spec, value in specs.items():
        setattr(task.return_value, spec, value)
    yield task


@pytest.mark.tasks
class TestUpdateScheduledTask:
    def test_enables_task_and_sets_porcelain(self, task_from_id, args):
        args.update({"enable": True, "porcelain": True})

        main(**args)

        assert task_from_id.return_value.update_schedule.call_args == call(
            {"enabled": True}, porcelain="porcelain"
        )
        assert task_from_id.return_value.update_schedule.call_count == 1

    def test_turns_off_snakesay(self, mocker, args, task_from_id):
        mock_logger = mocker.patch("scripts.pa_update_scheduled_task.get_logger")
        args.update({"quiet": True})

        main(**args)

        assert mock_logger.return_value.setLevel.call_count == 0

    def test_warns_when_task_update_schedule_raises(self, task_from_id, args, mocker):
        mock_logger = mocker.patch("scripts.pa_update_scheduled_task.get_logger")
        task_from_id.return_value.update_schedule.side_effect = Exception("error")
        mock_snake = mocker.patch("scripts.pa_update_scheduled_task.snakesay")

        main(**args)

        assert mock_snake.call_args == call("error")
        assert mock_logger.return_value.warning.call_args == call(mock_snake.return_value)

    def test_ensures_proper_daily_params(self, task_from_id, args):
        args.update({"hourly": True})

        main(**args)

        assert task_from_id.return_value.update_schedule.call_args == call(
            {"interval": "hourly"}, porcelain=None
        )

    def test_ensures_proper_hourly_params(self, task_from_id, args, mocker):
        mock_datetime = mocker.patch("scripts.pa_update_scheduled_task.datetime")
        args.update({"daily": True})

        main(**args)

        assert task_from_id.return_value.update_schedule.call_args == call(
            {"interval": "daily", "hour": mock_datetime.now.return_value.hour}, porcelain=None
        )
