import argparse
import json
import logging
import sys
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from netbox_mcp_server.config import Settings, configure_logging
from netbox_mcp_server.netbox_client import NetBoxRestClient
from netbox_mcp_server.netbox_types import NETBOX_OBJECT_TYPES


def parse_cli_args() -> dict[str, Any]:
    """
    Parse command-line arguments for configuration overrides.

    Returns:
        dict of configuration overrides (only includes explicitly set values)
    """
    parser = argparse.ArgumentParser(
        description="NetBox MCP Server - Model Context Protocol server for NetBox",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Core NetBox settings
    parser.add_argument(
        "--netbox-url",
        type=str,
        help="Base URL of the NetBox instance (e.g., https://netbox.example.com/)",
    )
    parser.add_argument(
        "--netbox-token",
        type=str,
        help="API token for NetBox authentication",
    )

    # Transport settings
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "http"],
        help="MCP transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host address for HTTP server (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port for HTTP server (default: 8000)",
    )

    # Security settings
    ssl_group = parser.add_mutually_exclusive_group()
    ssl_group.add_argument(
        "--verify-ssl",
        action="store_true",
        dest="verify_ssl",
        default=None,
        help="Verify SSL certificates (default)",
    )
    ssl_group.add_argument(
        "--no-verify-ssl",
        action="store_false",
        dest="verify_ssl",
        help="Disable SSL certificate verification (not recommended)",
    )

    # Observability settings
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity level (default: INFO)",
    )

    args: argparse.Namespace = parser.parse_args()

    overlay: dict[str, Any] = {}
    if args.netbox_url is not None:
        overlay["netbox_url"] = args.netbox_url
    if args.netbox_token is not None:
        overlay["netbox_token"] = args.netbox_token
    if args.transport is not None:
        overlay["transport"] = args.transport
    if args.host is not None:
        overlay["host"] = args.host
    if args.port is not None:
        overlay["port"] = args.port
    if args.verify_ssl is not None:
        overlay["verify_ssl"] = args.verify_ssl
    if args.log_level is not None:
        overlay["log_level"] = args.log_level

    return overlay


# Default object types for global search
DEFAULT_SEARCH_TYPES = [
    "dcim.device",  # Most common search target
    "dcim.site",  # Site names frequently searched
    "ipam.ipaddress",  # IP searches very common
    "dcim.interface",  # Interface names/descriptions
    "dcim.rack",  # Rack identifiers
    "ipam.vlan",  # VLAN names/IDs
    "circuits.circuit",  # Circuit identifiers
    "virtualization.virtualmachine",  # VM names
]

mcp = FastMCP("NetBox")
netbox = None


def _parse_filters(filters: str | dict[str, Any]) -> dict[str, Any]:
    """
    Parse filters parameter - accepts both JSON string and dict for backward compatibility.

    Args:
        filters: Either a JSON string (for n8n) or a dict (for Claude/other clients)

    Returns:
        Parsed filters dict
    """
    if isinstance(filters, dict):
        return filters
    if not filters:
        return {}
    try:
        return json.loads(filters)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid filters JSON: {e}") from e


def _parse_list_param(value: str | list[str]) -> list[str]:
    """
    Parse list parameter - accepts both comma-separated string and list for backward compatibility.

    Args:
        value: Either a comma-separated string (for n8n) or a list (for Claude/other clients)

    Returns:
        Parsed list of strings
    """
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_filters(filters: dict[str, Any]) -> None:
    """
    Validate that filters don't use multi-hop relationship traversal.

    NetBox API does not support nested relationship queries like:
    - device__site_id (filtering by related object's field)
    - interface__device__site (multiple relationship hops)

    Valid patterns:
    - Direct field filters: site_id, name, status
    - Lookup expressions: name__ic, status__in, id__gt

    Args:
        filters: Dictionary of filter parameters

    Raises:
        ValueError: If filter uses invalid multi-hop relationship traversal
    """
    valid_suffixes = {
        "n",
        "ic",
        "nic",
        "isw",
        "nisw",
        "iew",
        "niew",
        "ie",
        "nie",
        "empty",
        "regex",
        "iregex",
        "lt",
        "lte",
        "gt",
        "gte",
        "in",
    }

    for filter_name in filters:
        # Skip special parameters
        if filter_name in ("limit", "offset", "fields", "q"):
            continue

        if "__" not in filter_name:
            continue

        parts = filter_name.split("__")

        # Allow field__suffix pattern (e.g., name__ic, id__gt)
        if len(parts) == 2 and parts[-1] in valid_suffixes:
            continue
        # Block multi-hop patterns and invalid suffixes
        if len(parts) >= 2:
            raise ValueError(
                f"Invalid filter '{filter_name}': Multi-hop relationship "
                f"traversal or invalid lookup suffix not supported. Use direct field filters like "
                f"'site_id' or two-step queries."
            )


