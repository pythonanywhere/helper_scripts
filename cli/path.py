import json
import re
import sys

from collections import namedtuple
from pprint import pprint

import typer

from pythonanywhere.files import PAPath
from pythonanywhere.scripts_commons import get_logger

app = typer.Typer()


def setup(path: str, quiet: bool) -> PAPath:
    logger = get_logger(set_info=True)
    if quiet:
        logger.disabled = True
    return PAPath(path)


@app.command()
def get(
    path: str = typer.Argument(..., help="Path to PythonAnywhere file or directory."),
    only_files: bool = typer.Option(False, "-f", "--files", help="List only files."),
    only_dirs: bool = typer.Option(False, "-d", "--dirs", help="List only directories."),
    sort_by_type: bool = typer.Option(False, "-t", "--type", help="Sort by type."),
    sort_reverse: bool = typer.Option(False, "-r", "--reverse", help="Sort in reverse order."),
    raw: bool = typer.Option(
        False, "-a", "--raw", help="Print API response (has effect only for directories)."
    ),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Disable additional logging."),
):
    """
    Get contents of PATH.

    If PATH points to a directory, show list of it's contents.
    If PATH points to a file, print it's contents.
    """
    pa_path = setup(path, quiet)
    contents = pa_path.contents

    if contents is None:
        sys.exit(1)

    if raw or isinstance(contents, str):
        {dict: lambda x: print(json.dumps(x)), str: print}[type(contents)](contents)
        sys.exit()

    NameToType = namedtuple("NameToType", ["name", "type"])
    item = "file" if only_files else "directory" if only_dirs else "every"
    data = [NameToType(k, v["type"]) for k, v in contents.items()]

    if sort_reverse or sort_by_type:
        data.sort(key=lambda x: x.type if sort_by_type else x.name, reverse=sort_reverse)

    typer.echo(f"{pa_path.path}:")
    for name, type_ in data:
        if item == "every":
            typer.echo(f"{type_[0].upper()}  {name}")
        elif type_ == item:
            typer.echo(f"   {name}")


def _format_tree(data, current):
    last_child = "└── "
    next_child = "├── "
    connector  = "│   "
    filler     = "    "

    formatted = []
    level_tracker = set()

    for entry in reversed(data):
        entry = re.sub(r"/$", "\0", entry.replace(current, ""))
        chunks = [cc for cc in entry.split("/") if cc]
        item = chunks[-1].replace("\0", "/")
        level = len(chunks) - 1
        level_tracker = set([lvl for lvl in level_tracker if lvl <= level])
        indents = [connector if lvl in level_tracker else filler for lvl in range(level)]
        indents.append(last_child if level not in level_tracker else next_child)
        level_tracker.add(level)
        formatted.append("".join(indents) + item)

    return "\n".join(reversed(formatted))


@app.command()
def tree(
    path: str = typer.Argument(..., help="Path to PythonAnywhere directory."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Disable additional logging.")
):
    """Show preview of directory contents at PATH in tree-like format (2 levels deep)."""
    pa_path = setup(path, quiet)
    tree = pa_path.tree

    if tree is not None:
        typer.echo(f"{pa_path.path}:")
        typer.echo(".")
        typer.echo(_format_tree(tree, pa_path.path))
    else:
        sys.exit(1)


@app.command()
def upload(
    path: str = typer.Argument(..., help=("Full path of FILE where CONTENTS should be uploaded to.")),
    file: typer.FileBinaryRead = typer.Option(
        ...,
        "-c",
        "--contents",
        help="Path to exisitng file or stdin stream that should be uploaded to PATH."
    ),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Disable additional logging.")
):
    """
    Upload CONTENTS to file at PATH.

    If PATH points to an existing file, it will be overwritten.
    """
    pa_path = setup(path, quiet)
    success = pa_path.upload(file)
    sys.exit(0 if success else 1)


@app.command()
def delete(
    path: str = typer.Argument(..., help="Path to PythonAnywhere file or directory to be deleted."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Disable additional logging.")
):
    """
    Delete file or directory at PATH.

    If PATH points to a user owned directory all its contents will be
    deleted recursively.
    """
    pa_path = setup(path, quiet)
    success = pa_path.delete()
    sys.exit(0 if success else 1)


@app.command()
def share(
    path: str = typer.Argument(..., help="Path to PythonAnywhere file."),
    check: bool = typer.Option(False, "-c", "--check", help="Check sharing status."),
    porcelain: bool = typer.Option(False, "-p", "--porcelain", help="Return sharing url in easy-to-parse format."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Disable logging."),
):
    """Create a sharing link to a file at PATH or check its sharing status."""
    pa_path = setup(path, quiet or porcelain)
    link = pa_path.get_sharing_url() if check else pa_path.share()

    if not link:
        sys.exit(1)
    if porcelain:
        typer.echo(link)


@app.command()
def unshare(
    path: str = typer.Argument(..., help="Path to PythonAnywhere file."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Disable additional logging.")
):
    """Disable sharing link for a file at PATH."""
    pa_path = setup(path, quiet)
    success = pa_path.unshare()
    sys.exit(0 if success else 1)
