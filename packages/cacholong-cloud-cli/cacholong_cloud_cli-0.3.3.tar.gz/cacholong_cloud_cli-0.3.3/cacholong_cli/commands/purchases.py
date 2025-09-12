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
from cacholong_sdk import Purchase, PurchaseModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def list(
    ctx: typer.Context,
    product_type: Annotated[
        Optional[str], typer.Option(help="Automatically set based on chosen product.")
    ] = None,
    description: Annotated[
        Optional[str], typer.Option(help="Readonly on update.")
    ] = None,
    units: Annotated[Optional[str], typer.Option(help="")] = None,
    date_purchase: Annotated[Optional[str], typer.Option(help="")] = None,
    date_activation: Annotated[
        Optional[str],
        typer.Option(
            help="Will be stored as UTC time. Multiple formats are allowed such as: Y-m-d | Y-m-d H:i:s"
        ),
    ] = None,
    date_deactivation: Annotated[Optional[str], typer.Option(help="")] = None,
    date_next_bill: Annotated[Optional[str], typer.Option(help="")] = None,
    bill_sequence: Annotated[
        Optional[str],
        typer.Option(
            help="This will indicate the billing sequence. E.g. 1M = monthly, 1Y = yearly."
        ),
    ] = None,
    created_at: Annotated[Optional[str], typer.Option(help="")] = None,
    updated_at: Annotated[Optional[str], typer.Option(help="")] = None,
    account: Annotated[
        Optional[UUID], typer.Option(help="Existing account. Readonly on update.")
    ] = None,
    parent: Annotated[
        Optional[UUID],
        typer.Option(
            help="If purchase has parent, existing purchase. Readonly on update."
        ),
    ] = None,
    product: Annotated[
        Optional[UUID], typer.Option(help="Existing product. Readonly on update.")
    ] = None,
):
    # Build modifier
    modifier = []
    if product_type is not None:
        modifier.append(Filter(query_str="filter[product_type]=" + str(product_type)))
    if description is not None:
        modifier.append(Filter(description=description))
    if units is not None:
        modifier.append(Filter(units=units))
    if date_purchase is not None:
        modifier.append(Filter(query_str="filter[date_purchase]=" + str(date_purchase)))
    if date_activation is not None:
        modifier.append(
            Filter(query_str="filter[date_activation]=" + str(date_activation))
        )
    if date_deactivation is not None:
        modifier.append(
            Filter(query_str="filter[date_deactivation]=" + str(date_deactivation))
        )
    if date_next_bill is not None:
        modifier.append(
            Filter(query_str="filter[date_next_bill]=" + str(date_next_bill))
        )
    if bill_sequence is not None:
        modifier.append(Filter(query_str="filter[bill_sequence]=" + str(bill_sequence)))
    if created_at is not None:
        modifier.append(Filter(query_str="filter[created_at]=" + str(created_at)))
    if updated_at is not None:
        modifier.append(Filter(query_str="filter[updated_at]=" + str(updated_at)))
    if account is not None:
        modifier.append(Filter(account=str(account)))
    if parent is not None:
        modifier.append(Filter(parent=str(parent)))
    if product is not None:
        modifier.append(Filter(product=str(product)))
    modifier.append(Inclusion("account"))
    modifier.append(Inclusion("product"))

    # Table definition
    tabledef = [
        {"header": Column("Id", no_wrap=True), "column": "id"},
        {"header": "Account", "column": "account", "nested_column": "name"},
        {"header": "Product", "column": "product", "nested_column": "name"},
        {"header": "Description", "column": "description"},
        {"header": "Units", "column": "units"},
        {"header": "Date activation", "column": "date_activation"},
        {"header": "Created", "column": "created_at"},
        {"header": "Updated", "column": "updated_at"},
    ]
    async with Connection() as conn:
        await list_resources(ctx, Purchase(conn), tabledef, modifier)


@app.async_command()
async def show(
    ctx: typer.Context,
    purchase_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = Purchase(conn)
            model = await ctrl.fetch(purchase_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)
