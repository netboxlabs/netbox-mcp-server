import os
import re
import unicodedata
from typing import Dict, List

from mcp.server.fastmcp import FastMCP

from constants import API_ENDPOINTS
from netbox_client import NetBoxRestClient

mcp = FastMCP("NetBox", log_level="DEBUG")
netbox = None


@mcp.tool()
def get_valid_filters(object_type: str) -> List[Dict[str, str]]:
    """
    Retrieve valid filter keys and descriptions for a given NetBox object_type.

    Args:
        object_type (str): The type of NetBox object to query.
            Example values: "devices", "ip-addresses", "vlans", "virtual-machines", "tunnels", etc.

    Returns:
        A list of valid filters and descriptions for that object type, each containing:
            - name: The filter key
            - description: What the filter does

    Example:
        get_valid_filters("devices") →
        [
            {"name": "name", "description": "Exact match on device name"},
            {"name": "site", "description": "Filter by Site slug"},
            ...
        ]

    If the object_type is unknown or unsupported, returns an empty list.

    This should be used before calling get_objects if you are not sure what filters are
    valid or available for that type. Use the "name" field to construct the filters.
    """
    return API_ENDPOINTS.get(object_type, {}).get("filters", [])


@mcp.tool()
def get_fields(object_type: str) -> List[str]:
    """
    Retrieve available fields for a given NetBox object_type.

    Args:
        object_type (str): The type of NetBox object to query.
            Example values: "devices", "ip-addresses", "vlans", "virtual-machines", "tunnels", etc.

    Returns:
        A list of field names available for that object type.

    Example:
        get_fields("devices") →
        [
            "id",
            "url", 
            "name",
            "serial",
            "asset_tag",
            ...
        ]

    If the object_type is unknown or unsupported, returns an empty list.
    """
    return API_ENDPOINTS.get(object_type, {}).get("fields", [])


def call_netbox_api(endpoint_key: str, filters: dict = None):
    """
    Generic function to call a NetBox API endpoint.

    Args:
        endpoint_key (str): Key referencing the API_ENDPOINTS metadata
        filters (dict, optional): Filtering parameters. Defaults to empty dict.

    Returns:
        List[dict]: API response data
    """
    endpoint_info = API_ENDPOINTS.get(endpoint_key)
    if not endpoint_info:
        raise ValueError(f"Unknown endpoint key: {endpoint_key}")

    endpoint = endpoint_info["endpoint"]
    return netbox.get(endpoint, params=filters or {})


@mcp.tool()
def netbox_get_objects(object_type: str, filters: Dict[str, str], fields: str = None):
    """
    Get objects from NetBox based on their type and filters
    Args:
        object_type: String representing the NetBox object type (e.g. "devices", "ip-addresses")
        filters (dict): Key-value filters to apply. Must match valid filter keys for the given object_type.
        fields (str, optional): Comma-separated list of fields to include in response. If not specified, returns default fields.
    
    Valid object_type values:
    
    DCIM (Device and Infrastructure):
    - cables
    - console-ports
    - console-server-ports  
    - devices
    - device-bays
    - device-roles
    - device-types
    - front-ports
    - interfaces
    - inventory-items
    - locations
    - manufacturers
    - modules
    - module-bays
    - module-types
    - platforms
    - power-feeds
    - power-outlets
    - power-panels
    - power-ports
    - racks
    - rack-reservations
    - rack-roles
    - regions
    - sites
    - site-groups
    - virtual-chassis
    
    IPAM (IP Address Management):
    - asns
    - asn-ranges
    - aggregates 
    - fhrp-groups
    - ip-addresses
    - ip-ranges
    - prefixes
    - rirs
    - roles
    - route-targets
    - services
    - vlans
    - vlan-groups
    - vrfs
    
    Circuits:
    - circuits
    - circuit-types
    - circuit-terminations
    - providers
    - provider-networks
    
    Virtualization:
    - clusters
    - cluster-groups
    - cluster-types
    - virtual-machines
    - vm-interfaces
    
    Tenancy:
    - tenants
    - tenant-groups
    - contacts
    - contact-groups
    - contact-roles
    
    VPN:
    - ike-policies
    - ike-proposals
    - ipsec-policies
    - ipsec-profiles
    - ipsec-proposals
    - l2vpns
    - tunnels
    - tunnel-groups
    
    Wireless:
    - wireless-lans
    - wireless-lan-groups
    - wireless-links

    Customization:
    - custom-fields
    - custom-field-choice-sets
    - custom-links
    - export-templates
    - tags
    - image-attachments
    
    See NetBox API documentation for filtering options for each object type.
    """
    if object_type not in API_ENDPOINTS:
        raise ValueError(f"Unsupported object_type: {object_type}")

    if not filters:
        filters = {}

    filters["brief"] = 1
    if fields:
        filters["fields"] = fields

    return call_netbox_api(object_type, filters or {})


