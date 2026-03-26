"""
NetBox GraphQL MCP Tools

Provides MCP tools for querying the NetBox GraphQL API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
    from fastmcp import FastMCP

    from netbox_mcp_server.netbox_client import NetBoxRestClient

logger = logging.getLogger(__name__)


def register_graphql_tools(mcp_instance: FastMCP, netbox_client: NetBoxRestClient) -> None:
    """Register GraphQL tools on the MCP server.

    Args:
        mcp_instance: The FastMCP server instance to register tools on
        netbox_client: The NetBox REST client for making GraphQL requests
    """

    @mcp_instance.tool
    def netbox_graphql_query(
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query against the NetBox GraphQL API.

        Use this tool to fetch cross-object data in a single query with precise field
        selection — far more efficient than multiple REST API calls.

        Use netbox_graphql_schema_search to discover available types and fields.
        Use netbox_graphql_type_details to inspect specific type structure.

        CRITICAL: Always include pagination in list queries, e.g.:
            device_list(pagination: {limit: 50})

        All field names use snake_case (e.g., device_list, primary_ip4, site_id).

        Examples:
            Devices with interfaces and IPs (replaces 3+ REST calls):
                query {
                  device_list(
                    filters: { status: "active" }
                    pagination: { limit: 10 }
                  ) {
                    id
                    name
                    site { name }
                    interfaces(filters: { enabled: true }) {
                      name
                      ip_addresses { address dns_name }
                    }
                    primary_ip4 { address }
                  }
                }

            IP addresses in a prefix:
                query {
                  ip_address_list(
                    filters: { parent: "10.0.0.0/24" }
                    pagination: { limit: 50 }
                  ) {
                    address
                    dns_name
                    status
                  }
                }

        Args:
            query: GraphQL query string to execute against NetBox
            variables: Optional dict of query variables for parameterized queries

        Returns:
            GraphQL response dict with 'data' and/or 'errors' keys, or an 'error'
            key if the response is too large or GraphQL is unavailable.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty GraphQL query string")

        try:
            return netbox_client.graphql(query, variables)
        except ValueError as e:
            return {"error": str(e)}
        except requests.HTTPError as e:
            return {"error": f"HTTP error querying NetBox GraphQL: {e}"}

    @mcp_instance.tool
    def netbox_graphql_schema_search(
        keyword: str,
        max_types: int = 10,
        include_internal_types: bool = False,
    ) -> dict[str, Any]:
        """Search the NetBox GraphQL schema for types and fields matching a keyword.

        Use this tool BEFORE writing a GraphQL query to discover what types and fields
        are available. Search by concept name to find relevant types.

        Examples:
            netbox_graphql_schema_search("device") -> returns matching types and fields
            netbox_graphql_schema_search("interface") -> returns interface-related types and fields
            netbox_graphql_schema_search("ip") -> returns IP-related types and fields

        Args:
            keyword: Case-insensitive keyword to search for in type names and field names
            max_types: Maximum number of matching types to return (default 10, max 50)
            include_internal_types: Include GraphQL internal types (prefixed with '__')

        Returns:
            Dict with 'keyword', 'matching_types' (list of type info dicts),
            'matching_fields' (list of field matches with their parent type),
            and 'total_matches' count. Returns 'error' key if introspection fails.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be a non-empty search string")

        max_types = max(1, min(50, max_types))
        keyword_lower = keyword.lower()

        introspection_query = """
        {
          __schema {
            types {
              name
              kind
              description
              fields {
                name
                description
              }
            }
          }
        }
        """

        try:
            result = netbox_client.graphql(introspection_query)
        except (ValueError, requests.HTTPError) as e:
            return {"error": f"GraphQL introspection failed: {e}"}

        if "error" in result:
            return result

        types = result.get("data", {}).get("__schema", {}).get("types", [])

        matching_types: list[dict[str, Any]] = []
        matching_fields: list[dict[str, Any]] = []

        for type_info in types:
            type_name = type_info.get("name", "")

            if not include_internal_types and type_name.startswith("__"):
                continue

            type_matches = keyword_lower in type_name.lower()
            if type_matches and len(matching_types) < max_types:
                matching_types.append(
                    {
                        "name": type_name,
                        "kind": type_info.get("kind"),
                        "description": type_info.get("description"),
                    }
                )

            for field in type_info.get("fields") or []:
                field_name = field.get("name", "")
                field_desc = field.get("description", "") or ""
                if keyword_lower in field_name.lower() or keyword_lower in field_desc.lower():
                    matching_fields.append(
                        {
                            "field_name": field_name,
                            "parent_type": type_name,
                            "description": field.get("description"),
                        }
                    )

        if not matching_types and not matching_fields:
            return {
                "keyword": keyword,
                "matching_types": [],
                "matching_fields": [],
                "total_matches": 0,
                "message": (
                    f"No types or fields matching '{keyword}'. Try broader terms like "
                    "'device', 'ip', 'vlan', 'site'."
                ),
            }

        return {
            "keyword": keyword,
            "matching_types": matching_types,
            "matching_fields": matching_fields[:50],
            "total_matches": len(matching_types) + len(matching_fields),
        }

    @mcp_instance.tool
    def netbox_graphql_type_details(type_name: str) -> dict[str, Any]:
        """Get detailed field and argument information for a specific NetBox GraphQL type.

        Use this tool after netbox_graphql_schema_search to inspect the exact fields,
        arguments, and nested types available for a specific GraphQL type before
        writing your query.

        Examples:
            netbox_graphql_type_details("DeviceType") -> fields: id, name, site, interfaces, ...
            netbox_graphql_type_details("InterfaceType") -> fields: name, ip_addresses, ...
            netbox_graphql_type_details("IPAddressType") -> fields: address, dns_name, status, ...

        Args:
            type_name: The exact GraphQL type name to introspect (case-sensitive)

        Returns:
            Dict with type details including 'name', 'kind', 'description', 'fields'
            (each with name, type, description, and args), and 'enum_values' for
            enum types. Returns 'error' key if type not found or introspection fails.
        """
        if not type_name or not type_name.strip():
            raise ValueError("type_name must be a non-empty string")

        escaped_type_name = type_name.replace('"', '\\"')
        introspection_query = """
        {
          __type(name: "__TYPE_NAME__") {
            name
            kind
            description
            fields {
              name
              description
              type {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
              args {
                name
                description
                type {
                  name
                  kind
                }
              }
            }
            enumValues {
              name
              description
            }
            inputFields {
              name
              description
              type {
                name
                kind
              }
            }
          }
        }
        """
        introspection_query = introspection_query.replace("__TYPE_NAME__", escaped_type_name)

        try:
            result = netbox_client.graphql(introspection_query)
        except (ValueError, requests.HTTPError) as e:
            return {"error": f"GraphQL introspection failed: {e}"}

        if "error" in result:
            return result

        type_data = result.get("data", {}).get("__type")
        if type_data is None:
            return {
                "error": (
                    f"Type '{type_name}' not found in NetBox GraphQL schema. "
                    "Use netbox_graphql_schema_search to discover available types."
                )
            }

        return type_data
