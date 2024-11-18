#!/usr/bin/python3

from typing_extensions import Annotated

import typer
from snakesay import snakesay
from tabulate import tabulate

from pythonanywhere_core.website import Website
from pythonanywhere_core.exceptions import PythonAnywhereApiException, DomainAlreadyExistsException


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
    try:
        Website().create(domain_name=domain_name, command=command)
    except DomainAlreadyExistsException:
        typer.echo(f"You already have a website for {domain_name}.")
        raise typer.Exit(code=1)
    except PythonAnywhereApiException as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)

    typer.echo(
        snakesay(
            f"All done! Your site is now live at {domain_name}. "
        )
    )


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
    website = Website()
    if domain_name is not None:
        website_info = website.get(domain_name=domain_name)
        tabular_data = [
            ["domain name", website_info["domain_name"]],
            ["cname", website_info["webapp"]["domains"][0].get("cname")],
            ["enabled", website_info["enabled"]],
            ["command", website_info["webapp"]["command"]],
        ]
        if "logfiles" in website_info:
            tabular_data.extend(
                [
                    ["access log", website_info["logfiles"]["access"]],
                    ["error log", website_info["logfiles"]["error"]],
                    ["server log", website_info["logfiles"]["server"]],
                ]
            )
        tabular_data = [[k, v] for k, v in tabular_data if v is not None]

        table = tabulate(tabular_data, tablefmt="simple")
    else:
        websites = website.list()
        table = tabulate(
            [
                [website_info["domain_name"], website_info["enabled"]]
                for website_info in websites
            ],
            headers=["domain name", "enabled"],
            tablefmt="simple"
        )
    typer.echo(table)


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
    Website().reload(domain_name=domain_name)
    typer.echo(snakesay(f"Website {domain_name} has been reloaded!"))


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
    Website().delete(domain_name=domain_name)
    typer.echo(snakesay(f"Website {domain_name} has been deleted!"))


@app.command()
def create_autorenew_cert(
    domain_name: Annotated[
        str,
        typer.Option(
            "-d",
            "--domain",
            help="Domain name, eg. yourusername.pythonanywhere.com or www.mydomain.com",
        )
    ],
):
    """Create and apply an auto-renewing Let's Encrypt certificate for the given domain"""
    Website().auto_ssl(domain_name=domain_name)
    typer.echo(snakesay(f"Applied auto-renewing SSL certificate for {domain_name}!"))
