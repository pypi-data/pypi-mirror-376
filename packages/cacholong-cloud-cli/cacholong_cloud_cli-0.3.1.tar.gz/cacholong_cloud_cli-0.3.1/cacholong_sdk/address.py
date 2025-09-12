from .common import BaseController, BaseModel


class AddressModel(BaseModel):
    pass


class Address(BaseController[AddressModel]):
    _class = AddressModel

    def __init__(self, connection):
        self._resource = "addresses"

        super().__init__(connection)
