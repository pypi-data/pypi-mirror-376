from typing import Generic, TypeVar, Optional, Any, Union, Awaitable
from jsonapi_client.resourceobject import ResourceObject
from jsonapi_client import Modifier, Filter
from jsonapi_client.exceptions import DocumentError
from .exception import ValidationException

from rich.console import Console, ConsoleOptions, RenderResult
from rich.json import JSON
from uuid import UUID
import json


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class BaseModel:
    def __init__(self, obj: ResourceObject):
        self._obj = obj

    @property
    def id(self):
        return self._obj.id

    @id.setter
    def id(self, value):
        self._obj.id = value

    @property
    def json(self):
        return self._obj.json

    @property
    def url(self) -> str:
        return self._obj.url

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield JSON(json.dumps(self.json, cls=UUIDEncoder), indent=4)

    def __getitem__(self, item):
        return self._obj[item]

    def __setitem__(self, item, value):
        self._obj[item] = value

    def commit(
        self, custom_url: str = "", meta: Optional[dict] = None
    ) -> Awaitable[ResourceObject]:
        return self._obj.commit(custom_url, meta)


Model = TypeVar("Model", bound=BaseModel)


class BaseController(Generic[Model]):
    _class: Any
    _resource: str

    def __init__(self, connection) -> None:
        self._connection = connection
        if not issubclass(self._class, BaseModel):
            raise ValueError("_class attribute is not set")

    @property
    def resource(self):
        return self._resource

    async def fetch(self, resource_id) -> Model:
        doc = await self._connection.get(self._resource, resource_id)
        return self._class(doc.resource)

    async def fetch_all(self, modifier: Modifier = None):
        async for resource in self._connection.iterate(self._resource, modifier):
            yield self._class(resource)

    def create(self) -> Model:
        model = self._class(self._connection.create(self._resource))
        return model

    async def store(
        self, model: Model, create_issue: bool = False, meta: Optional[dict] = None
    ):
        custom_url = ""
        if create_issue:
            custom_url = model._obj.post_url
            custom_url = custom_url + "?issue=1"
        await model.commit(custom_url, meta)

    async def update(
        self, model: Model, create_issue: bool = False, meta: Optional[dict] = None
    ):
        custom_url = ""
        if create_issue:
            custom_url = model._obj.url
            custom_url = custom_url + "?issue=1"
        await model.commit(custom_url, meta)

    async def destroy(self, resource_id, create_issue: bool = False):
        resource = self._connection.create(self._resource)
        resource.id = resource_id
        resource.delete()
        try:
            custom_url = ""
            if create_issue:
                custom_url = resource.url
                custom_url = custom_url + "?issue=1"
            await resource.commit(custom_url)
        except KeyError:
            # Because we didn't fetch the record first it is not stored in
            # the cache, just handle the exception and that's it. The resource
            # is succesfully removed from the server.
            pass
        except DocumentError as e:
            raise ValidationException("Validation failed", e.errors)
