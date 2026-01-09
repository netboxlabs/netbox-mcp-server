"""NetBox MCP Server - Read-only MCP server for NetBox infrastructure data."""

__version__ = "1.0.0"  # Auto-managed by semantic-release

__all__ = ["NETBOX_OBJECT_TYPES", "NetBoxRestClient", "Settings"]

from netbox_mcp_server.config import Settings
from netbox_mcp_server.netbox_client import NetBoxRestClient
from netbox_mcp_server.netbox_types import NETBOX_OBJECT_TYPES
