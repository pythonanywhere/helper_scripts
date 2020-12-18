#!/usr/bin/python3

import typer

from pythonanywhere.django_project import DjangoProject
from pythonanywhere.snakesay import snakesay
from pythonanywhere.utils import ensure_domain

app = typer.Typer()


@app.command()
def autoconfigure(
    repo_url: str = typer.Argument(..., help="url of remote git repository of your django project"),
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
    """
    Autoconfigure a Django project from on a github URL.

    \b
    - downloads the repo
    - creates a virtualenv and installs django (or detects a requirements.txt if available)
    - creates webapp via api
    - creates django wsgi configuration file
    - adds static files config
    """
    domain = ensure_domain(domain_name)
    project = DjangoProject(domain, python_version)
    project.sanity_checks(nuke=nuke)
    project.download_repo(repo_url, nuke=nuke),
    project.create_virtualenv(nuke=nuke)
    project.create_webapp(nuke=nuke)
    project.add_static_file_mappings()
    project.find_django_files()
    project.update_wsgi_file()
    project.update_settings_file()
    project.run_collectstatic()
    project.run_migrate()
    project.webapp.reload()
    typer.echo(snakesay(f"All done!  Your site is now live at https://{domain_name}\n"))
    project.start_bash()


@app.command()
def start(
    domain_name: str = typer.Option(
        "your-username.pythonanywhere.com",
        "-d",
        "--domain",
        help="Domain name, eg www.mydomain.com",
    ),
    django_version: str = typer.Option(
        "latest",
        "-j",
        "--django-version",
        help="Django version, eg '3.1.2'",
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
    """
    Create a new Django webapp with a virtualenv.  Defaults to
    your free domain, the latest version of Django and Python 3.6
    """
    domain = ensure_domain(domain_name)
    project = DjangoProject(domain, python_version)
    project.sanity_checks(nuke=nuke)
    project.create_virtualenv(django_version, nuke=nuke)
    project.run_startproject(nuke=nuke)
    project.find_django_files()
    project.update_settings_file()
    project.run_collectstatic()
    project.create_webapp(nuke=nuke)
    project.add_static_file_mappings()

    project.update_wsgi_file()

    project.webapp.reload()

    typer.echo(snakesay(f"All done!  Your site is now live at https://{domain}"))
