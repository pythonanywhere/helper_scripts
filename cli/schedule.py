from typing import List

import typer
from tabulate import tabulate

from pythonanywhere.scripts_commons import get_logger, get_task_from_id
from pythonanywhere.snakesay import snakesay
from pythonanywhere.task import Task, TaskList

app = typer.Typer()


@app.command()
def set(
    command: str = typer.Option(
        ..., "-c", "--command", help="Task's command to be scheduled"
    ),
    hour: int = typer.Option(
        None,
        "-h",
        "--hour",
        min=0,
        max=23,
        help="Sets the task to be performed daily at HOUR",
    ),
    minute: int = typer.Option(
        ...,
        "-m",
        "--minute",
        min=0,
        max=59,
        help="Minute on which the task will be executed",
    ),
    disabled: bool = typer.Option(
        False, "-d", "--disabled", help="Creates disabled task (otherwise enabled)"
    ),
):
    """Create a scheduled task.

    Two categories of tasks are available: daily and hourly.
    Both kinds require a command to run and scheduled time. In order to create a
    daily task provide hour and minute; to create hourly task provide only minute.
    If task is intended to be enabled later add --disabled flag.

    Example:
      Create a daily task to be run at 13:15:

        pa schedule set --command "echo foo" --hour 13 --minute 15

      Create an inactive hourly task to be run 27 minutes past every hour:

        pa schedule set --command "echo bar" --minute 27 --disabled

    Note:
      Once task is created its behavior may be altered later on with
      `pa schedule update` or deleted with `pa schedule delete`
      commands."""

    task = Task.to_be_created(
        command=command, hour=hour, minute=minute, disabled=disabled
    )
    task.create_schedule()


delete_app = typer.Typer()
app.add_typer(
    delete_app, name="delete", help="Delete scheduled task(s) by id or nuke'em all."
)


@delete_app.command("nuke", help="Delete all scheduled tasks.")
def delete_all_tasks(
    force: bool = typer.Option(
        False, "-f", "--force", help="Turns off user confirmation before deleting tasks"
    ),
):
    if not force:
        user_response = typer.confirm(
            "This will irrevocably delete all your tasks, proceed?"
        )
        if not user_response:
            return None

    for task in TaskList().tasks:
        task.delete_schedule()


@delete_app.command(
    "id",
    help="""\b
    Delete one or more scheduled tasks by id.
    ID_NUMBERS may be acquired with `pa schedule list`
    """,
)
def delete_task_by_id(id_numbers: List[int] = typer.Argument(...)):
    for task_id in id_numbers:
        task = get_task_from_id(task_id, no_exit=True)
        task.delete_schedule()


@app.command()
def get(
    task_id: int = typer.Argument(..., metavar="id"),
    command: bool = typer.Option(
        False, "-c", "--command", help="Prints task's command"
    ),
    enabled: bool = typer.Option(
        False, "-e", "--enabled", help="Prints task's enabled status (True or False)"
    ),
    expiry: bool = typer.Option(
        False, "-x", "--expiry", help="Prints task's expiry date"
    ),
    minute: bool = typer.Option(
        False, "-m", "--minute", help="Prints task's scheduled minute"
    ),
    hour: bool = typer.Option(
        False, "-o", "--hour", help="Prints task's scheduled hour (if daily)"
    ),
    interval: bool = typer.Option(
        False, "-i", "--interval", help="Prints task's frequency (daily or hourly)"
    ),
    logfile: bool = typer.Option(
        False, "-l", "--logfile", help="Prints task's current log file path"
    ),
    printable_time: bool = typer.Option(
        False, "-p", "--printable-time", help="Prints task's scheduled time"
    ),
    no_spec: bool = typer.Option(
        False, "-n", "--no-spec", help="Prints only values without spec names"
    ),
    snake: bool = typer.Option(
        False, "-s", "--snakesay", help="Turns on snakesay... because why not"
    )
):
    """Get scheduled task's specs.

    Available specs are: command, enabled, interval, hour, minute, printable-time,
    logfile, expiry. If no option specified, script will output all mentioned specs.

    Note that logfile query provides path for current (last) logfile. There may be
    several logfiles for each task.
    If task has been updated (e.g. by `pa_update_scheduled_task.py` script) logfile
    name has been changed too, but the file will not be created until first execution
    of the task. Thus getting logfile path via API call does not necessarily mean the
    file exists on the server yet.

    Note:
    Task ID may be found using pa schedule list command.

    Example:
    Get all specs for task with id 42:

        pa schedule get 42

    Get only logfile name for task with id 42:

        pa schedule get 42 --logfile --no-spec"""

    kwargs = {k: v for k, v in locals().items() if k != "task_id"}
    logger = get_logger(set_info=True)

    task = get_task_from_id(task_id)

    print_snake = kwargs.pop("snake")
    print_only_values = kwargs.pop("no_spec")

    specs = (
        {spec: getattr(task, spec) for spec in kwargs if kwargs[spec]}
        if any([val for val in kwargs.values()])
        else {spec: getattr(task, spec) for spec in kwargs}
    )

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


@app.command("list")
def list_():
    raise NotImplementedError


@app.command()
def update():
    raise NotImplementedError
