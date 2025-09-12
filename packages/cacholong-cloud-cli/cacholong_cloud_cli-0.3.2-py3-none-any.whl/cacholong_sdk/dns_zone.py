from .common import BaseController, BaseModel


class DnsZoneModel(BaseModel):
    pass


class DnsZone(BaseController[DnsZoneModel]):
    _class = DnsZoneModel

    def __init__(self, connection):
        self._resource = "dns-zones"

        super().__init__(connection)
