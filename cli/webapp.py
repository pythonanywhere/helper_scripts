#!/usr/bin/python3

import typer

from pythonanywhere.api.webapp import Webapp
from pythonanywhere.snakesay import snakesay
from pythonanywhere.utils import ensure_domain

app = typer.Typer()


@app.command()
def reload(
    domain_name: str = typer.Option("your-username.pythonanywhere.com", help="Domain name")
):
    domain_name = ensure_domain(domain_name)
    webapp = Webapp(domain_name)
    webapp.reload()
    typer.echo(snakesay(f"{domain_name} has been reloaded"))
