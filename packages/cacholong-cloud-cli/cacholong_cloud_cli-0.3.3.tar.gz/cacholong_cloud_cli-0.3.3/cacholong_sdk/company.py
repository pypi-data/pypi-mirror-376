from .common import BaseController, BaseModel


class CompanyModel(BaseModel):
    pass


class Company(BaseController[CompanyModel]):
    _class = CompanyModel

    def __init__(self, connection):
        self._resource = "companies"

        super().__init__(connection)
