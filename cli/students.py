import sys

import typer

from pythonanywhere.scripts_commons import get_logger
from pythonanywhere.students import Students

app = typer.Typer(no_args_is_help=True)


def setup(quiet: bool) -> Students:
    logger = get_logger(set_info=True)
    if quiet:
        logger.disabled = True
    return Students()


@app.command()
def get(
    numbered: bool = typer.Option(
        False, "-n", "--numbered", help="Add ordering numbers."
    ),
    quiet: bool = typer.Option(
        False, "-q", "--quiet", help="Disable additional logging."
    ),
    raw: bool = typer.Option(
        False, "-a", "--raw", help="Print list of usernames from the API response."
    ),
    sort: bool = typer.Option(False, "-s", "--sort", help="Sort alphabetically"),
    sort_reverse: bool = typer.Option(
        False, "-r", "--reverse", help="Sort alphabetically in reverse order"
    ),
):
    """
    Get list of student usernames.
    """

    api = setup(quiet)
    students = api.get()

    if students is None or students == []:
        sys.exit(1)

    if raw:
        typer.echo(students)
        sys.exit()

    if sort or sort_reverse:
        students.sort(reverse=sort_reverse)

    for number, student in enumerate(students, start=1):
        line = f"{number:>3}. {student}" if numbered else student
        typer.echo(line)


@app.command()
def delete(
    student: str = typer.Argument(..., help="Username of a student to be removed."),
    quiet: bool = typer.Option(
        False, "-q", "--quiet", help="Disable additional logging."
    ),
):
    """
    Remove a student from the students list.
    """

    api = setup(quiet)
    result = 0 if api.delete(student) else 1
    sys.exit(result)


@app.command()
def holidays(
    quiet: bool = typer.Option(
        False, "-q", "--quiet", help="Disable additional logging."
    ),
):
    """
    School's out for summer! School's out forever! (removes all students)
    """

    api = setup(quiet)
    students = api.get()

    if not students:
        sys.exit(1)

    result = 0 if all(api.delete(s) for s in students) else 1
    if not quiet:
        typer.echo(
            [
                f"Removed all {len(students)} students!",
                f"Something went wrong, try again",
            ][result]
        )
    sys.exit(result)
