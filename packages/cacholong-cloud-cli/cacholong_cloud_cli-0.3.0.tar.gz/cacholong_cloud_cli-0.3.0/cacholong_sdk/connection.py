import importlib.metadata

from jsonapi_client import Session
from .api_schema import api_schema


class connection(Session):
    def __init__(self, api_uri, api_key, extra_headers={}) -> None:

        # Call parent constructor
        basic_headers = {
            "Accept": "application/vnd.api+json",
            "Authorization": "Bearer " + api_key,
            "User-Agent": "ccloud/" + importlib.metadata.version("ccloud"),
        }
        headers = basic_headers | extra_headers
        super().__init__(
            api_uri,
            enable_async=True,
            schema=api_schema,
            request_kwargs={"headers": headers},
        )
