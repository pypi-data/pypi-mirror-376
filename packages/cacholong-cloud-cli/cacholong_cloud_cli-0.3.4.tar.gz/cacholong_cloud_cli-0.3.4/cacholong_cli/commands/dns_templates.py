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
from cacholong_sdk import DnsTemplate, DnsTemplateModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def list(
    ctx: typer.Context,
    name: Annotated[
        Optional[str], typer.Option(help="Must be unique or unique with given account.")
    ] = None,
    created_at: Annotated[Optional[str], typer.Option(help="")] = None,
    updated_at: Annotated[Optional[str], typer.Option(help="")] = None,
    account: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing account. Some users can set this to null, meaning template is not limited to an account."
        ),
    ] = None,
):
    # Build modifier
    modifier = []
    if name is not None:
        modifier.append(Filter(name=name))
    if created_at is not None:
        modifier.append(Filter(query_str="filter[created_at]=" + str(created_at)))
    if updated_at is not None:
        modifier.append(Filter(query_str="filter[updated_at]=" + str(updated_at)))
    if account is not None:
        modifier.append(Filter(account=str(account)))
    modifier.append(Inclusion("account"))

    # Table definition
    tabledef = [
        {"header": Column("Id", no_wrap=True), "column": "id"},
        {"header": "Account", "column": "account", "nested_column": "name"},
        {"header": "Name", "column": "name"},
        {"header": "Created", "column": "created_at"},
        {"header": "Updated", "column": "updated_at"},
    ]
    async with Connection() as conn:
        await list_resources(ctx, DnsTemplate(conn), tabledef, modifier)


@app.async_command()
async def show(
    ctx: typer.Context,
    dns_template_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = DnsTemplate(conn)
            model = await ctrl.fetch(dns_template_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def create(
    ctx: typer.Context,
    name: Annotated[
        str, typer.Option(help="Must be unique or unique with given account.")
    ],
    account: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing account. Some users can set this to null, meaning template is not limited to an account."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = DnsTemplate(conn)
            model = ctrl.create()
            model["name"] = name
            if account is not None:
                model["account"] = ResourceTuple(account, "accounts")
            await ctrl.store(model, ctx.obj["create_issue"])

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def update(
    ctx: typer.Context,
    dns_template_id: Annotated[UUID, typer.Argument()],
    name: Annotated[
        Optional[str], typer.Option(help="Must be unique or unique with given account.")
    ] = None,
    account: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing account. Some users can set this to null, meaning template is not limited to an account."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = DnsTemplate(conn)
            model = await ctrl.fetch(dns_template_id)
            if name is not None:
                model["name"] = name
            if account is not None:
                model["account"].set(account, "accounts")
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def delete(
    ctx: typer.Context,
    dns_template_id: Annotated[List[UUID], typer.Argument()],
):
    try:
        async with Connection() as conn, asyncio.TaskGroup() as tg:
            ctrl = DnsTemplate(conn)
            for resource_id in dns_template_id:
                tg.create_task(ctrl.destroy(resource_id))
    except DocumentError as e:
        await print_document_error(e)
