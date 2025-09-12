from .common import BaseController, BaseModel


class PurchaseModel(BaseModel):
    pass


class Purchase(BaseController[PurchaseModel]):
    _class = PurchaseModel

    def __init__(self, connection):
        self._resource = "purchases"

        super().__init__(connection)
