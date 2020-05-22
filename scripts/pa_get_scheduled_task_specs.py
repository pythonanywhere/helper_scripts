#!/usr/bin/python3.6
"""Get current scheduled task's specs file by task id.

Available specs are: command, enabled, interval, hour, minute, printable-time,
logfile, expiry. If no option specified, script will output all mentioned specs.

Note that logfile query provides path for current (last) logfile. There may be
several logfiles for each task.
If task has been updated (e.g. by `pa_update_scheduled_task.py` script) logfile
name has been changed too, but the file will not be created until first execution
of the task. Thus getting logfile path via API call does not necessarily mean the
file exists on the server yet.

Usage:
  pa_get_scheduled_task_specs.py <id> [--command] [--enabled] [--interval]
                                      [--hour] [--minute] [--printable-time]
                                      [--logfile] [--expiry]
                                      [--snakesay | --no-spec]

Options:
  -h, --help                  Prints this message
  -c, --command               Prints task's command
  -e, --enabled               Prints task's enabled status (True or False)
  -i, --interval              Prints task's frequency (daily or hourly)
  -l, --logfile               Prints task's current log file path
  -m, --minute                Prints task's scheduled minute
  -o, --hour                  Prints task's scheduled hour (if daily)
  -p, --printable-time        Prints task's scheduled time
  -x, --expiry                Prints task's expiry date
  -n, --no-spec               Prints only values without spec names
  -s, --snakesay              Turns on snakesay... because why not

Note:
  Task <id> may be found using pa_get_scheduled_tasks_list.py script.

Example:
  Get all specs for task with id 42:

    pa_get_scheduled_task_specs 42

  Get only logfile name for task with id 42:

    pa_get_scheduled_task_specs 42 --logfile --no-spec"""

from docopt import docopt
from tabulate import tabulate

from pythonanywhere.scripts_commons import ScriptSchema, get_logger, get_task_from_id
from pythonanywhere.snakesay import snakesay


def main(*, task_id, **kwargs):
    logger = get_logger(set_info=True)
    task = get_task_from_id(task_id)

    print_snake = kwargs.pop("snake")
    print_only_values = kwargs.pop("no_spec")

    specs = (
        {spec: getattr(task, spec) for spec in kwargs if kwargs[spec]}
        if any([val for val in kwargs.values()])
        else {spec: getattr(task, spec) for spec in kwargs}
    )

    # get user path instead of server path:
    if specs.get("logfile"):
        specs.update({"logfile": task.logfile.replace(f"/user/{task.user}/files", "")})

    intro = f"Task {task_id} specs: "
    if print_only_values:
        specs = "\n".join([str(val) for val in specs.values()])
        logger.info(specs)
    elif print_snake:
        specs = [f"<{spec}>: {value}" for spec, value in specs.items()]
        specs.sort()
        logger.info(snakesay(intro + ", ".join(specs)))
    else:
        table = [[spec, val] for spec, val in specs.items()]
        table.sort(key=lambda x: x[0])
        logger.info(intro)
        logger.info(tabulate(table, tablefmt="simple"))


if __name__ == "__main__":
    schema = ScriptSchema(
        {
            "<id>": ScriptSchema.id_required,
            "--command": ScriptSchema.boolean,
            "--enabled": ScriptSchema.boolean,
            "--expiry": ScriptSchema.boolean,
            "--hour": ScriptSchema.boolean,
            "--interval": ScriptSchema.boolean,
            "--logfile": ScriptSchema.boolean,
            "--minute": ScriptSchema.boolean,
            "--printable-time": ScriptSchema.boolean,
            "--no-spec": ScriptSchema.boolean,
            "--snakesay": ScriptSchema.boolean,
        }
    )
    arguments = schema.validate_user_input(
        docopt(__doc__),
        conversions={
            "id": "task_id",
            "no-": "no_",
            "printable-": "printable_",
            "snakesay": "snake",
        },
    )

    main(**arguments)
