#!/usr/bin/python3.6
"""Get list of user's scheduled tasks as a table with columns:
id, interval, at (hour:minute/minute past), status (enabled/disabled), command.

Usage:
  pa_get_scheduled_tasks_list.py [--format TABLEFMT]

Options:
  -h, --help                  Prints this message
  -f, --format TABLEFMT       Sets table format supported by tabulate
                              (defaults to 'simple')

Note:
  This script provides an overview of all tasks. Once a task id is
  known and some specific data is required it's more convenient to get
  it using `pa_get_scheduled_task_specs.py` script instead of parsing
  the table."""

from docopt import docopt
from tabulate import tabulate

from pythonanywhere.scripts_commons import ScriptSchema, get_logger
from pythonanywhere.snakesay import snakesay
from pythonanywhere.task import TaskList


def main(tablefmt):
    logger = get_logger(set_info=True)
    headers = "id", "interval", "at", "status", "command"
    attrs = "task_id", "interval", "printable_time", "enabled", "command"

    def get_right_value(task, attr):
        value = getattr(task, attr)
        if attr == "enabled":
            value = "enabled" if value else "disabled"
        return value

    table = [[get_right_value(task, attr) for attr in attrs] for task in TaskList().tasks]
    msg = tabulate(table, headers, tablefmt=tablefmt) if table else snakesay("No scheduled tasks")
    logger.info(msg)


if __name__ == "__main__":
    schema = ScriptSchema({"--format": ScriptSchema.tabulate_format})
    argument = schema.validate_user_input(docopt(__doc__))

    main(argument.get("format", "simple"))
