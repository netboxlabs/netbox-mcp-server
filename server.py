from mcp.server.fastmcp import FastMCP
from netbox_client import NetBoxRestClient
import os
import argparse
import sys
import asyncio
from dotenv import load_dotenv

# Mapping of simple object names to API endpoints
NETBOX_OBJECT_TYPES = {
    # DCIM (Device and Infrastructure)
    "cables": "dcim/cables",
    "console-ports": "dcim/console-ports", 
    "console-server-ports": "dcim/console-server-ports",
    "devices": "dcim/devices",
    "device-bays": "dcim/device-bays",
    "device-roles": "dcim/device-roles",
    "device-types": "dcim/device-types",
    "front-ports": "dcim/front-ports",
    "interfaces": "dcim/interfaces",
    "inventory-items": "dcim/inventory-items",
    "locations": "dcim/locations",
    "manufacturers": "dcim/manufacturers",
    "modules": "dcim/modules",
    "module-bays": "dcim/module-bays",
    "module-types": "dcim/module-types",
    "platforms": "dcim/platforms",
    "power-feeds": "dcim/power-feeds",
    "power-outlets": "dcim/power-outlets",
    "power-panels": "dcim/power-panels",
    "power-ports": "dcim/power-ports",
    "racks": "dcim/racks",
    "rack-reservations": "dcim/rack-reservations",
    "rack-roles": "dcim/rack-roles",
    "regions": "dcim/regions",
    "sites": "dcim/sites",
    "site-groups": "dcim/site-groups",
    "virtual-chassis": "dcim/virtual-chassis",
    
    # IPAM (IP Address Management)
    "asns": "ipam/asns",
    "asn-ranges": "ipam/asn-ranges", 
    "aggregates": "ipam/aggregates",
    "fhrp-groups": "ipam/fhrp-groups",
    "ip-addresses": "ipam/ip-addresses",
    "ip-ranges": "ipam/ip-ranges",
    "prefixes": "ipam/prefixes",
    "rirs": "ipam/rirs",
    "roles": "ipam/roles",
    "route-targets": "ipam/route-targets",
    "services": "ipam/services",
    "vlans": "ipam/vlans",
    "vlan-groups": "ipam/vlan-groups",
    "vrfs": "ipam/vrfs",
    
    # Circuits
    "circuits": "circuits/circuits",
    "circuit-types": "circuits/circuit-types",
    "circuit-terminations": "circuits/circuit-terminations",
    "providers": "circuits/providers",
    "provider-networks": "circuits/provider-networks",
    
    # Virtualization
    "clusters": "virtualization/clusters",
    "cluster-groups": "virtualization/cluster-groups",
    "cluster-types": "virtualization/cluster-types",
    "virtual-machines": "virtualization/virtual-machines",
    "vm-interfaces": "virtualization/interfaces",
    
    # Tenancy
    "tenants": "tenancy/tenants",
    "tenant-groups": "tenancy/tenant-groups",
    "contacts": "tenancy/contacts",
    "contact-groups": "tenancy/contact-groups",
    "contact-roles": "tenancy/contact-roles",
    
    # VPN
    "ike-policies": "vpn/ike-policies",
    "ike-proposals": "vpn/ike-proposals",
    "ipsec-policies": "vpn/ipsec-policies",
    "ipsec-profiles": "vpn/ipsec-profiles",
    "ipsec-proposals": "vpn/ipsec-proposals",
    "l2vpns": "vpn/l2vpns",
    "tunnels": "vpn/tunnels",
    "tunnel-groups": "vpn/tunnel-groups",
    
    # Wireless
    "wireless-lans": "wireless/wireless-lans",
    "wireless-lan-groups": "wireless/wireless-lan-groups",
    "wireless-links": "wireless/wireless-links",

    # Extras
    "config-contexts": "extras/config-contexts",
    "custom-fields": "extras/custom-fields",
    "export-templates": "extras/export-templates",
    "image-attachments": "extras/image-attachments",
    "jobs": "extras/jobs",
    "saved-filters": "extras/saved-filters",
    "scripts": "extras/scripts",
    "tags": "extras/tags",
    "webhooks": "extras/webhooks",
}

# Global variables
app = FastMCP("NetBox")
netbox = None

@app.tool()
def netbox_get_objects(object_type: str, filters: dict):
    """
    Get objects from NetBox based on their type and filters
    Args:
        object_type: String representing the NetBox object type (e.g. "devices", "ip-addresses")
        filters: dict of filters to apply to the API call based on the NetBox API filtering options
    
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
    
    See NetBox API documentation for filtering options for each object type.
    """
    # Validate object_type exists in mapping
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")
        
    # Get API endpoint from mapping
    endpoint = NETBOX_OBJECT_TYPES[object_type]
        
    # Make API call
    return netbox.get(endpoint, params=filters)

@app.tool()
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
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")
        
    # Get API endpoint from mapping
    endpoint = f"{NETBOX_OBJECT_TYPES[object_type]}/{object_id}"
    
    return netbox.get(endpoint)

@app.tool()
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


def load_config():
    """Load configuration from .env file and CLI arguments."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="NetBox MCP Server")
    parser.add_argument(
        "--netbox-url",
        default=os.getenv("NETBOX_URL"),
        help="NetBox instance URL (default: from NETBOX_URL env var)"
    )
    parser.add_argument(
        "--netbox-token",
        default=os.getenv("NETBOX_TOKEN"),
        help="NetBox API token (default: from NETBOX_TOKEN env var)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.getenv("LOG_LEVEL", "INFO"),
        help="Log level (default: INFO)"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=os.getenv("MCP_TRANSPORT", "stdio"),
        help="MCP transport method (default: stdio)"
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_SERVER_HOST", "localhost"),
        help="Server host for HTTP transport (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_SERVER_PORT", "8000")),
        help="Server port for HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        default=os.getenv("VERIFY_SSL", "true").lower() == "true",
        help="Verify SSL certificates (default: true)"
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_false",
        dest="verify_ssl",
        help="Disable SSL certificate verification"
    )
    
    return parser.parse_args()


def initialize_netbox_client(config):
    """Initialize the NetBox client with the given configuration."""
    # Validate required configuration
    if not config.netbox_url:
        raise ValueError("NetBox URL must be provided via --netbox-url or NETBOX_URL environment variable")
    if not config.netbox_token:
        raise ValueError("NetBox token must be provided via --netbox-token or NETBOX_TOKEN environment variable")
    
    # Initialize NetBox client
    global netbox
    netbox = NetBoxRestClient(
        url=config.netbox_url,
        token=config.netbox_token,
        verify_ssl=config.verify_ssl
    )


def main():
    """Main entry point for the server."""
    # Load configuration from .env and CLI arguments
    config = load_config()
    
    # Initialize NetBox client
    initialize_netbox_client(config)
    
    # Run the server with the specified transport
    if config.transport == "stdio":
        # Run with stdio transport (default FastMCP behavior)
        app.run()
    elif config.transport == "http":
        # Run with HTTP transport
        # FastMCP supports this via the run method with transport parameter
        app.run(transport="streamable-http")
    else:
        raise ValueError(f"Unsupported transport: {config.transport}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error starting NetBox MCP Server: {e}", file=sys.stderr)
        sys.exit(1)
