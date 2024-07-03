#!/usr/bin/python3
import typer
from typing_extensions import Annotated


app = typer.Typer(no_args_is_help=True)

@app.command()
def create(
    domain_name: Annotated[
        str,
        typer.Option(
            "-d",
            "--domain",
            help="Domain name, eg. yourusername.pythonanywhere.com or www.mydomain.com",
        )
    ],
    command: Annotated[
        str,
        typer.Option(
            "-c",
            "--command",
            help="The command to start up your server",
        )
    ],
):
    """Create an ASGI website"""
    pass


@app.command()
def get(
    domain_name: str = typer.Option(
        None,
        "-d",
        "--domain",
        help="Get details for domain name, eg. yourusername.pythonanywhere.com or www.mydomain.com",
    )
):
    """If no domain name is specified, list all domains.  Otherwise get details for specified domain"""
    pass


@app.command()
def reload(
    domain_name: Annotated[
        str,
        typer.Option(
            "-d",
            "--domain",
            help="Domain name, eg. yourusername.pythonanywhere.com or www.mydomain.com",
        )
    ],
):
    """Reload the website at the given domain"""
    pass


@app.command()
def delete(
    domain_name: Annotated[
        str,
        typer.Option(
            "-d",
            "--domain",
            help="Domain name, eg. yourusername.pythonanywhere.com or www.mydomain.com",
        )
    ],
):
    """Delete the website at the given domain"""
    pass
