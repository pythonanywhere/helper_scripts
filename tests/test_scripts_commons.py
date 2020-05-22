import getpass
import logging
from unittest.mock import call

import pytest

from pythonanywhere.scripts_commons import (
    ScriptSchema,
    get_logger,
    get_task_from_id,
    tabulate_formats,
)


@pytest.mark.tasks
class TestScriptSchema:
    def test_validates_boolean(self):
        schema = ScriptSchema({"--toggle": ScriptSchema.boolean})

        for val in (True, False, None):
            result = schema.validate_user_input({"--toggle": val})
            assert result == {"toggle": val}

    def test_exits_because_boolean_not_satisfied(self, mocker):
        mock_exit = mocker.patch("pythonanywhere.scripts_commons.sys.exit")
        mock_snake = mocker.patch("pythonanywhere.scripts_commons.snakesay")
        mock_warning = mocker.patch("pythonanywhere.scripts_commons.logger.warning")
        schema = ScriptSchema({"--toggle": ScriptSchema.boolean})

        schema.validate_user_input({"--toggle": "not valid value"})

        assert mock_exit.call_args == call(1)
        assert mock_warning.call_count == 1
        assert mock_snake.call_args == call(
            "Key '--toggle' error:\nOr(None, <class 'bool'>) did not validate 'not valid value'\n"
            "'not valid value' should be instance of 'bool'"
        )

    def test_validates_bour(self):
        schema = ScriptSchema({"--hour": ScriptSchema.hour})

        for val in (None, 0, 12, 23):
            result = schema.validate_user_input({"--hour": val})
            assert result == {"hour": val}

    def test_exits_because_hour_not_satisfied(self, mocker):
        mock_exit = mocker.patch("pythonanywhere.scripts_commons.sys.exit")
        mock_snake = mocker.patch("pythonanywhere.scripts_commons.snakesay")
        mock_warning = mocker.patch("pythonanywhere.scripts_commons.logger.warning")
        schema = ScriptSchema({"--hour": ScriptSchema.hour})

        schema.validate_user_input({"--hour": 30})

        assert mock_exit.call_args == call(1)
        assert mock_warning.call_count == 1
        assert mock_snake.call_args == call("--hour has to be in 0..23")

    def test_validates_minute(self):
        schema = ScriptSchema({"--minute": ScriptSchema.minute})

        for val in (None, 1, 30, 59):
            result = schema.validate_user_input({"--minute": val})
            assert result == {"minute": val}

    def test_exits_because_minute_not_satisfied(self, mocker):
        mock_exit = mocker.patch("pythonanywhere.scripts_commons.sys.exit")
        mock_snake = mocker.patch("pythonanywhere.scripts_commons.snakesay")
        mock_warning = mocker.patch("pythonanywhere.scripts_commons.logger.warning")
        schema = ScriptSchema({"--minute": ScriptSchema.minute})

        schema.validate_user_input({"--minute": 60})

        assert mock_exit.call_args == call(1)
        assert mock_warning.call_count == 1
        assert mock_snake.call_args == call("--minute has to be in 0..59")

    def test_validates_using_conversions(self):
        schema = ScriptSchema({"<id>": ScriptSchema.id_required})

        result = schema.validate_user_input({"<id>": 42}, conversions={"id": "task_id"})

        assert result == {"task_id": 42}

    def test_exits_because_id_not_satisfied(self, mocker):
        mock_exit = mocker.patch("pythonanywhere.scripts_commons.sys.exit")
        mock_snake = mocker.patch("pythonanywhere.scripts_commons.snakesay")
        mock_warning = mocker.patch("pythonanywhere.scripts_commons.logger.warning")
        schema = ScriptSchema({"<id>": ScriptSchema.id_required})

        schema.validate_user_input({"<id>": None})

        assert mock_exit.call_args == call(1)
        assert mock_warning.call_count == 1
        assert mock_snake.call_args == call("<id> has to be an integer")

    def test_validates_tabulate_format(self):
        schema = ScriptSchema({"--format": ScriptSchema.tabulate_format})

        for val in tabulate_formats:
            result = schema.validate_user_input({"--format": val})
            assert result == {"format": val}

    def test_exits_because_tabulate_format_not_satisfied(self, mocker):
        mock_exit = mocker.patch("pythonanywhere.scripts_commons.sys.exit")
        mock_snake = mocker.patch("pythonanywhere.scripts_commons.snakesay")
        mock_warning = mocker.patch("pythonanywhere.scripts_commons.logger.warning")
        schema = ScriptSchema({"--format": ScriptSchema.tabulate_format})

        schema.validate_user_input({"--format": "non_existing_format"})

        assert mock_exit.call_args == call(1)
        assert mock_warning.call_count == 1
        assert mock_snake.call_args == call(
            "--format should match one of: plain, simple, github, grid, fancy_grid, pipe, orgtbl, "
            "jira, presto, psql, rst, mediawiki, moinmoin, youtrack, html, latex, latex_raw, "
            "latex_booktabs, textile"
        )


@pytest.mark.tasks
class TestScriptSchemaConvert:
    def test_replaces_default_strings(self):
        was = ("--option", "<arg>")
        should_be = ("option", "arg")

        for string, expected in zip(was, should_be):
            assert ScriptSchema({}).convert(string) == expected

    def test_returns_unchanged_string(self):
        assert ScriptSchema({}).convert("will_not_be_changed") == "will_not_be_changed"


@pytest.mark.tasks
class TestGetLogger:
    def test_returns_pa_logger(self, caplog):
        # get_logger should change logger to WARNING, i.e. level 30
        caplog.set_level(logging.INFO, logger="pythonanywhere")

        logger = get_logger()
        assert logger.name == "pythonanywhere"
        assert logger.level == 30

    def test_returns_pa_logger_info(self, caplog):
        # get_logger should change logger to INFO, i.e. level 20
        caplog.set_level(logging.WARNING, logger="pythonanywhere")

        logger = get_logger(set_info=True)

        assert logger.name == "pythonanywhere"
        assert logger.level == 20


@pytest.mark.tasks
class TestGetTaskFromId:
    def test_returns_task(self, mocker):
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
        mock_task = mocker.patch("pythonanywhere.scripts_commons.Task.from_id")
        for spec, value in specs.items():
            setattr(mock_task.return_value, spec, value)

        task = get_task_from_id(42)

        for spec, value in specs.items():
            assert getattr(task, spec) == value

    def test_catches_exception(self, mocker):
        mock_exit = mocker.patch("pythonanywhere.scripts_commons.sys.exit")
        mock_snakesay = mocker.patch("pythonanywhere.scripts_commons.snakesay")
        mock_warning = mocker.patch("pythonanywhere.scripts_commons.logger.warning")
        mock_task_from_id = mocker.patch("pythonanywhere.task.Task.from_id")
        mock_task_from_id.side_effect = Exception("exception")

        task = get_task_from_id(1)

        assert mock_snakesay.call_args == call("exception")
        assert mock_warning.call_count == 1
        assert mock_exit.call_args == call(1)
