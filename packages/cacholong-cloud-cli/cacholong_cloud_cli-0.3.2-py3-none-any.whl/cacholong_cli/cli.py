import importlib.metadata

import os
import sys
import typer
from typing import Optional
from cacholong_cli.commands import (
    accounts,
    addresses,
    companies,
    dns_records,
    dns_templates,
    dns_zones,
    products,
    purchases,
)
from cacholong_cli.common import OutputFormat
from xdg import BaseDirectory


# Version of our CLI
__version__ = importlib.metadata.version("cacholong-cloud-cli")

# Check if required config.ini file exists
configpath = BaseDirectory.save_config_path("cacholong-cli")
if not os.path.exists(os.path.join(configpath, "config.ini")):
    print("Get a token through our panel at https://cp.cacholong.eu/")
    token = input("API Token: ")
    if len(token) == 0:
        print("Invalid token")
        sys.exit(1)
    with open(os.path.join(configpath, "config.ini"), "w") as f:
        f.write("[DEFAULT]\n")
        f.write("api_url = 'https://api.cacholong.eu/api/v1/'\n")
        f.write("api_key = '" + token + "'\n")

# Generate the available commands
app = typer.Typer()
app.add_typer(accounts.app, name="accounts", help="Manage accounts")
app.add_typer(
    addresses.app, name="addresses", help="Manage addresses for users and companies"
)
app.add_typer(companies.app, name="companies", help="Manage companies")
app.add_typer(dns_records.app, name="dns-records", help="Manage DNS records")
app.add_typer(dns_templates.app, name="dns-templates", help="Manage DNS templates")
app.add_typer(dns_zones.app, name="dns-zones", help="Manage DNS zones")
app.add_typer(products.app, name="products", help="Manage products")
app.add_typer(purchases.app, name="purchases", help="Manage purchases")


# Handle version
def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"cacholong cli version: {__version__}")
        raise typer.Exit()


def _verbose_callback(ctx: typer.Context, value: bool) -> None:
    ctx.obj["verbose"] = False
    if value:
        ctx.obj["verbose"] = True


def _output_callback(ctx: typer.Context, value: OutputFormat) -> None:
    ctx.obj["output"] = value


def _create_issue_callback(ctx: typer.Context, value: bool) -> None:
    ctx.obj["create_issue"] = value


def _sync_callback(ctx: typer.Context, value: bool) -> None:
    ctx.obj["sync"] = value


def _sort_callback(ctx: typer.Context, value: str) -> None:
    ctx.obj["sort"] = value


@app.callback(context_settings={"obj": {}})
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    verbose: Optional[bool] = typer.Option(
        None, "--verbose", help="Verbose output", callback=_verbose_callback
    ),
    sort: Optional[str] = typer.Option(
        "-created_at", "--sort", help="Field to sort on", callback=_sort_callback
    ),
    create_issue: bool = typer.Option(
        False,
        "--create-issue",
        help="Create an issue in gitlab",
        callback=_create_issue_callback,
    ),
    sync: bool = typer.Option(
        False, "--sync", help="Process action directly", callback=_sync_callback
    ),
    output: OutputFormat = typer.Option(
        "table", "--output", help="Output format", callback=_output_callback
    ),
) -> None:

    return
