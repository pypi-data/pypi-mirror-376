# CLI frontend

The API client library for managing various resources.

[Client Library Documentation](https://docs.cacholong.eu/api/)

## Getting started

To install this package you need to take a few steps before this works correctly
1. Create an virtual environment: python3 -m venv <directory>
2. Activate the environment: <directory>/bin/activate
3. Now install the package: pip install cacholong-cloud-cli
4. Or upgrade the package: pip install cacholong-cloud-cli --upgrade

Now you can use the command `ccloud` on the system. Please note, make sure to activate the virtual environment before running the command `ccloud`.

You will need an API-token. This token can be created using our panel at https://cp.cacholong.eu/#/user/settings/api. You can create an api token within your profile under API.

When running the command `ccloud` for the first time it will ask you for an API-token.

After that you will be able to run the following command:
```bash
ccloud accounts list
```

This will give you an overview of accounts where you have access to.

## Usage

Overview of the possibilities:
```bash
ccloud --help
```

To fetch an overview of the dns-zones for an account:
```bash
ccloud dns-zones list --account <account uuid>
```

Creating a DNS-record:
```bash
ccloud dns-records create --dns-zone <dns-zone uuid> \
    --name localhost.example.com \
    --dns-record-type A \
    --content 127.0.0.1 \
    --ttl 300
```

Updating a DNS-record:
```bash
ccloud dns-records update <dns-record uuid> \
    --content 127.0.0.1
```

Deleting a DNS-record:
```bash
ccloud dns-records delete <dns-record uuid>
```

Every command includes an option --help which will give an overview of the possibilities.

## Advanced usage

Its also possible to create your own command line utility to handle various parts. Here are the same examples as above but now using python.

### Fetching DNS-zones
```python
import asyncio

from cacholong_sdk.connection import connection
from cacholong_sdk import ResourceTuple, Inclusion, Filter
from cacholong_sdk import DnsZone, DnsZoneModel, DnsRecord, DnsRecordModel

async def main():
    async with connection('https://api.cacholong.eu/api/v1/', 'YOUR-API-TOKEN') as api:
        searchfilter = Filter(account="UUID_OF_ACCOUNT")
        DnsZoneCtrl = DnsZone(api)
        async for zone in DnsZoneCtrl.fetch_all(searchfilter):
            print(zone["domain"])

# Execute main function
asyncio.run(main())
```

### Create a DNS-record
```python
import asyncio

from cacholong_sdk.connection import connection
from cacholong_sdk import ResourceTuple, Inclusion, Filter
from cacholong_sdk import DnsZone, DnsZoneModel, DnsRecord, DnsRecordModel

async def main():
    async with connection('https://api.cacholong.eu/api/v1/', 'YOUR-API-TOKEN') as api:
        DnsRecordCtrl = DnsRecord(api)

        dns_record = DNSRecordCtrl.create()
        dns_record["dns-zone"] = ResourceTuple("UUID_DNS_ZONE", "dns-zones")
        dns_record["name"] = "localhost.example.nl"
        dns_record["dns_record_type"] = "A"
        dns_record["content"] = "127.0.0.1"
        dns_record["ttl"] = 300
        await DNSRecordCtrl.store(dns_record)

# Execute main function
asyncio.run(main())
```

### Update a DNS-record
```python
import asyncio

from cacholong_sdk.connection import connection
from cacholong_sdk import ResourceTuple, Inclusion, Filter
from cacholong_sdk import DnsZone, DnsZoneModel, DnsRecord, DnsRecordModel

async def main():
    async with connection('https://api.cacholong.eu/api/v1/', 'YOUR-API-TOKEN') as api:
        DnsRecordCtrl = DnsRecord(api)

        dns_record = await DnsRecordCtrl.fetch("UUID_OF_DNS_RECORD")
        dns_record["content"] = "127.0.0.1"

        # Be careful: the above change will be applied automatically

# Execute main function
asyncio.run(main())
```

### Delete a DNS-record
```python
import asyncio

from cacholong_sdk.connection import connection
from cacholong_sdk import ResourceTuple, Inclusion, Filter
from cacholong_sdk import DnsZone, DnsZoneModel, DnsRecord, DnsRecordModel

async def main():
    async with connection('https://api.cacholong.eu/api/v1/', 'YOUR-API-TOKEN') as api:
        DnsRecordCtrl = DnsRecord(api)

        await DnsRecordCtrl.destroy("UUID_OF_DNS_RECORD")

# Execute main function
asyncio.run(main())
```

## Support
Questions, feedback, or suggestions? Send us an email at [ccloud-support@cacholong.nl].
