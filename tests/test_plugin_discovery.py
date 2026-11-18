"""Tests for plugin object-type discovery.

`discover_plugin_types` queries NetBox's object-types endpoint for installed
plugin models and returns them in the same format as NETBOX_OBJECT_TYPES.
"""

from unittest.mock import MagicMock

import httpx
import pytest

from netbox_mcp_server.server import discover_plugin_types


def _plugin_row(
    app_label: str,
    model: str,
    rest_url: str,
    display: str | None = None,
    is_plugin: bool = True,
) -> dict:
    row = {
        "app_label": app_label,
        "model": model,
        "rest_api_endpoint": rest_url,
        "is_plugin_model": is_plugin,
    }
    if display is not None:
        row["display"] = display
    return row


@pytest.fixture
def client():
    """Mock NetBox client with a configurable get() method."""
    return MagicMock()


# ============================================================================
# Happy path
# ============================================================================


def test_discovers_plugin_types(client):
    """Plugin rows with REST endpoints are returned in expected format."""
    client.get.return_value = {
        "results": [
            _plugin_row(
                "netbox_dns",
                "zone",
                "/api/plugins/netbox-dns/zones/",
                display="DNS Zone",
            ),
        ],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert result == {
        "netbox_dns.zone": {
            "name": "DNS Zone",
            "endpoint": "plugins/netbox-dns/zones",
        },
    }


def test_falls_back_to_model_when_display_missing(client):
    """If object-type has no `display` field, use the model name."""
    client.get.return_value = {
        "results": [
            _plugin_row("netbox_dns", "zone", "/api/plugins/netbox-dns/zones/"),
        ],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert result["netbox_dns.zone"]["name"] == "zone"


# ============================================================================
# Filtering
# ============================================================================


def test_skips_non_plugin_models(client):
    """Core (non-plugin) models must be excluded from result."""
    client.get.return_value = {
        "results": [
            _plugin_row("dcim", "device", "/api/dcim/devices/", is_plugin=False),
            _plugin_row("netbox_dns", "zone", "/api/plugins/netbox-dns/zones/"),
        ],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert "dcim.device" not in result
    assert "netbox_dns.zone" in result


def test_skips_rows_missing_rest_endpoint(client):
    """Plugin models without a REST API endpoint must be skipped."""
    client.get.return_value = {
        "results": [
            _plugin_row("netbox_dns", "internal_only", rest_url=""),
            _plugin_row("netbox_dns", "zone", "/api/plugins/netbox-dns/zones/"),
        ],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert "netbox_dns.internal_only" not in result
    assert "netbox_dns.zone" in result


def test_skips_rows_missing_app_label_or_model(client):
    """Rows missing either app_label or model are ignored."""
    client.get.return_value = {
        "results": [
            {
                "app_label": "",
                "model": "zone",
                "rest_api_endpoint": "/api/plugins/x/zones/",
                "is_plugin_model": True,
            },
            {
                "app_label": "netbox_dns",
                "model": "",
                "rest_api_endpoint": "/api/plugins/x/zones/",
                "is_plugin_model": True,
            },
        ],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert result == {}


def test_skips_collision_with_core_type(client):
    """Plugin type whose key collides with a core type is dropped."""
    client.get.return_value = {
        "results": [
            _plugin_row("dcim", "device", "/api/plugins/fake/devices/"),
        ],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert "dcim.device" not in result


# ============================================================================
# REST URL -> endpoint conversion
# ============================================================================


@pytest.mark.parametrize(
    ("rest_url", "expected_endpoint"),
    [
        ("/api/plugins/netbox-dns/zones/", "plugins/netbox-dns/zones"),
        ("api/plugins/netbox-dns/zones/", "plugins/netbox-dns/zones"),
        ("/plugins/netbox-dns/zones", "plugins/netbox-dns/zones"),
        (
            "/api/plugins/netbox-branching/branches/",
            "plugins/netbox-branching/branches",
        ),
    ],
)
def test_converts_rest_url_to_endpoint(client, rest_url, expected_endpoint):
    """REST API URL is normalized by stripping leading /api/ and surrounding slashes."""
    client.get.return_value = {
        "results": [_plugin_row("plug", "thing", rest_url)],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert result["plug.thing"]["endpoint"] == expected_endpoint


# ============================================================================
# Pagination
# ============================================================================


def test_follows_pagination(client):
    """Discovery paginates until `next` is null."""
    page_1 = {
        "results": [_plugin_row("plug_a", "thing", "/api/plugins/a/things/")],
        "next": "https://netbox.example.com/api/core/object-types/?limit=100&offset=1",
    }
    page_2 = {
        "results": [_plugin_row("plug_b", "thing", "/api/plugins/b/things/")],
        "next": None,
    }
    client.get.side_effect = [page_1, page_2]

    result = discover_plugin_types(client)

    assert set(result.keys()) == {"plug_a.thing", "plug_b.thing"}
    assert client.get.call_count == 2
    # Second call should have advanced the offset
    second_call_params = client.get.call_args_list[1].kwargs["params"]
    assert second_call_params["offset"] == 1


@pytest.mark.parametrize("page_size", [2, 100])
def test_discovers_all_types_when_server_caps_page_size(client: MagicMock, page_size: int) -> None:
    """NetBox may return fewer rows than the requested page limit."""
    rows = [
        _plugin_row("plug", f"type_{index}", f"/api/plugins/plug/type-{index}/")
        for index in range(5)
    ]

    def get_page(endpoint: str, params: dict, fallback_endpoint: str | None = None) -> dict:
        offset = params["offset"]
        results = rows[offset : offset + page_size]
        next_offset = offset + len(results)
        return {
            "results": results,
            "next": (
                f"https://netbox.example.com/api/core/object-types/?offset={next_offset}"
                if next_offset < len(rows)
                else None
            ),
        }

    client.get.side_effect = get_page

    result = discover_plugin_types(client)

    assert set(result) == {f"plug.type_{index}" for index in range(5)}
    assert client.get.call_count == (len(rows) + page_size - 1) // page_size


def test_stops_on_empty_page_with_next_link(client: MagicMock) -> None:
    """An empty page cannot advance discovery to another offset."""
    client.get.return_value = {
        "results": [],
        "next": "https://netbox.example.com/api/core/object-types/?offset=100",
    }

    assert discover_plugin_types(client) == {}
    assert client.get.call_count == 1


def test_stops_when_next_missing(client):
    """Single page with no `next` key terminates cleanly."""
    client.get.return_value = {
        "results": [_plugin_row("plug", "thing", "/api/plugins/x/things/")],
    }

    result = discover_plugin_types(client)

    assert "plug.thing" in result
    assert client.get.call_count == 1


# ============================================================================
# Graceful degradation
# ============================================================================


def test_returns_empty_dict_on_http_error(client):
    """HTTP errors are swallowed and empty dict returned."""
    client.get.side_effect = httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock())

    result = discover_plugin_types(client)

    assert result == {}


def test_returns_empty_dict_on_network_error(client):
    """Transport errors (timeouts, DNS, connection refused) are swallowed."""
    client.get.side_effect = httpx.ConnectError("connection refused")

    result = discover_plugin_types(client)

    assert result == {}


def test_returns_empty_dict_on_malformed_response(client):
    """ValueError from unexpected payload shape is swallowed."""
    client.get.side_effect = ValueError("bad json")

    result = discover_plugin_types(client)

    assert result == {}


def test_programmer_errors_still_surface(client):
    """AttributeError (likely a bug in our code) must not be silently swallowed."""
    client.get.side_effect = AttributeError("oops")

    with pytest.raises(AttributeError):
        discover_plugin_types(client)