@mcp.tool()
def netbox_get_object_by_id(object_type: str, object_id: int):
    """
    Get detailed information about a specific NetBox object by its ID.
    
    Args:
        object_type: String representing the NetBox object type (e.g. "devices", "ip-addresses")
        object_id: The numeric ID of the object
    
    Returns:
        Complete object details
    """
    # Validate object_type exists in mapping
    if object_type not in API_ENDPOINTS:
        valid_types = "\n".join(f"- {t}" for t in sorted(API_ENDPOINTS.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    # Get API endpoint from mapping
    endpoint = f"{API_ENDPOINTS[object_type]['endpoint']}/{object_id}"

    return netbox.get(endpoint)

@mcp.tool()
def get_object_by_name(object_type: str, object_name: str):
    """
    Get detailed information about a specific NetBox object by its name.

    Args:
        object_type: String representing the NetBox object type (e.g. "devices", "ip-addresses")
        object_name: The name of the object

    Returns:
        Complete object details
    """
    # Validate object_type exists in mapping
    if object_type not in API_ENDPOINTS:
        valid_types = "\n".join(f"- {t}" for t in sorted(API_ENDPOINTS.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    filters = {"q": object_name}
    # Get API endpoint from mapping
    data = call_netbox_api(object_type, filters or {})
    if len(data) == 1:
        endpoint = f"{API_ENDPOINTS[object_type]['endpoint']}/{data[0]['id']}"
        return netbox.get(endpoint)

    return data


@mcp.tool()
def slugify_name(object_name: str):
    """
    Slugify a name to be used as a NetBox object name.

    Args:
        object_name: The name to slugify

    Returns:
        Slugified name
    """
    value = str(object_name)
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


@mcp.tool()
def netbox_get_changelogs(filters: dict):
    """
    Get object change records (changelogs) from NetBox based on filters.
    
    Args:
        filters: dict of filters to apply to the API call based on the NetBox API filtering options
    
    Returns:
        List of changelog objects matching the specified filters
    
    Filtering options include:
    - user_id: Filter by user ID who made the change
    - user: Filter by username who made the change
    - changed_object_type_id: Filter by ContentType ID of the changed object
    - changed_object_id: Filter by ID of the changed object
    - object_repr: Filter by object representation (usually contains object name)
    - action: Filter by action type (created, updated, deleted)
    - time_before: Filter for changes made before a given time (ISO 8601 format)
    - time_after: Filter for changes made after a given time (ISO 8601 format)
    - q: Search term to filter by object representation

    Example:
    To find all changes made to a specific device with ID 123:
    {"changed_object_type_id": "dcim.device", "changed_object_id": 123}
    
    To find all deletions in the last 24 hours:
    {"action": "delete", "time_after": "2023-01-01T00:00:00Z"}
    
    Each changelog entry contains:
    - id: The unique identifier of the changelog entry
    - user: The user who made the change
    - user_name: The username of the user who made the change
    - request_id: The unique identifier of the request that made the change
    - action: The type of action performed (created, updated, deleted)
    - changed_object_type: The type of object that was changed
    - changed_object_id: The ID of the object that was changed
    - object_repr: String representation of the changed object
    - object_data: The object's data after the change (null for deletions)
    - object_data_v2: Enhanced data representation
    - prechange_data: The object's data before the change (null for creations)
    - postchange_data: The object's data after the change (null for deletions)
    - time: The timestamp when the change was made
    """
    endpoint = "core/object-changes"
    
    # Make API call
    return netbox.get(endpoint, params=filters)

if __name__ == "__main__":
    # Load NetBox configuration from environment variables
    netbox_url = os.getenv("NETBOX_URL")
    netbox_token = os.getenv("NETBOX_TOKEN")
    
    if not netbox_url or not netbox_token:
        raise ValueError("NETBOX_URL and NETBOX_TOKEN environment variables must be set")
    
    # Initialize NetBox client
    netbox = NetBoxRestClient(url=netbox_url, token=netbox_token)
    
    mcp.run(transport="stdio")