@mcp.tool(
    description="""
    Get objects from NetBox based on their type and filters

    Args:
        object_type: String representing the NetBox object type (e.g. "dcim.device", "ipam.ipaddress")
        filters: JSON string of filters to apply to the API call based on the NetBox API filtering options

                FILTER RULES:
                Valid: Direct fields like '{"site_id": 1, "name": "router", "status": "active"}'
                Valid: Lookups like '{"name__ic": "switch", "id__in": [1,2,3], "vid__gte": 100}'
                Invalid: Multi-hop like '{"device__site_id": 1}' - NOT supported

                Lookup suffixes: n, ic, nic, isw, nisw, iew, niew, ie, nie,
                                 empty, regex, iregex, lt, lte, gt, gte, in

                Two-step pattern for cross-relationship queries:
                  sites = netbox_get_objects('dcim.site', '{"name": "NYC"}')
                  netbox_get_objects('dcim.device', '{"site_id": 1}')

        fields: Comma-separated string of specific fields to return
                **IMPORTANT: ALWAYS USE THIS PARAMETER TO MINIMIZE TOKEN USAGE**
                Field filtering significantly reduces response payload and is critical for performance.

                - Empty string '' = returns all fields (NOT RECOMMENDED - use only when you need complete objects)
                - 'id,name' = returns only specified fields (RECOMMENDED)

                Examples:
                - For counting: 'id' (minimal payload)
                - For listings: 'id,name,status'
                - For IP addresses: 'address,dns_name,description'

                Uses NetBox's native field filtering via ?fields= parameter.
                **Always specify only the fields you actually need.**

        brief: returns only a minimal representation of each object in the response.
               This is useful when you need only a list of available objects without any related data.

        limit: Maximum results to return (default 5, max 100)
               Start with default, increase only if needed

        offset: Skip this many results for pagination (default 0)
                Example: offset=0 (page 1), offset=5 (page 2), offset=10 (page 3)

        ordering: Fields used to determine sort order of results.
                  Field names may be prefixed with '-' to invert the sort order.
                  Use comma-separated string for multiple fields.

                  Examples:
                  - 'name' (alphabetical by name)
                  - '-id' (ordered by ID descending)
                  - 'facility,-name' (by facility, then by name descending)
                  - '' (default NetBox ordering)


    Returns:
        Paginated response dict with the following structure:
            - count: Total number of objects matching the query
                     ALWAYS REFER TO THIS FIELD FOR THE TOTAL NUMBER OF OBJECTS MATCHING THE QUERY
            - next: URL to next page (or null if no more pages)
                    ALWAYS REFER TO THIS FIELD FOR THE NEXT PAGE OF RESULTS
            - previous: URL to previous page (or null if on first page)
                        ALWAYS REFER TO THIS FIELD FOR THE PREVIOUS PAGE OF RESULTS
            - results: Array of objects for this page
                       ALWAYS REFER TO THIS FIELD FOR THE OBJECTS ON THIS PAGE

    ENSURE YOU ARE AWARE THE RESULTS ARE PAGINATED BEFORE PROVIDING RESPONSE TO THE USER.

    Valid object_type values:

    """
    + "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
    + """

    See NetBox API documentation for filtering options for each object type.
    """
)
def netbox_get_objects(
    object_type: str,
    filters: str = "{}",
    fields: str = "",
    brief: bool = False,
    limit: Annotated[float, Field(default=5.0, ge=1.0, le=100.0)] = 5.0,
    offset: Annotated[float, Field(default=0.0, ge=0.0)] = 0.0,
    ordering: str = "",
):
    """
    Get objects from NetBox based on their type and filters
    """
    # Validate object_type exists in mapping
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    # Parse parameters - accept both string (n8n) and native types (Claude) for backward compatibility
    filters_dict = _parse_filters(filters)
    fields_list = _parse_list_param(fields)

    # Validate filter patterns
    validate_filters(filters_dict)

    # Get API endpoint and fallback from mapping
    endpoint, fallback = _get_endpoint_info(object_type)

    # Build params with pagination (parameters override filters dict)
    # Convert float to int for NetBox API compatibility
    params = filters_dict.copy()
    params["limit"] = int(limit)
    params["offset"] = int(offset)

    if fields_list:
        params["fields"] = ",".join(fields_list)

    if brief:
        params["brief"] = "1"

    if ordering and ordering.strip():
        params["ordering"] = ordering

    # Make API call
    return netbox.get(endpoint, params=params, fallback_endpoint=fallback)


