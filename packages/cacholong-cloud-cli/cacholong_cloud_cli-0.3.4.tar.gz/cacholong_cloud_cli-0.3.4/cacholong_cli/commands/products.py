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
from cacholong_sdk import Product, ProductModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def list(
    ctx: typer.Context,
    name: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, numbers 0 to 9, space or point."
        ),
    ] = None,
    product_type: Annotated[
        Optional[str],
        typer.Option(
            help='Please note that "option" is only available for child products.'
        ),
    ] = None,
    price: Annotated[
        Optional[str],
        typer.Option(
            help="Allows the use of both a comma and a period as decimal separator."
        ),
    ] = None,
    default_bill_sequence: Annotated[
        Optional[str],
        typer.Option(help="Only available for products with product_type management."),
    ] = None,
    invoice_description: Annotated[
        Optional[str], typer.Option(help="Default description for the invoice item.")
    ] = None,
    publish_start: Annotated[
        Optional[str], typer.Option(help="Start date of the product.")
    ] = None,
    publish_end: Annotated[
        Optional[str], typer.Option(help="End date of the product.")
    ] = None,
    created_at: Annotated[Optional[str], typer.Option(help="")] = None,
    updated_at: Annotated[Optional[str], typer.Option(help="")] = None,
    parent: Annotated[
        Optional[UUID],
        typer.Option(
            help="If product has parent, existing parent product. Readonly on update."
        ),
    ] = None,
):
    # Build modifier
    modifier = []
    if name is not None:
        modifier.append(Filter(name=name))
    if product_type is not None:
        modifier.append(Filter(query_str="filter[product_type]=" + str(product_type)))
    if price is not None:
        modifier.append(Filter(price=price))
    if default_bill_sequence is not None:
        modifier.append(
            Filter(
                query_str="filter[default_bill_sequence]=" + str(default_bill_sequence)
            )
        )
    if invoice_description is not None:
        modifier.append(
            Filter(query_str="filter[invoice_description]=" + str(invoice_description))
        )
    if publish_start is not None:
        modifier.append(Filter(query_str="filter[publish_start]=" + str(publish_start)))
    if publish_end is not None:
        modifier.append(Filter(query_str="filter[publish_end]=" + str(publish_end)))
    if created_at is not None:
        modifier.append(Filter(query_str="filter[created_at]=" + str(created_at)))
    if updated_at is not None:
        modifier.append(Filter(query_str="filter[updated_at]=" + str(updated_at)))
    if parent is not None:
        modifier.append(Filter(parent=str(parent)))

    # Table definition
    tabledef = [
        {"header": Column("Id", no_wrap=True), "column": "id"},
        {"header": "Name", "column": "name"},
        {"header": "Product type", "column": "product_type"},
        {"header": "Price", "column": "price"},
        {"header": "Publish start", "column": "publish_start"},
        {"header": "Created", "column": "created_at"},
        {"header": "Updated", "column": "updated_at"},
    ]
    async with Connection() as conn:
        await list_resources(ctx, Product(conn), tabledef, modifier)


@app.async_command()
async def show(
    ctx: typer.Context,
    product_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = Product(conn)
            model = await ctrl.fetch(product_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)
