#!/usr/bin/python3
import getpass

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
        help="Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]",
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


@app.command()
def delete_logs():
    raise NotImplementedError


@app.command()
def install_ssl():
    raise NotImplementedError


@app.command()
def reload(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]",
    )
):
    domain_name = ensure_domain(domain_name)
    webapp = Webapp(domain_name)
    webapp.reload()
    typer.echo(snakesay(f"{domain_name} has been reloaded"))
