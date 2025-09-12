import asyncio
import typer
from typing import List, Optional
from typing_extensions import Annotated
from rich.table import Column
from uuid import UUID
from cacholong_cli.AsyncTyper import AsyncTyper
from cacholong_cli.common import (
    list_resources,
    list_relation_resources,
    show_resource,
    print_document_error,
)
from cacholong_cli.connection import Connection
from cacholong_sdk import Filter, Inclusion, DocumentError, ResourceTuple
from cacholong_sdk import Account, AccountModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def list(
    ctx: typer.Context,
    name: Annotated[
        Optional[str],
        typer.Option(
            help="Must be unique. Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, single or alternative quote, numbers 0 to 9, space or the following symbols: @ & + - ( ) ? ! * # /"
        ),
    ] = None,
    display_name: Annotated[Optional[str], typer.Option(help="")] = None,
    description: Annotated[Optional[str], typer.Option(help="")] = None,
    created_at: Annotated[Optional[str], typer.Option(help="")] = None,
    updated_at: Annotated[Optional[str], typer.Option(help="")] = None,
    account_type: Annotated[
        Optional[str], typer.Option(help="Only available for certain users.")
    ] = None,
    account_account_id: Annotated[
        Optional[str],
        typer.Option(
            help="Only available for certain users. When used, account_account_relation is mandatory."
        ),
    ] = None,
    account_account_relation: Annotated[
        Optional[str],
        typer.Option(
            help="Only available for certain users. When used, account_account_id is mandatory."
        ),
    ] = None,
    company: Annotated[Optional[UUID], typer.Option(help="")] = None,
):
    # Build modifier
    modifier = []
    if name is not None:
        modifier.append(Filter(name=name))
    if display_name is not None:
        modifier.append(Filter(query_str="filter[display_name]=" + str(display_name)))
    if description is not None:
        modifier.append(Filter(description=description))
    if created_at is not None:
        modifier.append(Filter(query_str="filter[created_at]=" + str(created_at)))
    if updated_at is not None:
        modifier.append(Filter(query_str="filter[updated_at]=" + str(updated_at)))
    if account_type is not None:
        modifier.append(Filter(query_str="filter[account_type]=" + str(account_type)))
    if account_account_id is not None:
        modifier.append(
            Filter(query_str="filter[account_account_id]=" + str(account_account_id))
        )
    if account_account_relation is not None:
        modifier.append(
            Filter(
                query_str="filter[account_account_relation]="
                + str(account_account_relation)
            )
        )
    if company is not None:
        modifier.append(Filter(company=str(company)))

    # Table definition
    tabledef = [
        {"header": Column("Id", no_wrap=True), "column": "id"},
        {"header": "Name", "column": "name"},
        {"header": "Display name", "column": "display_name"},
        {"header": "Created", "column": "created_at"},
        {"header": "Updated", "column": "updated_at"},
    ]
    async with Connection() as conn:
        await list_resources(ctx, Account(conn), tabledef, modifier)


@app.async_command()
async def show(
    ctx: typer.Context,
    account_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = Account(conn)
            model = await ctrl.fetch(account_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)
