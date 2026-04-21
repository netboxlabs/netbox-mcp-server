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

    # n8n compatibility
    parser.add_argument(
        "--n8n-compat",
        action="store_true",
        dest="n8n_compat",
        default=None,
        help="Enable n8n AI Agent MCP client compatibility mode "
        "(string-typed tool parameters). See README.",
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
    if args.n8n_compat is not None:
        overlay["n8n_compat"] = args.n8n_compat

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

netbox = None

# Some MCP clients (e.g., n8n) send literal strings for empty optional parameters
_EMPTY_STRING_VALUES = {"undefined", "null", "none"}


def _is_empty_string(value: str) -> bool:
    """Check if a string represents an empty value (including n8n-style nulls)."""
    stripped = value.strip()
    return not stripped or stripped.lower() in _EMPTY_STRING_VALUES


def _parse_filters(filters: str | dict[str, Any] | None) -> dict[str, Any]:
    """Parse filters parameter from JSON string or dict (n8n-compat mode only).

    Called from the compat-mode tool wrappers, which advertise ``filters`` as
    a JSON string via the MCP schema. Accepts a dict too as a convenience for
    direct Python callers, but MCP clients in compat mode always send strings.

    Strict-mode (default) wrappers take native dicts and do not call this
    helper.
    """
    if filters is None:
        return {}
    if isinstance(filters, dict):
        return filters
    if _is_empty_string(filters):
        return {}
    try:
        return json.loads(filters.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid filters JSON: {e}") from e


def _parse_list_param(value: str | list[str] | None) -> list[str]:
    """Parse a list parameter from a comma-separated string or list (n8n-compat mode only).

    Called from the compat-mode tool wrappers, which advertise list-like
    parameters as comma-separated strings via the MCP schema. Accepts a list
    as a convenience for direct Python callers.

    Strict-mode (default) wrappers take native ``list[str]`` and do not call
    this helper.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if _is_empty_string(value):
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


def _netbox_get_objects_impl(
    object_type: str,
    filters: dict[str, Any],
    fields: list[str],
    brief: bool,
    limit: int,
    offset: int,
    ordering: str = "",
) -> Any:
    """Shared business logic for netbox_get_objects. Takes native Python types.

    Called from both strict and compat tool wrappers. No schema concerns; no
    parsing; no string handling.
    """
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    validate_filters(filters)

    endpoint, fallback = _get_endpoint_info(object_type)

    params = filters.copy()
    params["limit"] = limit
    params["offset"] = offset

    if fields:
        params["fields"] = ",".join(fields)

    if brief:
        params["brief"] = "1"

    if ordering and ordering.strip():
        params["ordering"] = ordering

    return netbox.get(endpoint, params=params, fallback_endpoint=fallback)


_NETBOX_GET_OBJECTS_DESCRIPTION = (
    """
    Get objects from NetBox based on their type and filters

    Args:
        object_type: String representing the NetBox object type (e.g. "dcim.device", "ipam.ipaddress")
        filters: Filters to apply to the API call based on the NetBox API filtering options

                FILTER RULES:
                Valid: Direct fields like {"site_id": 1, "name": "router", "status": "active"}
                Valid: Lookups like {"name__ic": "switch", "id__in": [1,2,3], "vid__gte": 100}
                Invalid: Multi-hop like {"device__site_id": 1} - NOT supported

                Lookup suffixes: n, ic, nic, isw, nisw, iew, niew, ie, nie,
                                 empty, regex, iregex, lt, lte, gt, gte, in

                Two-step pattern for cross-relationship queries:
                  sites = netbox_get_objects('dcim.site', {"name": "NYC"})
                  netbox_get_objects('dcim.device', {"site_id": 1})

        fields: List of specific fields to return
                **IMPORTANT: ALWAYS USE THIS PARAMETER TO MINIMIZE TOKEN USAGE**
                Field filtering significantly reduces response payload and is critical for performance.

                - None or [] = returns all fields (NOT RECOMMENDED - use only when you need complete objects)
                - ["id", "name"] = returns only specified fields (RECOMMENDED)

                Examples:
                - For counting: ["id"] (minimal payload)
                - For listings: ["id", "name", "status"]
                - For IP addresses: ["address", "dns_name", "description"]

                Uses NetBox's native field filtering via ?fields= parameter.
                **Always specify only the fields you actually need.**

        brief: returns only a minimal representation of each object in the response.

        limit: Maximum results to return (default 5, max 100)

        offset: Skip this many results for pagination (default 0)

        ordering: Fields used to determine sort order of results.
                  Field names may be prefixed with '-' to invert the sort order.
                  Use comma-separated string for multiple fields.

                  Examples:
                  - 'name' (alphabetical by name)
                  - '-id' (ordered by ID descending)
                  - 'facility,-name' (by facility, then by name descending)


    Returns:
        Paginated response dict with count / next / previous / results.

    Valid object_type values:

    """
    + "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
    + """

    See NetBox API documentation for filtering options for each object type.
    """
)


def netbox_get_objects(
    object_type: str,
    filters: dict[str, Any] | None = None,
    fields: list[str] | None = None,
    brief: bool = False,
    limit: Annotated[int, Field(ge=1, le=100)] = 5,
    offset: Annotated[int, Field(ge=0)] = 0,
    ordering: str = "",
) -> Any:
    """Strict-mode wrapper (default). Takes native Python types."""
    return _netbox_get_objects_impl(
        object_type=object_type,
        filters=filters or {},
        fields=fields or [],
        brief=brief,
        limit=limit,
        offset=offset,
        ordering=ordering,
    )


def _netbox_get_object_by_id_impl(
    object_type: str,
    object_id: int,
    fields: list[str],
    brief: bool,
) -> Any:
    """Shared business logic for netbox_get_object_by_id. Takes native types."""
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")

    endpoint, fallback = _get_endpoint_info(object_type)
    full_endpoint = f"{endpoint}/{object_id}"
    full_fallback = f"{fallback}/{object_id}" if fallback else None

    params: dict[str, Any] = {}
    if fields:
        params["fields"] = ",".join(fields)

    if brief:
        params["brief"] = "1"

    return netbox.get(full_endpoint, params=params, fallback_endpoint=full_fallback)


def netbox_get_object_by_id(
    object_type: str,
    object_id: int,
    fields: list[str] | None = None,
    brief: bool = False,
) -> Any:
    """Strict-mode wrapper for netbox_get_object_by_id.

    Get detailed information about a specific NetBox object by its ID.

    Args:
        object_type: String representing the NetBox object type (e.g. "dcim.device")
        object_id: The numeric ID of the object
        fields: List of specific fields to return (e.g. ["id", "name", "status"])
        brief: Return only a minimal representation

    Returns:
        Object dict (complete or with only requested fields based on fields parameter)
    """
    fields_list = fields or []
    return _netbox_get_object_by_id_impl(
        object_type=object_type,
        object_id=object_id,
        fields=fields_list,
        brief=brief,
    )


def _netbox_get_changelogs_impl(filters: dict[str, Any]) -> Any:
    """Shared business logic for netbox_get_changelogs. Takes native Python types.

    Called from both strict and compat tool wrappers. No schema concerns; no
    parsing; no string handling.
    """
    return netbox.get("core/object-changes", params=filters)


def netbox_get_changelogs(filters: dict[str, Any] | None = None) -> Any:
    """Strict-mode wrapper for netbox_get_changelogs.

    Get object change records (changelogs) from NetBox based on filters.

    Args:
        filters: Dict of filters to apply to the API call.

    Returns:
        Paginated response dict.
    """
    return _netbox_get_changelogs_impl(filters or {})


def _netbox_search_objects_impl(
    query: str,
    object_types: list[str],
    fields: list[str],
    limit: int,
) -> dict[str, list[dict[str, Any]]]:
    """Shared business logic for netbox_search_objects. Takes native types."""
    search_types = object_types or DEFAULT_SEARCH_TYPES

    for obj_type in search_types:
        if obj_type not in NETBOX_OBJECT_TYPES:
            valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
            raise ValueError(f"Invalid object_type '{obj_type}'. Must be one of:\n{valid_types}")

    results: dict[str, list[dict[str, Any]]] = {obj_type: [] for obj_type in search_types}

    for obj_type in search_types:
        try:
            endpoint, fallback = _get_endpoint_info(obj_type)
            response = netbox.get(
                endpoint,
                params={
                    "q": query,
                    "limit": limit,
                    "fields": ",".join(fields) if fields else None,
                },
                fallback_endpoint=fallback,
            )
            results[obj_type] = response.get("results", [])
        except Exception:  # noqa: S112 - intentional error-resilient search
            continue

    return results


_NETBOX_SEARCH_OBJECTS_DESCRIPTION = (
    """
    Perform global search across NetBox infrastructure.

    Searches names, descriptions, IP addresses, serial numbers, asset tags,
    and other key fields across multiple object types.

    Args:
        query: Search term (device names, IPs, serial numbers, hostnames, site names)
               Examples: 'switch01', '192.168.1.1', 'NYC-DC1', 'SN123456'
        object_types: List of types to search (optional)
                     Default: """
    + ",".join(DEFAULT_SEARCH_TYPES)
    + """
                     Examples: ['dcim.device', 'ipam.ipaddress', 'dcim.site']
        fields: List of specific fields to return (reduces response size)
                Examples: ['id', 'name', 'status'], ['address', 'dns_name']
        limit: Max results per object type (default 5, max 100)

    Returns:
        Dictionary with object_type keys and list of matching objects.
    """
)


def netbox_search_objects(
    query: str,
    object_types: list[str] | None = None,
    fields: list[str] | None = None,
    limit: Annotated[int, Field(ge=1, le=100)] = 5,
) -> dict[str, list[dict[str, Any]]]:
    """Strict-mode wrapper for netbox_search_objects."""
    return _netbox_search_objects_impl(
        query=query,
        object_types=object_types or [],
        fields=fields or [],
        limit=limit,
    )


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


def _register_strict_tools(mcp: FastMCP) -> None:
    """Register strict-typed tools (native int/list/dict). Default mode."""
    mcp.tool(description=_NETBOX_GET_OBJECTS_DESCRIPTION)(netbox_get_objects)
    mcp.tool()(netbox_get_object_by_id)
    mcp.tool()(netbox_get_changelogs)
    mcp.tool(description=_NETBOX_SEARCH_OBJECTS_DESCRIPTION)(netbox_search_objects)


def _register_compat_tools(mcp: FastMCP) -> None:
    """Register string-typed tools for n8n AI Agent MCP client compatibility.

    n8n's MCP client has a hardcoded mapTypes table that does not support
    JSON Schema integer/array/object. See n8n-io/n8n#20682.
    """

    @mcp.tool(description=_NETBOX_GET_OBJECTS_DESCRIPTION)
    def netbox_get_objects(
        object_type: str,
        filters: str = "{}",
        fields: str = "",
        brief: bool = False,
        # float (not int) works around n8n's mapTypes missing "integer"
        limit: Annotated[float, Field(default=5.0, ge=1.0, le=100.0)] = 5.0,
        offset: Annotated[float, Field(default=0.0, ge=0.0)] = 0.0,
        ordering: str = "",
    ) -> Any:
        """n8n-compat wrapper. Parses strings to native types, calls impl."""
        return _netbox_get_objects_impl(
            object_type=object_type,
            filters=_parse_filters(filters),
            fields=_parse_list_param(fields),
            brief=brief,
            limit=int(limit),
            offset=int(offset),
            ordering=ordering,
        )

    @mcp.tool()
    def netbox_get_object_by_id(
        object_type: str,
        object_id: float,
        fields: str = "",
        brief: bool = False,
    ) -> Any:
        """n8n-compat wrapper for netbox_get_object_by_id."""
        return _netbox_get_object_by_id_impl(
            object_type=object_type,
            object_id=int(object_id),
            fields=_parse_list_param(fields),
            brief=brief,
        )

    @mcp.tool()
    def netbox_get_changelogs(filters: str = "{}") -> Any:
        """n8n-compat wrapper for netbox_get_changelogs."""
        return _netbox_get_changelogs_impl(_parse_filters(filters))

    @mcp.tool(description=_NETBOX_SEARCH_OBJECTS_DESCRIPTION)
    def netbox_search_objects(
        query: str,
        object_types: str = "",
        fields: str = "",
        limit: Annotated[float, Field(default=5.0, ge=1.0, le=100.0)] = 5.0,
    ) -> dict[str, list[dict[str, Any]]]:
        """n8n-compat wrapper for netbox_search_objects."""
        return _netbox_search_objects_impl(
            query=query,
            object_types=_parse_list_param(object_types),
            fields=_parse_list_param(fields),
            limit=int(limit),
        )


def create_mcp(n8n_compat: bool) -> FastMCP:
    """Create a FastMCP instance with tools registered for the given mode.

    Args:
        n8n_compat: If True, register string-typed tool wrappers for the n8n
                    AI Agent MCP client. If False (default), register
                    strict JSON Schema types (integer/array/object) as
                    consumed by most clients (Claude, Cursor, Cline, etc.).
    """
    mcp = FastMCP("NetBox")
    if n8n_compat:
        _register_compat_tools(mcp)
    else:
        _register_strict_tools(mcp)
    return mcp


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

    mcp = create_mcp(n8n_compat=settings.n8n_compat)
    if settings.n8n_compat:
        logger.info("n8n compatibility mode ENABLED (string-typed tool parameters)")

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
