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
from cacholong_sdk import DnsRecord, DnsRecordModel

# Create typer object
app = AsyncTyper()


@app.async_command()
async def list(
    ctx: typer.Context,
    external_service_provider_status: Annotated[
        Optional[str], typer.Option(help="Status for external service provider.")
    ] = None,
    dns_record_type: Annotated[
        Optional[str],
        typer.Option(
            help="Depending on DNS record type name, content, ttl and priority will be validated. Only record types mentioned are allowed and NS record type is only available for certain users."
        ),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option(
            help="For most records this must be a valid domain (SRV, TLSA and NS records follow different rules). When dns template is given, placeholder $domain$ must be used. When dns zone is given, name must be identical to dns zone domain fqdn. It is not allowed to end the name with a point."
        ),
    ] = None,
    content: Annotated[
        Optional[str],
        typer.Option(
            help="Content differs for each DNS record type. When dns template is given, placeholder $domain$ is allowed for some records (for example CAA or CNAME records). Only TXT records can be longer then 255 chars."
        ),
    ] = None,
    ttl: Annotated[
        Optional[str],
        typer.Option(
            help='Time to live in seconds, limited to allowed values. Please note that a TTL of 1 (one) can have a special meaning (Cloudflare considers this value "automatic").'
        ),
    ] = None,
    priority: Annotated[
        Optional[str], typer.Option(help="Prohibited, except for MX and SRV record.")
    ] = None,
    created_at: Annotated[Optional[str], typer.Option(help="")] = None,
    updated_at: Annotated[Optional[str], typer.Option(help="")] = None,
    dns_zone: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing dns zone. Required unless dns template is given. Only available for certain users, dnz zone should not be administratively disabled. Must be unique with type, name, content and priority."
        ),
    ] = None,
    dns_template: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing dns template. Required unless dns zone is given. Must be unique with type, name, content and priority."
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
    if dns_record_type is not None:
        modifier.append(
            Filter(query_str="filter[dns_record_type]=" + str(dns_record_type))
        )
    if name is not None:
        modifier.append(Filter(name=name))
    if content is not None:
        modifier.append(Filter(content=content))
    if ttl is not None:
        modifier.append(Filter(ttl=ttl))
    if priority is not None:
        modifier.append(Filter(priority=priority))
    if created_at is not None:
        modifier.append(Filter(query_str="filter[created_at]=" + str(created_at)))
    if updated_at is not None:
        modifier.append(Filter(query_str="filter[updated_at]=" + str(updated_at)))
    if dns_zone is not None:
        modifier.append(Filter(query_str="filter[dns-zone]=" + str(dns_zone)))
    if dns_template is not None:
        modifier.append(Filter(query_str="filter[dns-template]=" + str(dns_template)))

    # Table definition
    tabledef = [
        {"header": Column("Id", no_wrap=True), "column": "id"},
        {"header": "Name", "column": "name"},
        {"header": "Dns record type", "column": "dns_record_type"},
        {"header": "Content", "column": "content"},
        {
            "header": "External service provider status",
            "column": "external_service_provider_status",
        },
        {"header": "Created", "column": "created_at"},
        {"header": "Updated", "column": "updated_at"},
    ]
    async with Connection() as conn:
        await list_resources(ctx, DnsRecord(conn), tabledef, modifier)


