#!/usr/bin/python3
import getpass
from enum import Enum
from pathlib import Path

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
        "--python-version",
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
    access = "access"
    error = "error"
    server = "server"
    all = "all"


def index_callback(value: str):
    if value == "all" or (value.isnumeric() and int(value) in range(10)):
        return value
    raise typer.BadParameter(
        "log_index has to be 0 for current log, 1-9 for one of archive logs or all for all of them"
    )


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
        "--log-type",
    ),
    log_index: str = typer.Option(
        "all",
        "-i",
        "--log-index",
        callback=index_callback,
        help="0 for current log, 1-9 for one of archive logs or all for all of them",
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
    typer.echo(snakesay("All done!"))


@app.command()
def install_ssl(
    domain_name: str = typer.Argument(
        ...,
        help="Domain name, eg www.mydomain.com",
    ),
    certificate_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
        help="The name of the file containing the combined certificate in PEM format (normally a number of blocks, "
        'each one starting "BEGIN CERTIFICATE" and ending "END CERTIFICATE")',
    ),
    private_key_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        readable=True,
        resolve_path=True,
        help="The name of the file containing the private key in PEM format (a file with one block, "
        'starting with something like "BEGIN PRIVATE KEY" and ending with something like "END PRIVATE KEY")',
    ),
    suppress_reload: bool = typer.Option(
        False,
        help="The website will need to be reloaded in order to activate the new certificate/key combination "
        "-- this happens by default, use this option to suppress it.",
    ),
):
    with open(certificate_file, "r") as f:
        certificate = f.read()

    with open(private_key_file, "r") as f:
        private_key = f.read()

    webapp = Webapp(domain_name)
    webapp.set_ssl(certificate, private_key)
    if not suppress_reload:
        webapp.reload()

    ssl_details = webapp.get_ssl_info()
    typer.echo(
        snakesay(
            "That's all set up now :-)\n"
            f"Your new certificate for {domain_name} will expire\n"
            f"on {ssl_details['not_after'].date().isoformat()},\n"
            "so shortly before then you should renew it\n"
            "and install the new certificate."
        )
    )


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
