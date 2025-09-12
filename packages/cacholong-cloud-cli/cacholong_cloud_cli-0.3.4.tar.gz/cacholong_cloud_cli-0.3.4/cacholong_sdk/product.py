from .common import BaseController, BaseModel


class ProductModel(BaseModel):
    pass


class Product(BaseController[ProductModel]):
    _class = ProductModel

    def __init__(self, connection):
        self._resource = "products"

        super().__init__(connection)
