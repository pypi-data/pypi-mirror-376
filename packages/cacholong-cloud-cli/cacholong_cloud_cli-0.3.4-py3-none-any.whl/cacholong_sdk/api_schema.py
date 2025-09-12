api_schema = {
    "accounts": {
        "properties": {
            "name": {"type": ["string"]},
            "display_name": {"type": ["string"]},
            "description": {"type": ["string"]},
            "created_at": {"type": ["string", "null"]},
            "updated_at": {"type": ["string", "null"]},
            "account_type": {"type": ["string", "null"]},
            "account_account_id": {"type": ["string", "null"]},
            "account_account_relation": {"type": ["string", "null"]},
            "company": {"relation": "to-one", "resource": "companies"},
            "users": {"relation": "to-many", "resource": "users"},
        }
    },
    "addresses": {
        "properties": {
            "street": {"type": ["string"]},
            "number": {"type": ["string"]},
            "suffix": {"type": ["string"]},
            "zipcode": {"type": ["string"]},
            "city": {"type": ["string"]},
            "state": {"type": ["string"]},
            "country": {"type": ["string"]},
            "user": {"relation": "to-one", "resource": "users"},
            "company": {"relation": "to-one", "resource": "companies"},
        }
    },
    "companies": {
        "properties": {
            "name": {"type": ["string"]},
            "kvknr": {"type": ["string", "null"]},
            "phone": {"type": ["string", "null"]},
            "email": {"type": ["string", "null"]},
            "email_invoice": {"type": ["string", "null"]},
            "vat_number": {"type": ["string", "null"]},
            "created_at": {"type": ["string", "null"]},
            "updated_at": {"type": ["string", "null"]},
            "account": {"relation": "to-one", "resource": "accounts"},
            "addresses": {"relation": "to-many", "resource": "addresses"},
        }
    },
    "dns-records": {
        "properties": {
            "external_service_provider_status": {"type": ["string", "null"]},
            "dns_record_type": {"type": ["string"]},
            "name": {"type": ["string"]},
            "content": {"type": ["string"]},
            "ttl": {"type": ["integer"]},
            "priority": {"type": ["integer", "null"]},
            "created_at": {"type": ["string", "null"]},
            "updated_at": {"type": ["string", "null"]},
            "dns-zone": {"relation": "to-one", "resource": "dns-zones"},
            "dns-template": {"relation": "to-one", "resource": "dns-templates"},
        }
    },
    "dns-templates": {
        "properties": {
            "name": {"type": ["string"]},
            "created_at": {"type": ["string", "null"]},
            "updated_at": {"type": ["string", "null"]},
            "account": {"relation": "to-one", "resource": "accounts"},
            "dns-records": {"relation": "to-many", "resource": "dns-records"},
        }
    },
    "dns-zones": {
        "properties": {
            "external_service_provider_status": {"type": ["string", "null"]},
            "domain": {"type": ["string"]},
            "active": {"type": ["boolean"]},
            "administratively_disabled": {"type": ["boolean", "null"]},
            "dnssec": {"type": ["boolean"]},
            "dnssec_status": {"type": ["string", "null"]},
            "dnssec_flags": {"type": ["number", "null"]},
            "dnssec_algorithm": {"type": ["number", "null"]},
            "dnssec_public_key": {"type": ["string", "null"]},
            "created_at": {"type": ["string", "null"]},
            "updated_at": {"type": ["string", "null"]},
            "account": {"relation": "to-one", "resource": "accounts"},
            "name-server-group": {
                "relation": "to-one",
                "resource": "name-server-groups",
            },
            "purchase": {"relation": "to-one", "resource": "purchases"},
            "product": {"relation": "to-one", "resource": "products"},
            "dns-records": {"relation": "to-many", "resource": "dns-records"},
        }
    },
    "products": {
        "properties": {
            "name": {"type": ["string"]},
            "product_type": {"type": ["string"]},
            "price": {"type": ["number", "null"]},
            "default_bill_sequence": {"type": ["string"]},
            "invoice_description": {"type": ["string"]},
            "publish_start": {"type": ["string"]},
            "publish_end": {"type": ["string"]},
            "created_at": {"type": ["string", "null"]},
            "updated_at": {"type": ["string", "null"]},
            "children": {"relation": "to-many", "resource": "products"},
            "parent": {"relation": "to-one", "resource": "products"},
            "service-bundles": {"relation": "to-many", "resource": "service-bundles"},
            "tlds": {"relation": "to-many", "resource": "tlds"},
        }
    },
    "purchases": {
        "properties": {
            "product_type": {"type": ["string", "null"]},
            "description": {"type": ["string"]},
            "units": {"type": ["integer"]},
            "date_purchase": {"type": ["string", "null"]},
            "date_activation": {"type": ["string", "null"]},
            "date_deactivation": {"type": ["string", "null"]},
            "date_next_bill": {"type": ["string", "null"]},
            "bill_sequence": {"type": ["string", "null"]},
            "created_at": {"type": ["string", "null"]},
            "updated_at": {"type": ["string", "null"]},
            "account": {"relation": "to-one", "resource": "accounts"},
            "children": {"relation": "to-many", "resource": "purchases"},
            "parent": {"relation": "to-one", "resource": "purchases"},
            "product": {"relation": "to-one", "resource": "products"},
        }
    },
}
