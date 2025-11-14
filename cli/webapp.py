#!/usr/bin/python3
import getpass
from enum import Enum
from pathlib import Path

import typer
from pythonanywhere_core.exceptions import MissingCNAMEException
from pythonanywhere_core.webapp import Webapp
from snakesay import snakesay
from tabulate import tabulate

from pythonanywhere.project import Project
from pythonanywhere.utils import ensure_domain, format_log_deletion_message

app = typer.Typer(no_args_is_help=True)


@app.command(name="list")
def list_():
    """List all your webapps"""
    webapps = Webapp.list_webapps()
    if not webapps:
        typer.echo(snakesay("No webapps found."))
        return

    for webapp in webapps:
        typer.echo(webapp['domain_name'])


@app.command()
def get(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com",
    )
):
    """Get details for a specific webapp"""
    domain_name = ensure_domain(domain_name)
    webapp = Webapp(domain_name)
    webapp_info = webapp.get()

    table = [
        ["Domain", webapp_info['domain_name']],
        ["Python version", webapp_info.get('python_version', 'unknown')],
        ["Source directory", webapp_info.get('source_directory', 'not set')],
        ["Virtualenv path", webapp_info.get('virtualenv_path', 'not set')],
        ["Enabled", webapp_info.get('enabled', 'unknown')]
    ]

    typer.echo(tabulate(table, tablefmt="simple"))


@app.command()
def create(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com",
    ),
    python_version: str = typer.Option(
        "3.8",
        "-p",
        "--python-version",
        help="Python version, eg '3.9'",
    ),
    nuke: bool = typer.Option(
        False,
        help="*Irrevocably* delete any existing web app config on this domain. Irrevocably.",
    ),
):
    """Create a new webapp with virtualenv and project setup"""
    domain = ensure_domain(domain_name)
    project = Project(domain, python_version)
    typer.echo(snakesay("Running sanity checks"))
    project.sanity_checks(nuke=nuke)
    project.virtualenv.create(nuke=nuke)
    project.create_webapp(nuke=nuke)
    project.add_static_file_mappings()
    typer.echo(snakesay(f"Reloading {domain_name} via API"))
    project.reload_webapp()

    typer.echo(
        snakesay(
            f"All done! Your site is now live at https://{domain}. "
            f"Your web app config screen is here: https://www.pythonanywhere.com/user/{getpass.getuser().lower()}"
            f"/webapps/{domain.replace('.', '_')}"
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
    """Reload a webapp to apply code or configuration changes"""
    domain_name = ensure_domain(domain_name)
    webapp = Webapp(domain_name)
    typer.echo(snakesay(f"Reloading {domain_name} via API"))
    try:
        webapp.reload()
    except MissingCNAMEException as e:
        typer.echo(snakesay(str(e)))
    typer.echo(snakesay(f"{domain_name} has been reloaded"))


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
    """Install SSL certificate and private key for a webapp"""
    with open(certificate_file, "r") as f:
        certificate = f.read()

    with open(private_key_file, "r") as f:
        private_key = f.read()

    webapp = Webapp(domain_name)
    webapp.set_ssl(certificate, private_key)
    if not suppress_reload:
        try:
            webapp.reload()
        except MissingCNAMEException as e:
            typer.echo(snakesay(str(e)))

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
    """Delete webapp log files (access, error, server logs)"""
    domain = ensure_domain(domain_name)
    webapp = Webapp(domain)
    log_types = ["access", "error", "server"]
    logs = webapp.get_log_info()
    if log_type == "all" and log_index == "all":
        for key in log_types:
            for log in logs[key]:
                typer.echo(snakesay(format_log_deletion_message(domain, key, log)))
                webapp.delete_log(key, log)
    elif log_type == "all":
        for key in log_types:
            typer.echo(snakesay(format_log_deletion_message(domain, key, int(log_index))))
            webapp.delete_log(key, int(log_index))
    elif log_index == "all":
        for i in logs[log_type]:
            typer.echo(snakesay(format_log_deletion_message(domain, log_type.value, i)))
            webapp.delete_log(log_type, int(i))
    else:
        typer.echo(snakesay(format_log_deletion_message(domain, log_type.value, int(log_index))))
        webapp.delete_log(log_type, int(log_index))
    typer.echo(snakesay("All done!"))


@app.command()
def delete(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com",
    )
):
    """Delete a webapp"""
    domain_name = ensure_domain(domain_name)
    webapp = Webapp(domain_name)
    typer.echo(snakesay(f"Deleting {domain_name} via API"))
    webapp.delete()
    typer.echo(snakesay(f"{domain_name} has been deleted"))
