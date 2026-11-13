"""Tests for MCP tool annotations."""

import asyncio

from netbox_mcp_server.server import mcp


def test_all_tools_declare_read_only_hint():
    """Each tool must declare readOnlyHint, because the server is read-only."""
    tools = asyncio.run(mcp.list_tools())

    assert tools
    for tool in tools:
        assert tool.annotations is not None, tool.name
        assert tool.annotations.readOnlyHint is True, tool.name
