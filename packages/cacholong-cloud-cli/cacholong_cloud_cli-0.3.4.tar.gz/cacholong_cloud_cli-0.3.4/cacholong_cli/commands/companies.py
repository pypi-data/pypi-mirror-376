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
from cacholong_sdk import Company, CompanyModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def show(
    ctx: typer.Context,
    company_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = Company(conn)
            model = await ctrl.fetch(company_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def update(
    ctx: typer.Context,
    company_id: Annotated[UUID, typer.Argument()],
    name: Annotated[
        Optional[str],
        typer.Option(
            help="Must be unique. Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, numbers 0 to 9, space, point or the folowing symbols: @ & + - ( ) ? ! * # /"
        ),
    ] = None,
    kvknr: Annotated[Optional[str], typer.Option(help="")] = None,
    phone: Annotated[
        Optional[str],
        typer.Option(help="Can contain valid phonenumber from NL,BE,DE,GB or US."),
    ] = None,
    email: Annotated[
        Optional[str],
        typer.Option(
            help="Email will be validated and DNS records checked to make sure server accepts emails."
        ),
    ] = None,
    email_invoice: Annotated[
        Optional[str],
        typer.Option(
            help="Email for invoicing, defaults to email if not given. Email will be validated and DNS records checked to make sure server accepts emails."
        ),
    ] = None,
    vat_number: Annotated[
        Optional[str],
        typer.Option(
            help="VAT number, must be valid. If not given, it will be set to null. If given, it will be validated."
        ),
    ] = None,
    account: Annotated[
        Optional[UUID],
        typer.Option(help="Existing account. Must be unique. Readonly on update."),
    ] = None,
    addresses: Annotated[
        Optional[List[UUID]], typer.Option(help="Existing addresses. Readonly.")
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = Company(conn)
            model = await ctrl.fetch(company_id)
            if name is not None:
                model["name"] = name
            if kvknr is not None:
                model["kvknr"] = kvknr
            if phone is not None:
                model["phone"] = phone
            if email is not None:
                model["email"] = email
            if email_invoice is not None:
                model["email_invoice"] = email_invoice
            if vat_number is not None:
                model["vat_number"] = vat_number
            if account is not None:
                model["account"].set(account, "accounts")
            if addresses is not None:
                model["addresses"].set(addresses, "addresses")
    except DocumentError as e:
        await print_document_error(e)
