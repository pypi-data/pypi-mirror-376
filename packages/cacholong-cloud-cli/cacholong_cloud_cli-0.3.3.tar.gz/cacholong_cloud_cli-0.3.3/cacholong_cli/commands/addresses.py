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
from cacholong_sdk import Address, AddressModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def list(
    ctx: typer.Context,
    street: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, single or alternative quote or space."
        ),
    ] = None,
    number: Annotated[
        Optional[str], typer.Option(help="Can contain any number from any language.")
    ] = None,
    suffix: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter or number from any language or space."
        ),
    ] = None,
    zipcode: Annotated[
        Optional[str],
        typer.Option(help="Must contain valid zipcode from NL,BE,DE,GB or US."),
    ] = None,
    city: Annotated[
        Optional[str],
        typer.Option(help="Can contain any letter from any language or space."),
    ] = None,
    state: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, single or alternative quote or space."
        ),
    ] = None,
    country: Annotated[
        Optional[str], typer.Option(help="Must contain two uppercase letters (A-Z).")
    ] = None,
    user: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing user. Required unless company is given. Readonly on update."
        ),
    ] = None,
    company: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing company. Required unless user is given. Readonly on update."
        ),
    ] = None,
):
    # Build modifier
    modifier = []
    if street is not None:
        modifier.append(Filter(street=street))
    if number is not None:
        modifier.append(Filter(number=number))
    if suffix is not None:
        modifier.append(Filter(suffix=suffix))
    if zipcode is not None:
        modifier.append(Filter(zipcode=zipcode))
    if city is not None:
        modifier.append(Filter(city=city))
    if state is not None:
        modifier.append(Filter(state=state))
    if country is not None:
        modifier.append(Filter(country=country))
    if user is not None:
        modifier.append(Filter(user=str(user)))
    if company is not None:
        modifier.append(Filter(company=str(company)))
    modifier.append(Inclusion("company"))
    modifier.append(Inclusion("user"))

    # Table definition
    tabledef = [
        {"header": Column("Id", no_wrap=True), "column": "id"},
        {"header": "Company", "column": "company", "nested_column": "name"},
        {"header": "User", "column": "user", "nested_column": "name"},
        {"header": "Street", "column": "street"},
        {"header": "Number", "column": "number"},
        {"header": "City", "column": "city"},
        {"header": "Created", "column": "created_at"},
        {"header": "Updated", "column": "updated_at"},
    ]
    async with Connection() as conn:
        await list_resources(ctx, Address(conn), tabledef, modifier)


@app.async_command()
async def show(
    ctx: typer.Context,
    address_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = Address(conn)
            model = await ctrl.fetch(address_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def create(
    ctx: typer.Context,
    street: Annotated[
        str,
        typer.Option(
            help="Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, single or alternative quote or space."
        ),
    ],
    number: Annotated[
        str, typer.Option(help="Can contain any number from any language.")
    ],
    zipcode: Annotated[
        str, typer.Option(help="Must contain valid zipcode from NL,BE,DE,GB or US.")
    ],
    city: Annotated[
        str, typer.Option(help="Can contain any letter from any language or space.")
    ],
    country: Annotated[
        str, typer.Option(help="Must contain two uppercase letters (A-Z).")
    ],
    suffix: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter or number from any language or space."
        ),
    ] = None,
    state: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, single or alternative quote or space."
        ),
    ] = None,
    user: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing user. Required unless company is given. Readonly on update."
        ),
    ] = None,
    company: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing company. Required unless user is given. Readonly on update."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = Address(conn)
            model = ctrl.create()
            model["street"] = street
            model["number"] = number
            if suffix is not None:
                model["suffix"] = suffix
            model["zipcode"] = zipcode
            model["city"] = city
            if state is not None:
                model["state"] = state
            model["country"] = country
            if user is not None:
                model["user"] = ResourceTuple(user, "users")
            if company is not None:
                model["company"] = ResourceTuple(company, "companies")
            await ctrl.store(model, ctx.obj["create_issue"])

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def update(
    ctx: typer.Context,
    address_id: Annotated[UUID, typer.Argument()],
    street: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, single or alternative quote or space."
        ),
    ] = None,
    number: Annotated[
        Optional[str], typer.Option(help="Can contain any number from any language.")
    ] = None,
    suffix: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter or number from any language or space."
        ),
    ] = None,
    zipcode: Annotated[
        Optional[str],
        typer.Option(help="Must contain valid zipcode from NL,BE,DE,GB or US."),
    ] = None,
    city: Annotated[
        Optional[str],
        typer.Option(help="Can contain any letter from any language or space."),
    ] = None,
    state: Annotated[
        Optional[str],
        typer.Option(
            help="Can contain any letter (combined with accent) from any language, any kind of hyphen or dash, single or alternative quote or space."
        ),
    ] = None,
    country: Annotated[
        Optional[str], typer.Option(help="Must contain two uppercase letters (A-Z).")
    ] = None,
    user: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing user. Required unless company is given. Readonly on update."
        ),
    ] = None,
    company: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing company. Required unless user is given. Readonly on update."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = Address(conn)
            model = await ctrl.fetch(address_id)
            if street is not None:
                model["street"] = street
            if number is not None:
                model["number"] = number
            if suffix is not None:
                model["suffix"] = suffix
            if zipcode is not None:
                model["zipcode"] = zipcode
            if city is not None:
                model["city"] = city
            if state is not None:
                model["state"] = state
            if country is not None:
                model["country"] = country
            if user is not None:
                model["user"].set(user, "users")
            if company is not None:
                model["company"].set(company, "companies")
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def delete(
    ctx: typer.Context,
    address_id: Annotated[List[UUID], typer.Argument()],
):
    try:
        async with Connection() as conn, asyncio.TaskGroup() as tg:
            ctrl = Address(conn)
            for resource_id in address_id:
                tg.create_task(ctrl.destroy(resource_id))
    except DocumentError as e:
        await print_document_error(e)
