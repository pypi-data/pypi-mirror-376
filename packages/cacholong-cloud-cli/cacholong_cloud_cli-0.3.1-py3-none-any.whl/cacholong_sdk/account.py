from .common import BaseController, BaseModel


class AccountModel(BaseModel):
    pass


class Account(BaseController[AccountModel]):
    _class = AccountModel

    def __init__(self, connection):
        self._resource = "accounts"

        super().__init__(connection)
