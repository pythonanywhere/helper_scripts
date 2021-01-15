from typing import List

import typer

from pythonanywhere.scripts_commons import get_task_from_id
from pythonanywhere.task import Task, TaskList

app = typer.Typer()


@app.command()
def create(
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

        pa scheduled-task create --command "echo foo" --hour 13 --minute 15

      Create an inactive hourly task to be run 27 minutes past every hour:

        pa scheduled-task create --command "echo bar" --minute 27 --disabled

    Note:
      Once task is created its behavior may be altered later on with
      `pa scheduled-task update` or deleted with `pa scheduled-task delete`
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
    ID_NUMBERS may be acquired with `pa scheduled-task list`
    """,
)
def delete_task_by_id(id_numbers: List[int] = typer.Argument(...)):
    for task_id in id_numbers:
        task = get_task_from_id(task_id, no_exit=True)
        task.delete_schedule()


@app.command()
def describe():
    raise NotImplementedError


@app.command("list")
def list_():
    raise NotImplementedError


@app.command()
def update():
    raise NotImplementedError
