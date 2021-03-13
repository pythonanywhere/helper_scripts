import getpass
import re
import sys

from collections import namedtuple
from pprint import pprint

import typer

from pythonanywhere.files import PAPath

app = typer.Typer()


def standarize_path(path):
    return path.replace("~", f"/home/{getpass.getuser()}") if path.startswith("~") else path


@app.command()
def get(
    path: str          = typer.Argument(..., help="Path to PythonAnywhere file or directory"),
    only_files: bool   = typer.Option(False, "-f", "--files",   help="List only files"),
    only_dirs: bool    = typer.Option(False, "-d", "--dirs",    help="List only directories"),
    sort_by_type: bool = typer.Option(False, "-t", "--type",    help="Sort by type"),
    sort_reverse: bool = typer.Option(False, "-r", "--reverse", help="Sort in reverse order"),
    raw: bool          = typer.Option(False, "-a", "--raw",     help="Print API response (if PATH is file that's the only option)"),
):
    """
    Get contents of PATH.
    If PATH points to a directory, show list of it's contents.
    If PATH points to a file, print it's contents.
    """
    path = standarize_path(path)
    contents = PAPath(path).contents

    if contents is None:
        sys.exit(1)

    if raw or type(contents) == str:
        {dict: pprint, str: print}[type(contents)](contents)
        sys.exit()

    NameToType = namedtuple("NameToType", ["name", "type"])
    item = "file" if only_files else "directory" if only_dirs else "every"
    data = [NameToType(k, v["type"]) for k, v in contents.items()]

    if sort_reverse or sort_by_type:
        data.sort(key=lambda x: x.type if sort_by_type else x.name, reverse=sort_reverse)

    print(f"{path}:")
    for name, type_ in data:
        if item == "every":
            print(f"{type_[0].upper()}  {name}")
        elif type_ == item:
            print(f"   {name}")


def _format_tree(data, current):
    last_child = "└── "
    next_child = "├── "
    connector  = "│   "
    filler     = "    "

    formatted = []
    following = []

    for idx, entry in enumerate(reversed(data)):
        entry = re.sub(r"/$", "\0", entry.replace(current, ""))
        chunks = [cc for cc in entry.split('/') if cc]
        item = chunks[-1].replace("\0", "/")

        level = len(chunks) - 1
        following = [ll for ll in following if ll <= level]

        indent = ""
        for lvl in range(level):
            indent += connector if lvl in following else filler
        indent += last_child if level not in following else next_child

        if level not in following:
            following.append(level)

        formatted.append(indent + item)

    return "\n".join(reversed(formatted))


@app.command()
def tree(path: str = typer.Argument(..., help="Path to PythonAnywhere file or directory")):
    path = standarize_path(path)
    tree = PAPath(path).tree

    if tree is not None:
        formatted_tree = _format_tree(tree, path)
        print(f"{path}:")
        print(".")
        print(formatted_tree)


@app.command()
def upload(path: str = typer.Argument(..., help="Path to PythonAnywhere file or directory")):
    pass


@app.command()
def delete(path: str = typer.Argument(..., help="Path to PythonAnywhere file or directory")):
    pass


@app.command()
def share(path: str = typer.Argument(..., help="Path to PythonAnywhere file or directory")):
    pass


@app.command()
def unshare(path: str = typer.Argument(..., help="Path to PythonAnywhere file or directory")):
    pass