@mcp.tool
def netbox_get_object_by_id(
    object_type: str,
    object_id: float,
    fields: str = "",
    brief: bool = False,
):
    """
    Get detailed information about a specific NetBox object by its ID.

    Args:
        object_type: String representing the NetBox object type (e.g. "dcim.device", "ipam.ipaddress")
        object_id: The numeric ID of the object
        fields: Comma-separated string of specific fields to return
                **IMPORTANT: ALWAYS USE THIS PARAMETER TO MINIMIZE TOKEN USAGE**
                Field filtering reduces response payload by 80-90% and is critical for performance.

                - Empty string '' = returns all fields (NOT RECOMMENDED - use only when you need complete objects)
                - 'id,name' = returns only specified fields (RECOMMENDED)

                Examples:
                - For basic info: 'id,name,status'
                - For devices: 'id,name,status,site'
                - For IP addresses: 'address,dns_name,vrf,status'

                Uses NetBox's native field filtering via ?fields= parameter.
                **Always specify only the fields you actually need.**
        brief: returns only a minimal representation of the object in the response.
               This is useful when you need only a summary of the object without any related data.

    Returns:
        Object dict (complete or with only requested fields based on fields parameter)
    """
    # Validate object_type exists in mapping
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    # Parse fields - accept both string (n8n) and list (Claude) for backward compatibility
    fields_list = _parse_list_param(fields)

    # Get API endpoint and fallback from mapping
    # Convert float to int for NetBox API compatibility
    endpoint, fallback = _get_endpoint_info(object_type)
    full_endpoint = f"{endpoint}/{int(object_id)}"
    full_fallback = f"{fallback}/{int(object_id)}" if fallback else None

    params = {}
    if fields_list:
        params["fields"] = ",".join(fields_list)

    if brief:
        params["brief"] = "1"

    return netbox.get(full_endpoint, params=params, fallback_endpoint=full_fallback)


