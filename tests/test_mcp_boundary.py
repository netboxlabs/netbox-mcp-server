"""End-to-end tests through the FastMCP schema-validation boundary.

Most other tests invoke the strict-mode wrappers directly (``tool_fn(...)``),
bypassing Pydantic's schema enforcement. The tests in this file go through
``Client.call_tool``, which is the path every real MCP client takes — the
schema is enforced.

The tests here exercise *compat-mode* behavior: the string-typed tool schemas
n8n's MCP client requires. Strict-mode boundary coverage lives in Task 4's
additions (see ``test_impl_parity.py`` and the strict-mode section below
once added).
"""

import asyncio
from unittest.mock import patch

import pytest
from fastmcp import Client

from netbox_mcp_server.server import create_mcp

EMPTY_RESPONSE = {"count": 0, "next": None, "previous": None, "results": []}


async def _call_compat(tool_name: str, arguments: dict):
    mcp = create_mcp(n8n_compat=True)
    async with Client(mcp) as client:
        return await client.call_tool(tool_name, arguments)


def test_string_filters_accepted_through_mcp_boundary():
    """JSON-string filters — the shape n8n and LLM clients send — must round-trip."""
    with patch("netbox_mcp_server.server.netbox") as mock:
        mock.get.return_value = EMPTY_RESPONSE
        asyncio.run(
            _call_compat(
                "netbox_get_objects",
                {"object_type": "dcim.site", "filters": '{"status": "active"}'},
            )
        )
        params = mock.get.call_args[1]["params"]
        assert params["status"] == "active"


def test_dict_filters_rejected_through_mcp_boundary():
    """Native dicts must be rejected at the boundary.

    Regression guard: if a future refactor widens the schema to accept `object`,
    n8n's `mapTypes` will fail again. See #58 and n8n-io/n8n#19835.
    """
    with patch("netbox_mcp_server.server.netbox") as mock:
        mock.get.return_value = EMPTY_RESPONSE
        with pytest.raises(Exception, match="valid string"):
            asyncio.run(
                _call_compat(
                    "netbox_get_objects",
                    {"object_type": "dcim.site", "filters": {"status": "active"}},
                )
            )


def test_integer_limit_accepted_and_coerced():
    """LLM clients sending integer `limit` must still work.

    JSON Schema `number` (our n8n-compatible annotation) accepts integers,
    and Pydantic coerces them to float before the int(limit) conversion
    inside the function body.
    """
    with patch("netbox_mcp_server.server.netbox") as mock:
        mock.get.return_value = EMPTY_RESPONSE
        asyncio.run(
            _call_compat(
                "netbox_get_objects",
                {"object_type": "dcim.site", "limit": 10},
            )
        )
        assert mock.get.call_args[1]["params"]["limit"] == 10


def test_integer_object_id_accepted_through_mcp_boundary():
    """Native integer IDs (how LLM clients reference objects) must pass schema validation."""
    with patch("netbox_mcp_server.server.netbox") as mock:
        mock.get.return_value = {"id": 42, "name": "site-nyc"}
        asyncio.run(
            _call_compat(
                "netbox_get_object_by_id",
                {"object_type": "dcim.site", "object_id": 42},
            )
        )
        called_endpoint = mock.get.call_args[0][0]
        assert called_endpoint.endswith("/42")
