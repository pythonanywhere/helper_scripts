import getpass
from unittest.mock import call

import pytest
from scripts.pa_get_scheduled_task_specs import main


@pytest.fixture()
def args():
    yield {
        "task_id": 42,
        "command": None,
        "enabled": None,
        "hour": None,
        "interval": None,
        "logfile": None,
        "minute": None,
        "printable_time": None,
        "snake": None,
        "no_spec": None,
    }


@pytest.fixture()
def task_from_id(mocker):
    user = getpass.getuser()
    specs = {
        "can_enable": False,
        "command": "echo foo",
        "enabled": True,
        "hour": 10,
        "interval": "daily",
        "logfile": f"/user/{user}/files/foo",
        "minute": 23,
        "printable_time": "10:23",
        "task_id": 42,
        "username": user,
    }
    task = mocker.patch("scripts.pa_get_scheduled_task_specs.get_task_from_id")
    for spec, value in specs.items():
        setattr(task.return_value, spec, value)
    yield task


@pytest.mark.tasks
class TestGetScheduledTaskSpecs:
    def test_prints_all_specs_using_tabulate(self, task_from_id, args, mocker):
        mock_tabulate = mocker.patch("scripts.pa_get_scheduled_task_specs.tabulate")

        main(**args)

        assert task_from_id.call_args == call(42)
        assert mock_tabulate.call_args == call(
            [
                ["command", "echo foo"],
                ["enabled", True],
                ["hour", 10],
                ["interval", "daily"],
                ["logfile", f"/user/{getpass.getuser()}/files/foo"],
                ["minute", 23],
                ["printable_time", "10:23"],
            ],
            tablefmt="simple",
        )

    def test_prints_all_specs_using_snakesay(self, task_from_id, args, mocker):
        args.update({"snake": True})
        mock_snakesay = mocker.patch("scripts.pa_get_scheduled_task_specs.snakesay")

        main(**args)

        assert task_from_id.call_args == call(42)
        expected = (
            "Task 42 specs: <command>: echo foo, <enabled>: True, <hour>: 10, <interval>: daily, "
            "<logfile>: /user/{}/files/foo, <minute>: 23, <printable_time>: 10:23".format(
                getpass.getuser()
            )
        )
        assert mock_snakesay.call_args == call(expected)

    def test_logs_only_value(self, task_from_id, args, mocker):
        args.update({"no_spec": True, "printable_time": True})
        mock_logger = mocker.patch("scripts.pa_get_scheduled_task_specs.get_logger")

        main(**args)

        assert task_from_id.call_args == call(42)
        assert mock_logger.call_args == call(set_info=True)
        assert mock_logger.return_value.info.call_args == call("10:23")

    def test_prints_one_spec(self, task_from_id, args, mocker):
        args.update({"command": True})
        mock_tabulate = mocker.patch("scripts.pa_get_scheduled_task_specs.tabulate")

        main(**args)

        assert task_from_id.call_args == call(42)
        assert mock_tabulate.call_args == call([["command", "echo foo"]], tablefmt="simple")
