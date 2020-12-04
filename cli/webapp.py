#!/usr/bin/python3
import getpass
from enum import Enum

import typer

from pythonanywhere.api.webapp import Webapp
from pythonanywhere.project import Project
from pythonanywhere.snakesay import snakesay
from pythonanywhere.utils import ensure_domain

app = typer.Typer()


@app.command()
def create(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com",
    ),
    python_version: str = typer.Option(
        "3.6",
        "-p",
        "--python_version",
        help="Python version, eg '3.8'",
    ),
    nuke: bool = typer.Option(
        False,
        help="*Irrevocably* delete any existing web app config on this domain. Irrevocably.",
    ),
):
    domain = ensure_domain(domain_name)
    project = Project(domain, python_version)
    project.sanity_checks(nuke=nuke)
    project.virtualenv.create(nuke=nuke)
    project.create_webapp(nuke=nuke)
    project.add_static_file_mappings()
    project.webapp.reload()

    typer.echo(
        snakesay(
            f"All done! Your site is now live at https://{domain}. "
            f"Your web app config screen is here: https://www.pythonanywhere.com/user/{getpass.getuser().lower()}"
            f"/webapps/{domain.replace('.', '_')}"
        )
    )


class LogType(str, Enum):
    access ="access"
    error = "error"
    server = "server"
    all = "all"


class LogIndex(str, Enum):
    current = "0"
    one = "1"
    two = "2"
    three = "3"
    four = "4"
    five = "5"
    six = "6"
    seven = "7"
    eight = "8"
    nine = "9"
    all = "all"


@app.command()
def delete_logs(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com",
    ),
    log_type: LogType = typer.Option(
        LogType.all,
        "-t",
        "--log_type",
    ),
    log_index: LogIndex = typer.Option(
        LogIndex.all,
        "-i",
        "--log_index",
        help="0 for current log, 1-9 for one of archive logs or all for all of them"
    ),
):
    webapp = Webapp(ensure_domain(domain_name))
    log_types = ["access", "error", "server"]
    logs = webapp.get_log_info()
    if log_type == "all" and log_index == "all":
        for key in log_types:
            for log in logs[key]:
                webapp.delete_log(key, log)
    elif log_type == "all":
        for key in log_types:
            webapp.delete_log(key, int(log_index))
    elif log_index == "all":
        for i in logs[log_type]:
            webapp.delete_log(log_type, int(i))
    else:
        webapp.delete_log(log_type, int(log_index))
    typer.echo(snakesay('All done!'))


@app.command()
def install_ssl():
    raise NotImplementedError


@app.command()
def reload(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com",
    )
):
    domain_name = ensure_domain(domain_name)
    webapp = Webapp(domain_name)
    webapp.reload()
    typer.echo(snakesay(f"{domain_name} has been reloaded"))
