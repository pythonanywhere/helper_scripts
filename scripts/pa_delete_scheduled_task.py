#!/usr/bin/python3.6
"""Delete scheduled task(s) by id or nuke'em all.

Usage:
  pa_delete_scheduled_task.py id <num>...
  pa_delete_scheduled_task.py nuke [--force]

Options:
  -h, --help                  Prints this message
  -f, --force                 Turns off user confirmation before deleting tasks

Note:
  Task id <num> may be acquired with `pa_get_scheduled_tasks_list.py` script."""

from docopt import docopt

from pythonanywhere.scripts_commons import ScriptSchema, get_logger, get_task_from_id
from pythonanywhere.task import TaskList


def _delete_all(force):
    if not force:
        if input("This will irrevocably delete all your tasks, proceed? [y/N] ").lower() != "y":
            return None

    for task in TaskList().tasks:
        task.delete_schedule()


def _delete_by_id(id_numbers):
    for task_id in id_numbers:
        task = get_task_from_id(task_id, no_exit=True)
        task.delete_schedule()


def main(*, id_numbers, nuke, force):
    get_logger(set_info=True)

    if nuke:
        _delete_all(force)
    else:
        _delete_by_id(id_numbers)


if __name__ == "__main__":
    schema = ScriptSchema(
        {"id": bool, "<num>": ScriptSchema.id_multi, "nuke": bool, "--force": ScriptSchema.boolean}
    )
    arguments = schema.validate_user_input(docopt(__doc__), conversions={"num": "id_numbers"})
    arguments.pop("id")

    main(**arguments)