@app.async_command()
async def show(
    ctx: typer.Context,
    dns_record_id: Annotated[UUID, typer.Argument()],
):
    # Show resource
    try:
        async with Connection() as conn:
            ctrl = DnsRecord(conn)
            model = await ctrl.fetch(dns_record_id)

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def create(
    ctx: typer.Context,
    dns_record_type: Annotated[
        str,
        typer.Option(
            help="Depending on DNS record type name, content, ttl and priority will be validated. Only record types mentioned are allowed and NS record type is only available for certain users."
        ),
    ],
    name: Annotated[
        str,
        typer.Option(
            help="For most records this must be a valid domain (SRV, TLSA and NS records follow different rules). When dns template is given, placeholder $domain$ must be used. When dns zone is given, name must be identical to dns zone domain fqdn. It is not allowed to end the name with a point."
        ),
    ],
    content: Annotated[
        str,
        typer.Option(
            help="Content differs for each DNS record type. When dns template is given, placeholder $domain$ is allowed for some records (for example CAA or CNAME records). Only TXT records can be longer then 255 chars."
        ),
    ],
    ttl: Annotated[
        Optional[int],
        typer.Option(
            help='Time to live in seconds, limited to allowed values. Please note that a TTL of 1 (one) can have a special meaning (Cloudflare considers this value "automatic").'
        ),
    ] = None,
    priority: Annotated[
        Optional[int], typer.Option(help="Prohibited, except for MX and SRV record.")
    ] = None,
    dns_zone: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing dns zone. Required unless dns template is given. Only available for certain users, dnz zone should not be administratively disabled. Must be unique with type, name, content and priority."
        ),
    ] = None,
    dns_template: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing dns template. Required unless dns zone is given. Must be unique with type, name, content and priority."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = DnsRecord(conn)
            model = ctrl.create()
            model["dns_record_type"] = dns_record_type
            model["name"] = name
            model["content"] = content
            if ttl is not None:
                model["ttl"] = ttl
            if priority is not None:
                model["priority"] = priority
            if dns_zone is not None:
                model["dns-zone"] = ResourceTuple(dns_zone, "dns-zones")
            if dns_template is not None:
                model["dns-template"] = ResourceTuple(dns_template, "dns-templates")
            await ctrl.store(model, ctx.obj["create_issue"])

            show_resource(ctx, model)
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def update(
    ctx: typer.Context,
    dns_record_id: Annotated[UUID, typer.Argument()],
    dns_record_type: Annotated[
        Optional[str],
        typer.Option(
            help="Depending on DNS record type name, content, ttl and priority will be validated. Only record types mentioned are allowed and NS record type is only available for certain users."
        ),
    ] = None,
    name: Annotated[
        Optional[str],
        typer.Option(
            help="For most records this must be a valid domain (SRV, TLSA and NS records follow different rules). When dns template is given, placeholder $domain$ must be used. When dns zone is given, name must be identical to dns zone domain fqdn. It is not allowed to end the name with a point."
        ),
    ] = None,
    content: Annotated[
        Optional[str],
        typer.Option(
            help="Content differs for each DNS record type. When dns template is given, placeholder $domain$ is allowed for some records (for example CAA or CNAME records). Only TXT records can be longer then 255 chars."
        ),
    ] = None,
    ttl: Annotated[
        Optional[int],
        typer.Option(
            help='Time to live in seconds, limited to allowed values. Please note that a TTL of 1 (one) can have a special meaning (Cloudflare considers this value "automatic").'
        ),
    ] = None,
    priority: Annotated[
        Optional[int], typer.Option(help="Prohibited, except for MX and SRV record.")
    ] = None,
    dns_zone: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing dns zone. Required unless dns template is given. Only available for certain users, dnz zone should not be administratively disabled. Must be unique with type, name, content and priority."
        ),
    ] = None,
    dns_template: Annotated[
        Optional[UUID],
        typer.Option(
            help="Existing dns template. Required unless dns zone is given. Must be unique with type, name, content and priority."
        ),
    ] = None,
):
    try:
        async with Connection() as conn:
            ctrl = DnsRecord(conn)
            model = await ctrl.fetch(dns_record_id)
            if dns_record_type is not None:
                model["dns_record_type"] = dns_record_type
            if name is not None:
                model["name"] = name
            if content is not None:
                model["content"] = content
            if ttl is not None:
                model["ttl"] = ttl
            if priority is not None:
                model["priority"] = priority
            if dns_zone is not None:
                model["dns-zone"].set(dns_zone, "dns-zones")
            if dns_template is not None:
                model["dns-template"].set(dns_template, "dns-templates")
    except DocumentError as e:
        await print_document_error(e)


@app.async_command()
async def delete(
    ctx: typer.Context,
    dns_record_id: Annotated[List[UUID], typer.Argument()],
):
    try:
        async with Connection() as conn, asyncio.TaskGroup() as tg:
            ctrl = DnsRecord(conn)
            for resource_id in dns_record_id:
                tg.create_task(ctrl.destroy(resource_id))
    except DocumentError as e:
        await print_document_error(e)
