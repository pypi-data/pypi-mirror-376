from .common import BaseController, BaseModel


class DnsRecordModel(BaseModel):
    pass


class DnsRecord(BaseController[DnsRecordModel]):
    _class = DnsRecordModel

    def __init__(self, connection):
        self._resource = "dns-records"

        super().__init__(connection)
