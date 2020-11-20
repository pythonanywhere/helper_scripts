#!/usr/bin/python3

import typer

from pythonanywhere.api.webapp import Webapp
from pythonanywhere.snakesay import snakesay
from pythonanywhere.utils import ensure_domain

app = typer.Typer()


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


@app.command()
def delete_logs():
    raise NotImplementedError


@app.command()
def install_ssl():
    raise NotImplementedError
