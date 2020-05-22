#!/usr/bin/python3.6
"""Create a scheduled task.

Two categories of tasks are available: daily and hourly.
Both kinds require a command to run and scheduled time. In order to create a
daily task provide hour and minute; to create hourly task provide only minute.
If task is intended to be enabled later add --disabled flag.

Usage:
  pa_create_scheduled_task.py --command COMMAND [--hour HOUR] --minute MINUTE
                              [--disabled]

Options:
  -h, --help                  Prints this message
  -c, --command COMMAND       Task's command to be scheduled
  -o, --hour HOUR             Sets the task to be performed daily at HOUR
                              (otherwise the task will be run hourly)
  -m, --minute MINUTE         Minute on which the task will be executed
  -d, --disabled              Creates disabled task (otherwise enabled)

Example:
  Create a daily task to be run at 13:15:

    pa_create_scheduled_task.py --command "echo foo" --hour 13 --minute 15

  Create an inactive hourly task to be run 27 minutes past every hour:

    pa_create_scheduled_task.py --command "echo bar" --minute 27 --disabled

Note:
  Once task is created its behavior may be altered later on with
  `pa_update_scheduled_task.py` or deleted with `pa_delete_scheduled_task.py`
  scripts."""

from docopt import docopt

from pythonanywhere.scripts_commons import ScriptSchema, get_logger
from pythonanywhere.task import Task


def main(*, command, hour, minute, disabled):
    get_logger(set_info=True)
    hour = int(hour) if hour is not None else None
    task = Task.to_be_created(command=command, hour=hour, minute=int(minute), disabled=disabled)
    task.create_schedule()


if __name__ == "__main__":
    schema = ScriptSchema(
        {
            "--command": str,
            "--hour": ScriptSchema.hour,
            "--minute": ScriptSchema.minute,
            "--disabled": ScriptSchema.boolean,
        }
    )
    arguments = schema.validate_user_input(docopt(__doc__))

    main(**arguments)
