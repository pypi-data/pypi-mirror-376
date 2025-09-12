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
from cacholong_sdk import DnsZone, DnsZoneModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def list(
    ctx: typer.Context,
    external_service_provider_status: Annotated[
        Optional[str], typer.Option(help="Status for external service provider.")
    ] = None,
    domain: Annotated[
        Optional[str],
        typer.Option(
            help="Valid when provided with a domain and TLD (without a protocol)."
        ),
    ] = None,
    active: Annotated[
        Optional[str], typer.Option(help="Is dns zone active or not?")
    ] = None,
    administratively_disabled: Annotated[
        Optional[str],
        typer.Option(
            help="Is dns zone administratively disabled or not? Only visible for certain users."
        ),
    ] = None,
    dnssec: Annotated[
        Optional[str], typer.Option(help="Is dnssec enabled or not?")
    ] = None,
    dnssec_status: Annotated[
        Optional[str], typer.Option(help="Status of DNSSEC.")
    ] = None,
    dnssec_flags: Annotated[
        Optional[str], typer.Option(help="Flag for DNSSEC record.")
    ] = None,
    dnssec_algorithm: Annotated[
        Optional[str], typer.Option(help="Algorithm key code.")
    ] = None,
    dnssec_public_key: Annotated[
        Optional[str], typer.Option(help="Public key for DS record.")
    ] = None,
    created_at: Annotated[Optional[str], typer.Option(help="")] = None,
    updated_at: Annotated[Optional[str], typer.Option(help="")] = None,
    account: Annotated[
        Optional[UUID], typer.Option(help="Account for this dns zone.")
    ] = None,
    name_server_group: Annotated[
        Optional[UUID],
        typer.Option(help="Name server groups for this dns zone. Readonly."),
    ] = None,
    purchase: Annotated[
        Optional[UUID],
        typer.Option(
            help="Purchase for this dns zone. Required if no product is provided."
        ),
    ] = None,
    product: Annotated[
        Optional[UUID],
        typer.Option(
            help="Product for this dns zone. Required if no purchase is provided."
        ),
    ] = None,
):
    # Build modifier
    modifier = []
    if external_service_provider_status is not None:
        modifier.append(
            Filter(
                query_str="filter[external_service_provider_status]="
                + str(external_service_provider_status)
            )
        )
    if domain is not None:
        modifier.append(Filter(domain=domain))
    if active is not None:
        modifier.append(Filter(active=active))
    if administratively_disabled is not None:
        modifier.append(
            Filter(
                query_str="filter[administratively_disabled]="
                + str(administratively_disabled)
            )
        )
    if dnssec is not None:
        modifier.append(Filter(dnssec=dnssec))
    if dnssec_status is not None:
        modifier.append(Filter(query_str="filter[dnssec_status]=" + str(dnssec_status)))
    if dnssec_flags is not None:
        modifier.append(Filter(query_str="filter[dnssec_flags]=" + str(dnssec_flags)))
    if dnssec_algorithm is not None:
        modifier.append(
            Filter(query_str="filter[dnssec_algorithm]=" + str(dnssec_algorithm))
        )
    if dnssec_public_key is not None:
        modifier.append(
            Filter(query_str="filter[dnssec_public_key]=" + str(dnssec_public_key))
        )
    if created_at is not None:
        modifier.append(Filter(query_str="filter[created_at]=" + str(created_at)))
    if updated_at is not None:
        modifier.append(Filter(query_str="filter[updated_at]=" + str(updated_at)))
    if account is not None:
        modifier.append(Filter(account=str(account)))
    if name_server_group is not None:
        modifier.append(
            Filter(query_str="filter[name-server-group]=" + str(name_server_group))
        )
    if purchase is not None:
        modifier.append(Filter(purchase=str(purchase)))
    if product is not None:
        modifier.append(Filter(product=str(product)))
    modifier.append(Inclusion("account"))

    # Table definition
    tabledef = [
        {"header": Column("Id", no_wrap=True), "column": "id"},
        {"header": "Account", "column": "account", "nested_column": "name"},
        {"header": "Domain", "column": "domain"},
        {"header": "Active", "column": "active"},
        {"header": "Dnssec", "column": "dnssec"},
        {
            "header": "External service provider status",
            "column": "external_service_provider_status",
        },
        {"header": "Created", "column": "created_at"},
        {"header": "Updated", "column": "updated_at"},
    ]
    async with Connection() as conn:
        await list_resources(ctx, DnsZone(conn), tabledef, modifier)


@app.async_command()
async def show(
    ctx: typer.Context,
    dns_zone_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = DnsZone(conn)
            model = await ctrl.fetch(dns_zone_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def create(
    ctx: typer.Context,
    domain: Annotated[
        str,
        typer.Option(
            help="Valid when provided with a domain and TLD (without a protocol)."
        ),
    ],
    account: Annotated[UUID, typer.Option(help="Account for this dns zone.")],
    active: Annotated[
        Optional[bool], typer.Option(help="Is dns zone active or not?")
    ] = None,
    dnssec: Annotated[
        Optional[bool], typer.Option(help="Is dnssec enabled or not?")
    ] = None,
    purchase: Annotated[
        Optional[UUID],
        typer.Option(
            help="Purchase for this dns zone. Required if no product is provided."
        ),
    ] = None,
    product: Annotated[
        Optional[UUID],
        typer.Option(
            help="Product for this dns zone. Required if no purchase is provided."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = DnsZone(conn)
            model = ctrl.create()
            model["domain"] = domain
            if active is not None:
                model["active"] = active
            if dnssec is not None:
                model["dnssec"] = dnssec
            model["account"] = ResourceTuple(account, "accounts")
            if purchase is not None:
                model["purchase"] = ResourceTuple(purchase, "purchases")
            if product is not None:
                model["product"] = ResourceTuple(product, "products")
            await ctrl.store(model, ctx.obj["create_issue"])

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def update(
    ctx: typer.Context,
    dns_zone_id: Annotated[UUID, typer.Argument()],
    domain: Annotated[
        Optional[str],
        typer.Option(
            help="Valid when provided with a domain and TLD (without a protocol)."
        ),
    ] = None,
    active: Annotated[
        Optional[bool], typer.Option(help="Is dns zone active or not?")
    ] = None,
    dnssec: Annotated[
        Optional[bool], typer.Option(help="Is dnssec enabled or not?")
    ] = None,
    account: Annotated[
        Optional[UUID], typer.Option(help="Account for this dns zone.")
    ] = None,
    purchase: Annotated[
        Optional[UUID],
        typer.Option(
            help="Purchase for this dns zone. Required if no product is provided."
        ),
    ] = None,
    product: Annotated[
        Optional[UUID],
        typer.Option(
            help="Product for this dns zone. Required if no purchase is provided."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = DnsZone(conn)
            model = await ctrl.fetch(dns_zone_id)
            if domain is not None:
                model["domain"] = domain
            if active is not None:
                model["active"] = active
            if dnssec is not None:
                model["dnssec"] = dnssec
            if account is not None:
                model["account"].set(account, "accounts")
            if purchase is not None:
                model["purchase"].set(purchase, "purchases")
            if product is not None:
                model["product"].set(product, "products")
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def delete(
    ctx: typer.Context,
    dns_zone_id: Annotated[List[UUID], typer.Argument()],
):
    try:
        async with Connection() as conn, asyncio.TaskGroup() as tg:
            ctrl = DnsZone(conn)
            for resource_id in dns_zone_id:
                tg.create_task(ctrl.destroy(resource_id))
    except DocumentError as e:
        await print_document_error(e)
