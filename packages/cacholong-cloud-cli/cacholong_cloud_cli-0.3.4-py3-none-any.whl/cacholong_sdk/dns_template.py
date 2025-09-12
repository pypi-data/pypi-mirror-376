from .common import BaseController, BaseModel


class DnsTemplateModel(BaseModel):
    pass


class DnsTemplate(BaseController[DnsTemplateModel]):
    _class = DnsTemplateModel

    def __init__(self, connection):
        self._resource = "dns-templates"

        super().__init__(connection)
