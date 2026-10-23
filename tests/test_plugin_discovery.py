"""Tests for plugin object-type discovery.

`discover_plugin_types` queries NetBox's object-types endpoint for installed
plugin models and returns them in the same format as NETBOX_OBJECT_TYPES.
"""

from unittest.mock import MagicMock
from urllib.parse import urlsplit

import httpx
import pytest

from netbox_mcp_server.netbox_client import NetBoxRestClient
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
    mock_client = MagicMock()
    mock_client.base_url = "https://netbox.example.com"
    mock_client.api_url = "https://netbox.example.com/api"
    return mock_client


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


@pytest.mark.parametrize(
    ("base_url", "rest_url", "expected_endpoint", "expected_plugin_path"),
    [
        (
            "https://netbox.example.com",
            "/api/plugins/netbox-dns/zones/",
            "plugins/netbox-dns/zones",
            "/api/plugins/netbox-dns/zones/",
        ),
        (
            "https://netbox.example.com/netbox",
            "/netbox/api/plugins/netbox-dns/zones/",
            "plugins/netbox-dns/zones",
            "/netbox/api/plugins/netbox-dns/zones/",
        ),
        (
            "https://netbox.example.com/team/netbox",
            "/team/netbox/api/plugins/netbox-dns/zones/",
            "plugins/netbox-dns/zones",
            "/team/netbox/api/plugins/netbox-dns/zones/",
        ),
        (
            "https://netbox.example.com/plugins",
            "/plugins/api/plugins/netbox-dns/zones/",
            "plugins/netbox-dns/zones",
            "/plugins/api/plugins/netbox-dns/zones/",
        ),
        (
            "https://netbox.example.com/plugins",
            "/plugins/netbox-dns/zones/",
            "plugins/netbox-dns/zones",
            "/plugins/api/plugins/netbox-dns/zones/",
        ),
        (
            "https://netbox.example.com/api",
            "/api/api/plugins/netbox-dns/zones/",
            "plugins/netbox-dns/zones",
            "/api/api/plugins/netbox-dns/zones/",
        ),
        (
            "https://netbox.example.com/api",
            "/api/plugins/netbox-dns/zones/",
            "plugins/netbox-dns/zones",
            "/api/api/plugins/netbox-dns/zones/",
        ),
    ],
)
def test_discovered_endpoint_is_requested_once_under_api_base(
    base_url, rest_url, expected_endpoint, expected_plugin_path
):
    """Discovered REST paths remain usable for root and BASE_PATH deployments."""
    requested_paths = []

    def handler(request):
        requested_paths.append(request.url.path)
        if request.url.path.endswith("/object-types/"):
            return httpx.Response(
                200,
                json={
                    "results": [_plugin_row("netbox_dns", "zone", rest_url)],
                    "next": None,
                },
            )
        return httpx.Response(200, json={})

    client = NetBoxRestClient(base_url, "test-token")
    client.session.close()
    client.session = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        plugin_types = discover_plugin_types(client)
        assert plugin_types["netbox_dns.zone"]["endpoint"] == expected_endpoint
        client.get(plugin_types["netbox_dns.zone"]["endpoint"])
    finally:
        client.session.close()

    assert requested_paths == [
        f"{urlsplit(base_url).path.rstrip('/')}/api/core/object-types/",
        expected_plugin_path,
    ]


def test_base_path_prefix_match_requires_a_segment_boundary(client):
    """A similarly named path prefix must remain part of the endpoint."""
    client.base_url = "https://netbox.example.com/netbox"
    client.api_url = "https://netbox.example.com/netbox/api"
    client.get.return_value = {
        "results": [_plugin_row("plug", "thing", "/netboxish/api/plugins/example/things/")],
        "next": None,
    }

    result = discover_plugin_types(client)

    assert result["plug.thing"]["endpoint"] == "netboxish/api/plugins/example/things"


# ============================================================================
# Pagination
# ============================================================================


def test_follows_pagination(client):
    """Discovery paginates until `next` is null."""
    page_1 = {
        "results": [_plugin_row("plug_a", "thing", "/api/plugins/a/things/")],
        "next": "https://netbox.example.com/api/core/object-types/?limit=100&offset=100",
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
    assert second_call_params["offset"] == 100


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
