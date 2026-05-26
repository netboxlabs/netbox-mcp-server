"""Tests for MCP tool descriptions."""

import asyncio

from netbox_mcp_server.server import mcp


def test_get_objects_description_warns_about_field_specific_lookup_support():
    """The LLM-facing filter guidance should not imply universal lookup support."""
    tool = asyncio.run(mcp.get_tool("netbox_get_objects"))

    description = tool.description

    assert "Lookup support is field-specific" in description
    assert "silently ignore unsupported" in description
    assert "'__in' suffix is not supported" in description
    assert "{'name__ic': 'switch', 'id__in'" not in description
    assert "id__in': [1, 2, 3]" not in description
