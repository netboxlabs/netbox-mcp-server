"""Sanity checks that the flag flips the advertised tool schema.

We deliberately do not exhaustively assert every property's type — that would
test FastMCP's schema generation, not our code. One assertion per mode on the
key type difference is enough.
"""

import asyncio

from fastmcp import Client

from netbox_mcp_server.server import create_mcp


async def _get_filters_types(n8n_compat: bool) -> set[str]:
    """Return the set of types accepted by the ``filters`` parameter schema.

    Pydantic renders ``dict | None = None`` as ``anyOf: [{type: object}, {type: null}]``,
    and ``str = "{}"`` as a single ``{type: string}``. Normalising to a set
    lets each test assert the exact accepted type universe.
    """
    mcp = create_mcp(n8n_compat=n8n_compat)
    async with Client(mcp) as client:
        tools = await client.list_tools()
        for tool in tools:
            if tool.name == "netbox_get_objects":
                schema = tool.inputSchema["properties"]["filters"]
                if "anyOf" in schema:
                    return {entry.get("type") for entry in schema["anyOf"]}
                return {schema.get("type")}
    raise AssertionError("netbox_get_objects not found in registered tools")


def test_strict_mode_advertises_object_filters():
    """Default mode advertises filters as JSON object (nullable). No strings allowed."""
    types = asyncio.run(_get_filters_types(n8n_compat=False))
    assert types == {"object", "null"}


def test_compat_mode_advertises_string_filters():
    """Compat mode advertises filters as a string only. No objects allowed."""
    types = asyncio.run(_get_filters_types(n8n_compat=True))
    assert types == {"string"}
