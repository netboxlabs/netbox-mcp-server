# NetBox Client Library

A Python client library for interacting with NetBox, providing both a base abstract class and a REST API implementation.

## Features

- Abstract base class with generic CRUD methods
- REST API implementation of the base class
- Support for both single and bulk operations
- Designed to be extensible for ORM-based implementations

## Installation

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -e .
```

## Usage

### REST API Client

```python
from client import NetBoxRestClient

# Initialize the client
client = NetBoxRestClient(
    url="https://netbox.example.com",
    token="your_api_token_here",
    verify_ssl=True
)

# Get all sites
sites = client.get("dcim/sites")
print(f"Found {len(sites)} sites")

# Get a specific site
site = client.get("dcim/sites", id=1)
print(f"Site name: {site.get('name')}")

# Example with pagination
# Get sites page by page
page = 1
limit = 50
while True:
    sites_page = client.get("dcim/sites", params={
        "limit": limit,
        "offset": (page - 1) * limit
    })
    if not sites_page:
        break
        
    print(f"Processing page {page} with {len(sites_page)} sites")
    for site in sites_page:
        print(f"Site: {site.get('name')}")
        
    page += 1

# Create a new site
new_site = client.create("dcim/sites", {
    "name": "New Site",
    "slug": "new-site",
    "status": "active"
})
print(f"Created site: {new_site.get('name')} (ID: {new_site.get('id')})")

# Update a site
updated_site = client.update("dcim/sites", id=1, data={
    "description": "Updated description"
})

# Delete a site
success = client.delete("dcim/sites", id=1)
if success:
    print("Site deleted successfully")

# Bulk operations
new_sites = client.bulk_create("dcim/sites", [
    {"name": "Site 1", "slug": "site-1", "status": "active"},
    {"name": "Site 2", "slug": "site-2", "status": "active"}
])

updated_sites = client.bulk_update("dcim/sites", [
    {"id": 1, "description": "Updated description 1"},
    {"id": 2, "description": "Updated description 2"}
])

success = client.bulk_delete("dcim/sites", ids=[1, 2])
```

## Extending for ORM Implementation

The `NetBoxClientBase` abstract base class can be extended to create an ORM-based implementation for use within a NetBox plugin:

```python
from client import NetBoxClientBase
from django.db import transaction

class NetBoxOrmClient(NetBoxClientBase):
    """
    NetBox client implementation using the ORM directly.
    This would be used within a NetBox plugin.
    """
    
    def __init__(self):
        # No authentication needed as this would run within NetBox
        pass
    
    def get(self, endpoint, id=None, params=None):
        # Implementation would use Django ORM to fetch objects
        # Example (not implemented)
        pass
    
    # Other methods would be implemented similarly
```

## License

MIT
