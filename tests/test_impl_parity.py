"""Parity test: strict and compat wrappers must produce identical NetBox API calls.

The impl function is shared, so the real risk surface is the compat wrapper's
string-parsing step. Cases here exercise only inputs that are actually
transformed (JSON <-> dict, CSV <-> list). Trivially equivalent numeric casts
(limit=10 vs 10.0) are covered by unit tests elsewhere.
"""

import asyncio
from unittest.mock import patch

import pytest
from fastmcp import Client

from netbox_mcp_server.server import create_mcp

EMPTY_RESPONSE = {"count": 0, "next": None, "previous": None, "results": []}


async def _call(mcp, tool_name: str, arguments: dict):
    async with Client(mcp) as client:
        return await client.call_tool(tool_name, arguments)


@pytest.mark.parametrize(
    ("strict_kwargs", "compat_kwargs"),
    [
        # filters: dict <-> JSON string
        (
            {"object_type": "dcim.site", "filters": {"status": "active"}},
            {"object_type": "dcim.site", "filters": '{"status": "active"}'},
        ),
        (
            {"object_type": "dcim.site", "filters": {"name__ic": "router", "id__in": [1, 2, 3]}},
            {"object_type": "dcim.site", "filters": '{"name__ic": "router", "id__in": [1, 2, 3]}'},
        ),
        # fields: list <-> CSV string
        (
            {"object_type": "dcim.site", "filters": {}, "fields": ["id", "name"]},
            {"object_type": "dcim.site", "filters": "{}", "fields": "id,name"},
        ),
        # n8n-style empty filter string: "null" in compat = {} in strict
        (
            {"object_type": "dcim.site", "filters": {}},
            {"object_type": "dcim.site", "filters": "null"},
        ),
    ],
)
def test_get_objects_parity(strict_kwargs, compat_kwargs):
    """Semantically equivalent inputs to both modes produce identical API params."""
    with patch("netbox_mcp_server.server.netbox") as mock:
        mock.get.return_value = EMPTY_RESPONSE

        strict_mcp = create_mcp(n8n_compat=False)
        asyncio.run(_call(strict_mcp, "netbox_get_objects", strict_kwargs))
        strict_params = mock.get.call_args[1]["params"]

        mock.reset_mock()
        mock.get.return_value = EMPTY_RESPONSE

        compat_mcp = create_mcp(n8n_compat=True)
        asyncio.run(_call(compat_mcp, "netbox_get_objects", compat_kwargs))
        compat_params = mock.get.call_args[1]["params"]

    assert strict_params == compat_params, (
        f"Mode divergence!\nstrict: {strict_params}\ncompat: {compat_params}"
    )


def test_search_objects_parity():
    """Search tool: list[str] in strict <-> CSV in compat.

    Asserts both modes searched the same number of object types (guards
    against _parse_list_param silently dropping a type) and that the
    outgoing API params are identical.
    """
    with patch("netbox_mcp_server.server.netbox") as mock:
        mock.get.return_value = EMPTY_RESPONSE

        strict_mcp = create_mcp(n8n_compat=False)
        asyncio.run(
            _call(
                strict_mcp,
                "netbox_search_objects",
                {
                    "query": "nyc",
                    "object_types": ["dcim.site", "dcim.device"],
                    "fields": ["id", "name"],
                },
            )
        )
        strict_call_count = mock.get.call_count
        # Capture params from the last call; they're structurally identical per-type
        # because _netbox_search_objects_impl builds the same {q, limit, fields} dict.
        strict_params = mock.get.call_args[1]["params"]

        mock.reset_mock()
        mock.get.return_value = EMPTY_RESPONSE

        compat_mcp = create_mcp(n8n_compat=True)
        asyncio.run(
            _call(
                compat_mcp,
                "netbox_search_objects",
                {
                    "query": "nyc",
                    "object_types": "dcim.site,dcim.device",
                    "fields": "id,name",
                },
            )
        )
        compat_call_count = mock.get.call_count
        compat_params = mock.get.call_args[1]["params"]

    assert strict_call_count == compat_call_count, (
        f"Mode divergence in searched types!\n"
        f"strict searched {strict_call_count} types; compat searched {compat_call_count}"
    )
    assert strict_params == compat_params, (
        f"Mode divergence in API params!\nstrict: {strict_params}\ncompat: {compat_params}"
    )
