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
    """Default mode advertises filters as a required JSON object. No strings or null allowed."""
    types = asyncio.run(_get_filters_types(n8n_compat=False))
    assert types == {"object"}


def test_compat_mode_advertises_string_filters():
    """Compat mode advertises filters as a string only. No objects allowed."""
    types = asyncio.run(_get_filters_types(n8n_compat=True))
    assert types == {"string"}


async def _get_tool_description(tool_name: str, n8n_compat: bool) -> str:
    """Return the ``description`` field of a registered tool as seen by MCP clients."""
    mcp = create_mcp(n8n_compat=n8n_compat)
    async with Client(mcp) as client:
        tools = await client.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool.description or ""
    raise AssertionError(f"{tool_name} not found in registered tools")


def test_compat_mode_description_has_preamble():
    """Compat-mode descriptions warn LLMs about JSON-string / CSV parameter shapes."""
    for tool_name in (
        "netbox_get_objects",
        "netbox_get_object_by_id",
        "netbox_get_changelogs",
        "netbox_search_objects",
    ):
        desc = asyncio.run(_get_tool_description(tool_name, n8n_compat=True))
        assert "JSON STRING" in desc, f"{tool_name} missing JSON-string guidance"
        assert "COMMA-SEPARATED" in desc, f"{tool_name} missing CSV guidance"


def test_strict_mode_description_has_no_preamble():
    """Strict-mode descriptions must not carry the compat preamble (cosmetic noise for strict clients)."""
    for tool_name in (
        "netbox_get_objects",
        "netbox_get_object_by_id",
        "netbox_get_changelogs",
        "netbox_search_objects",
    ):
        desc = asyncio.run(_get_tool_description(tool_name, n8n_compat=False))
        assert "JSON STRING" not in desc, f"{tool_name} leaked compat preamble"
        assert "COMMA-SEPARATED" not in desc, f"{tool_name} leaked compat preamble"


def test_compat_get_object_by_id_has_rich_description():
    """Regression guard for C1: compat's get_object_by_id previously served only a 47-char stub."""
    desc = asyncio.run(_get_tool_description("netbox_get_object_by_id", n8n_compat=True))
    assert "Field filtering reduces response payload" in desc
    assert len(desc) > 500
