#!/usr/bin/python3

import os
import typer

from pythonanywhere import __version__

os.environ["PYTHONANYWHERE_CLIENT"] = f"pa/{__version__}"

from cli import django
from cli import path
from cli import schedule
from cli import students
from cli import webapp
from cli import website

help = """This is a new experimental PythonAnywhere cli client.

It was build with typer & click under the hood.
"""

app = typer.Typer(help=help, no_args_is_help=True, context_settings={"help_option_names": ["--help", "-h"]})
app.add_typer(
    django.app,
    name="django",
    help="Makes Django Girls tutorial projects deployment easy"
)
app.add_typer(
    path.app,
    name="path",
    help="Perform some operations on files"
)
app.add_typer(
    schedule.app,
    name="schedule",
    help="Manage scheduled tasks"
)
app.add_typer(
    students.app,
    name="students",
    help="Perform some operations on students"
)
app.add_typer(
    webapp.app,
    name="webapp",
    help="Everything for web apps: use this if you're not using our experimental features"
)
app.add_typer(
    website.app,
    name="website",
    help="EXPERIMENTAL: create and manage ASGI websites"
)


if __name__ == "__main__":
    app(prog_name="pa")
