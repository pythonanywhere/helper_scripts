import typer

from pythonanywhere.task import Task

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


@app.command()
def delete():
    raise NotImplementedError


@app.command()
def describe():
    raise NotImplementedError


@app.command("list")
def list_():
    raise NotImplementedError


@app.command()
def update():
    raise NotImplementedError
