# Common functionality
from typing import List
from enum import Enum
import typer
from rich.console import Console
from rich.table import Table
from cacholong_cli.connection import Connection
import json
from cacholong_sdk import BaseController, BaseModel
from cacholong_sdk import Modifier, Sort, SparseField, DocumentError
from uuid import UUID

ErrorConsole = Console(stderr=True, style="bold red")


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class OutputFormat(str, Enum):
    TABLE = "table"
    JSON = "json"


async def print_document_error(doc_error: DocumentError):
    ErrorConsole.print("Status: {}".format(doc_error.errors["status_code"]))
    js = await doc_error.response.json()
    i = 1
    for error in js["errors"]:
        detail = ""
        if "detail" in error:
            detail = error["detail"]
        ErrorConsole.print("{}: {}: {}".format(i, error["title"], detail))
        i = i + 1


async def _perform_list_resources(
    controller: BaseController, modifier: Modifier, tabledef, callback
):
    relations = [
        relation["column"] for relation in tabledef if "nested_column" in relation
    ]
    async for resource in controller.fetch_all(modifier):
        for relation in relations:
            await resource[relation].fetch()
        callback(resource)


async def _perform_list_relation_resources(model: BaseModel, relation: str, callback):
    await model[relation].fetch()
    for resource in model[relation].resources:
        callback(resource)


def _handle_column(row, column_definition):
    if "nested_column" in column_definition:
        if row[column_definition["column"]].resource != None:
            return str(
                row[column_definition["column"]].resource[
                    column_definition["nested_column"]
                ]
            )
        return ""
    else:
        return str(row[column_definition["column"]])


def _build_row(row, table, tabledef):
    if any(d["column"] == "id" for d in tabledef):
        table.add_row(
            row.id, *[_handle_column(row, d) for d in tabledef if d["column"] != "id"]
        )
    else:
        table.add_row(
            *[_handle_column(row, d) for d in tabledef if d["column"] != "id"]
        )


async def list_resources(
    ctx: typer.Context,
    controller: BaseController,
    tabledef,
    modifier: List[Modifier] = [],
):
    # Handle sort globally
    if ctx.obj["sort"] is not None and ctx.obj["sort"] != "":
        modifier.append(Sort(ctx.obj["sort"]))

    # Only fetch the data needed
    if ctx.obj["output"] == OutputFormat.TABLE:
        modifier.append(
            SparseField(
                controller.resource,
                *list(
                    dict.fromkeys(
                        [d["column"] for d in tabledef if d["column"] != "id"]
                    )
                )
            )
        )

    # Build modifier (query parameters)
    mod = modifier[0]
    for m in modifier[1:]:
        mod = mod + m

    try:
        if ctx.obj["output"] == OutputFormat.TABLE:
            console = Console()
            table = Table(*[d["header"] for d in tabledef])
            await _perform_list_resources(
                controller, mod, tabledef, lambda row: _build_row(row, table, tabledef)
            )
            console.print(table)
        elif ctx.obj["output"] == OutputFormat.JSON:
            data = []
            await _perform_list_resources(
                controller, mod, tabledef, lambda row: data.append(row.json)
            )
            print(json.dumps(data))
    except DocumentError as e:
        await print_document_error(e)


async def list_relation_resources(
    ctx: typer.Context,
    model: BaseModel,
    relation: str,
    tabledef,
    modifier: List[Modifier] = [],
):
    # Handle sort globally
    #    if ctx.obj["sort"] is not None and ctx.obj["sort"] != "":
    #        modifier.append(Sort(ctx.obj["sort"]))
    #
    #    # Only fetch the data needed
    #    if ctx.obj["output"] == OutputFormat.TABLE:
    #        modifier.append(
    #            SparseField(
    #                controller.resource,
    #                *[d["column"] for d in tabledef if d["column"] != "id"]
    #            )
    #        )
    #
    #    # Build modifier (query parameters)
    #    mod = modifier[0]
    #    for m in modifier[1:]:
    #        mod = mod + m

    try:
        if ctx.obj["output"] == OutputFormat.TABLE:
            console = Console()
            table = Table(*[d["header"] for d in tabledef])
            await _perform_list_relation_resources(
                model, relation, lambda row: _build_row(row, table, tabledef)
            )
            console.print(table)
        elif ctx.obj["output"] == OutputFormat.JSON:
            data = []
            await _perform_list_relation_resources(
                model, relation, lambda row: data.append(row.json)
            )
            print(json.dumps(data))
    except DocumentError as e:
        await print_document_error(e)


def show_resource(
    ctx: typer.Context,
    model: BaseModel,
):
    if ctx.obj["output"] == OutputFormat.TABLE:
        console = Console()
        console.print(model)
    elif ctx.obj["output"] == OutputFormat.JSON:
        print(json.dumps(model.json, cls=UUIDEncoder))
