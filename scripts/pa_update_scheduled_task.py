#!/usr/bin/python3.6
"""Update a scheduled task using id and proper specs.

Note that logfile name will change after updating the task but it won't be
created until first execution of the task.
To change interval from hourly to daily use --daily flag and provide --hour.
When --daily flag is not accompanied with --hour, new hour for the task
will be automatically set to current hour.
When changing interval from daily to hourly --hour flag is ignored.

Usage:
  pa_update_scheduled_task.py <id> [--command COMMAND]
                                   [--hour HOUR] [--minute MINUTE]
                                   [--disable | --enable | --toggle-enabled]
                                   [--daily | --hourly]
                                   [--quiet | --porcelain]

Options:
  -h, --help                  Print this message
  -c, --command COMMAND       Changes command to COMMAND (multiword commands
                              should be quoted)
  -o, --hour HOUR             Changes hour to HOUR (in 24h format)
  -m, --minute MINUTE         Changes minute to MINUTE
  -d, --disable               Disables task
  -e, --enable                Enables task
  -t, --toggle-enabled        Toggles enable/disable state
  -a, --daily                 Switches interval to daily (when --hour is not
                              provided, sets it automatically to current hour)
  -u, --hourly                Switches interval to hourly (takes precedence
                              over --hour, i.e. sets hour to None)
  -q, --quiet                 Turns off messages
  -p, --porcelain             Prints message in easy-to-parse format

Example:
  Change command for a scheduled task 42:

    pa_update_scheduled_task 42 --command "echo new command"

  Change interval of the task 42 from hourly to daily to be run at 10 am:

    pa_update_scheduled_task 42 --hour 10

  Change interval of the task 42 from daily to hourly and set new minute:

    pa_update_scheduled_task 42 --minute 13 --hourly"""

import logging
from datetime import datetime

from docopt import docopt

from pythonanywhere.scripts_commons import ScriptSchema, get_logger, get_task_from_id
from pythonanywhere.snakesay import snakesay


def main(*, task_id, **kwargs):
    logger = get_logger()

    if kwargs.pop("hourly"):
        kwargs["interval"] = "hourly"
    if kwargs.pop("daily"):
        kwargs["hour"] = kwargs["hour"] if kwargs["hour"] else datetime.now().hour
        kwargs["interval"] = "daily"

    def parse_opts(*opts):
        candidates = [key for key in opts if kwargs.pop(key, None)]
        return candidates[0] if candidates else None

    if not parse_opts("quiet"):
        logger.setLevel(logging.INFO)

    porcelain = parse_opts("porcelain")
    enable_opt = parse_opts("toggle_enabled", "disable", "enable")

    task = get_task_from_id(task_id)

    params = {key: val for key, val in kwargs.items() if val}
    if enable_opt:
        enabled = {"toggle_enabled": not task.enabled, "disable": False, "enable": True}[
            enable_opt
        ]
        params.update({"enabled": enabled})

    try:
        task.update_schedule(params, porcelain=porcelain)
    except Exception as e:
        logger.warning(snakesay(str(e)))


if __name__ == "__main__":
    schema = ScriptSchema(
        {
            "<id>": ScriptSchema.id_required,
            "--command": ScriptSchema.string,
            "--daily": ScriptSchema.boolean,
            "--disable": ScriptSchema.boolean,
            "--enable": ScriptSchema.boolean,
            "--hour": ScriptSchema.hour,
            "--hourly": ScriptSchema.boolean,
            "--minute": ScriptSchema.minute,
            "--porcelain": ScriptSchema.boolean,
            "--quiet": ScriptSchema.boolean,
            "--toggle-enabled": ScriptSchema.boolean,
        }
    )
    arguments = schema.validate_user_input(
        docopt(__doc__), conversions={"id": "task_id", "toggle-": "toggle_"}
    )

    main(**arguments)