@mcp.tool
def netbox_get_changelogs(filters: str = "{}"):
    """
    Get object change records (changelogs) from NetBox based on filters.

    Args:
        filters: JSON string of filters to apply to the API call based on the NetBox API filtering options

    Returns:
        Paginated response dict with the following structure:
            - count: Total number of changelog entries matching the query
                     ALWAYS REFER TO THIS FIELD FOR THE TOTAL NUMBER OF CHANGELOG ENTRIES MATCHING THE QUERY
            - next: URL to next page (or null if no more pages)
                    ALWAYS REFER TO THIS FIELD FOR THE NEXT PAGE OF RESULTS
            - previous: URL to previous page (or null if on first page)
                        ALWAYS REFER TO THIS FIELD FOR THE PREVIOUS PAGE OF RESULTS
            - results: Array of changelog entries for this page
                       ALWAYS REFER TO THIS FIELD FOR THE CHANGELOG ENTRIES ON THIS PAGE

    Filtering options include:
    - user_id: Filter by user ID who made the change
    - user: Filter by username who made the change
    - changed_object_type_id: Filter by numeric ContentType ID (e.g., 21 for dcim.device)
                              Note: This expects a numeric ID, not an object type string
    - changed_object_id: Filter by ID of the changed object
    - object_repr: Filter by object representation (usually contains object name)
    - action: Filter by action type (created, updated, deleted)
    - time_before: Filter for changes made before a given time (ISO 8601 format)
    - time_after: Filter for changes made after a given time (ISO 8601 format)
    - q: Search term to filter by object representation

    Examples:
    To find all changes made to a specific object by ID:
    '{"changed_object_id": 123}'

    To find changes by object name pattern:
    '{"object_repr": "router-01"}'

    To find all deletions in the last 24 hours:
    '{"action": "delete", "time_after": "2023-01-01T00:00:00Z"}'

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
    # Parse filters - accept both string (n8n) and dict (Claude) for backward compatibility
    filters_dict = _parse_filters(filters)

    endpoint = "core/object-changes"

    # Make API call
    return netbox.get(endpoint, params=filters_dict)


@mcp.tool(
    description="""
    Perform global search across NetBox infrastructure.

    Searches names, descriptions, IP addresses, serial numbers, asset tags,
    and other key fields across multiple object types.

    Args:
        query: Search term (device names, IPs, serial numbers, hostnames, site names)
               Examples: 'switch01', '192.168.1.1', 'NYC-DC1', 'SN123456'
        object_types: Comma-separated string of types to search (optional)
                     Default: """
    + ",".join(DEFAULT_SEARCH_TYPES)
    + """
                     Examples: 'dcim.device,ipam.ipaddress,dcim.site'
        fields: Comma-separated string of specific fields to return (reduces response size) IT IS STRONGLY RECOMMENDED TO USE THIS PARAMETER TO MINIMIZE TOKEN USAGE.
                - Empty string '' = returns all fields (no filtering)
                - 'id,name' = returns only specified fields
                Examples: 'id,name,status', 'address,dns_name'
                Uses NetBox's native field filtering via ?fields= parameter
        limit: Max results per object type (default 5, max 100)

    Returns:
        Dictionary with object_type keys and list of matching objects.
        All searched types present in result (empty list if no matches).

    Example:
        # Search for anything matching "switch"
        results = netbox_search_objects('switch')
        # Returns: {
        #   'dcim.device': [{'id': 1, 'name': 'switch-01', ...}],
        #   'dcim.site': [],
        #   ...
        # }

        # Search for IP address
        results = netbox_search_objects('192.168.1.100')
        # Returns: {
        #   'ipam.ipaddress': [{'id': 42, 'address': '192.168.1.100/24', ...}],
        #   ...
        # }

        # Limit search to specific types with field projection
        results = netbox_search_objects(
            'NYC',
            object_types='dcim.site,dcim.location',
            fields='id,name,status'
        )
    """
)
def netbox_search_objects(
    query: str,
    object_types: str = "",
    fields: str = "",
    limit: Annotated[float, Field(default=5.0, ge=1.0, le=100.0)] = 5.0,
) -> dict[str, list[dict[str, Any]]]:
    """
    Perform global search across NetBox infrastructure.
    """
    # Parse parameters - accept both string (n8n) and list (Claude) for backward compatibility
    search_types = _parse_list_param(object_types) or DEFAULT_SEARCH_TYPES
    fields_list = _parse_list_param(fields)

    # Validate all object types exist in mapping
    for obj_type in search_types:
        if obj_type not in NETBOX_OBJECT_TYPES:
            valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
            raise ValueError(f"Invalid object_type '{obj_type}'. Must be one of:\n{valid_types}")

    results = {obj_type: [] for obj_type in search_types}

    # Build results dictionary (error-resilient)
    for obj_type in search_types:
        try:
            endpoint, fallback = _get_endpoint_info(obj_type)
            response = netbox.get(
                endpoint,
                params={
                    "q": query,
                    "limit": int(limit),
                    "fields": ",".join(fields_list) if fields_list else None,
                },
                fallback_endpoint=fallback,
            )
            # Extract results array from paginated response
            results[obj_type] = response.get("results", [])
        except Exception:  # noqa: S112 - intentional error-resilient search
            # Continue searching other types if one fails
            # results[obj_type] already has empty list
            continue

    return results


def _get_endpoint_info(object_type: str) -> tuple[str, str | None]:
    """
    Returns (endpoint, fallback_endpoint) for the given object type.

    The fallback_endpoint is used for NetBox version compatibility when
    an endpoint path has changed between versions.

    Args:
        object_type: The NetBox object type (e.g., "dcim.device")

    Returns:
        Tuple of (endpoint, fallback_endpoint). fallback_endpoint is None
        if no fallback is needed for this object type.
    """
    type_info = NETBOX_OBJECT_TYPES[object_type]
    return type_info["endpoint"], type_info.get("fallback_endpoint")


def main() -> None:
    """Main entry point for the MCP server."""
    global netbox

    cli_overlay: dict[str, Any] = parse_cli_args()

    try:
        settings = Settings(**cli_overlay)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)  # noqa: T201 - before logging configured
        sys.exit(1)

    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting NetBox MCP Server")
    logger.info(f"Effective configuration: {settings.get_effective_config_summary()}")

    if not settings.verify_ssl:
        logger.warning(
            "SSL certificate verification is DISABLED. "
            "This is insecure and should only be used for testing."
        )

    if settings.transport == "http" and settings.host in ["0.0.0.0", "::", "[::]"]:  # noqa: S104 - checking, not binding
        logger.warning(
            f"HTTP transport is bound to {settings.host}:{settings.port}, which exposes the "
            "service to all network interfaces (IPv4/IPv6). This is insecure and should only be "
            "used for testing. Ensure this is secured with TLS/reverse proxy if exposed to network."
        )
    elif settings.transport == "http" and settings.host not in [
        "127.0.0.1",
        "localhost",
    ]:
        logger.info(
            f"HTTP transport is bound to {settings.host}:{settings.port}. "
            "Ensure this is secured with TLS/reverse proxy if exposed to network."
        )

    try:
        netbox = NetBoxRestClient(
            url=str(settings.netbox_url),
            token=settings.netbox_token.get_secret_value(),
            verify_ssl=settings.verify_ssl,
        )
        logger.debug("NetBox client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize NetBox client: {e}")
        sys.exit(1)

    try:
        if settings.transport == "stdio":
            logger.info("Starting stdio transport")
            mcp.run(transport="stdio")
        elif settings.transport == "http":
            logger.info(f"Starting HTTP transport on {settings.host}:{settings.port}")
            mcp.run(transport="http", host=settings.host, port=settings.port)
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
