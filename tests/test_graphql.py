"""Tests for NetBoxRestClient GraphQL method.

The GraphQL method provides access to NetBox's GraphQL API endpoint,
which is located at /graphql/ (not under /api/).
"""

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from netbox_mcp_server.graphql_tools import register_graphql_tools
from netbox_mcp_server.netbox_client import NetBoxRestClient


@pytest.fixture
def client():
    """Create a test client."""
    return NetBoxRestClient(
        url="https://netbox.example.com",
        token="test-token",
        verify_ssl=True,
    )


def test_graphql_valid_query(client):
    """GraphQL method should return parsed JSON response for valid query."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"data": {"device_list": [{"id": 1}]}}'
    mock_response.json.return_value = {"data": {"device_list": [{"id": 1}]}}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "post") as mock_post:
        mock_post.return_value = mock_response

        result = client.graphql("{ device_list { id } }")

        assert result == {"data": {"device_list": [{"id": 1}]}}
        mock_post.assert_called_once()


def test_graphql_with_variables(client):
    """GraphQL method should include variables in POST body."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"data": {"device": {"id": 1, "name": "router-01"}}}'
    mock_response.json.return_value = {"data": {"device": {"id": 1, "name": "router-01"}}}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "post") as mock_post:
        mock_post.return_value = mock_response

        result = client.graphql(
            "query GetDevice($id: Int!) { device(id: $id) { id name } }",
            variables={"id": 1},
        )

        # Verify POST body contains query and variables
        call_args = mock_post.call_args
        assert (
            call_args[1]["json"]["query"]
            == "query GetDevice($id: Int!) { device(id: $id) { id name } }"
        )
        assert call_args[1]["json"]["variables"] == {"id": 1}
        assert result == {"data": {"device": {"id": 1, "name": "router-01"}}}


def test_graphql_url_uses_base_url_not_api_url(client):
    """GraphQL URL should use /graphql/ not /api/graphql/."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"data": {}}'
    mock_response.json.return_value = {"data": {}}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "post") as mock_post:
        mock_post.return_value = mock_response

        client.graphql("{ test }")

        # Verify URL is correct
        call_args = mock_post.call_args
        url = call_args[0][0]
        assert url == "https://netbox.example.com/graphql/"
        assert "/api/graphql/" not in url


def test_graphql_http_error_raises(client):
    """GraphQL method should raise HTTPError on 4xx/5xx responses."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")

    with patch.object(client.session, "post") as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError, match="401 Unauthorized"):
            client.graphql("{ test }")


def test_graphql_non_json_response_raises_value_error(client):
    """GraphQL method should raise ValueError for non-JSON responses."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.content = b"<html>GraphQL is disabled</html>"
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "post") as mock_post:
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match=r"non-JSON|GraphQL may be disabled"):
            client.graphql("{ test }")


def test_graphql_oversized_response_returns_truncation_message(client):
    """GraphQL method should return error dict for responses exceeding 500KB."""
    oversized_content = b"x" * 600_000  # 600KB

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = oversized_content
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "post") as mock_post:
        mock_post.return_value = mock_response

        result = client.graphql("{ test }")

        assert "error" in result
        assert "500KB" in result["error"] or "500" in result["error"]
        assert "narrow" in result["error"].lower() or "query" in result["error"].lower()


# --- GraphQL Query Tool Tests ---


class _ToolCapture:
    """Capture tool functions registered via @mcp.tool."""

    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., dict[str, Any]]] = {}

    def tool(self, func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        self.tools[func.__name__] = func
        return func


@pytest.fixture
def mock_netbox_client() -> MagicMock:
    """Return a mocked NetBox client for tool testing."""
    return MagicMock(spec=NetBoxRestClient)


def _make_graphql_query_tool(
    mock_client: MagicMock,
) -> Callable[..., dict[str, Any]]:
    """Register graphql tools and return netbox_graphql_query."""
    capture = _ToolCapture()
    register_graphql_tools(capture, mock_client)
    return capture.tools["netbox_graphql_query"]


def test_graphql_query_valid(mock_netbox_client: MagicMock):
    """netbox_graphql_query should return raw client GraphQL data."""
    mock_netbox_client.graphql.return_value = {"data": {"device_list": [{"id": 1}]}}

    tool = _make_graphql_query_tool(mock_netbox_client)
    result = tool(query="{ device_list { id } }")

    assert result == {"data": {"device_list": [{"id": 1}]}}
    mock_netbox_client.graphql.assert_called_once_with("{ device_list { id } }", None)


def test_graphql_query_with_variables(mock_netbox_client: MagicMock):
    """netbox_graphql_query should pass variables to client.graphql."""
    mock_netbox_client.graphql.return_value = {"data": {"device": {"id": 1, "name": "router-01"}}}

    tool = _make_graphql_query_tool(mock_netbox_client)
    result = tool(
        query="query GetDevice($id: Int!) { device(id: $id) { id name } }",
        variables={"id": 1},
    )

    assert result == {"data": {"device": {"id": 1, "name": "router-01"}}}
    mock_netbox_client.graphql.assert_called_once_with(
        "query GetDevice($id: Int!) { device(id: $id) { id name } }",
        {"id": 1},
    )


def test_graphql_query_partial_errors_returned_intact(mock_netbox_client: MagicMock):
    """netbox_graphql_query should return partial data and errors unchanged."""
    graphql_response = {
        "data": {"device_list": [{"id": 1}]},
        "errors": [{"message": "Field 'foo' not found"}],
    }
    mock_netbox_client.graphql.return_value = graphql_response

    tool = _make_graphql_query_tool(mock_netbox_client)
    result = tool(query="{ device_list { id foo } }")

    assert result == graphql_response


def test_graphql_query_http_error_returns_error_dict(mock_netbox_client: MagicMock):
    """netbox_graphql_query should return error dict on HTTPError."""
    mock_netbox_client.graphql.side_effect = requests.HTTPError("503 Service Unavailable")

    tool = _make_graphql_query_tool(mock_netbox_client)
    result = tool(query="{ device_list { id } }")

    assert result == {"error": "HTTP error querying NetBox GraphQL: 503 Service Unavailable"}


def test_graphql_query_value_error_returns_error_dict(mock_netbox_client: MagicMock):
    """netbox_graphql_query should return error dict on ValueError."""
    mock_netbox_client.graphql.side_effect = ValueError("GraphQL disabled")

    tool = _make_graphql_query_tool(mock_netbox_client)
    result = tool(query="{ device_list { id } }")

    assert result == {"error": "GraphQL disabled"}


def test_graphql_query_empty_query_raises_value_error(mock_netbox_client: MagicMock):
    """netbox_graphql_query should validate non-empty query."""
    tool = _make_graphql_query_tool(mock_netbox_client)

    with pytest.raises(ValueError, match="non-empty GraphQL query string"):
        tool(query="")


def test_graphql_query_whitespace_query_raises_value_error(mock_netbox_client: MagicMock):
    """netbox_graphql_query should reject whitespace-only query strings."""
    tool = _make_graphql_query_tool(mock_netbox_client)

    with pytest.raises(ValueError, match="non-empty GraphQL query string"):
        tool(query="   \n\t")


def _make_schema_search_tool(mock_client: MagicMock) -> Callable[..., dict[str, Any]]:
    capture = _ToolCapture()
    register_graphql_tools(capture, mock_client)
    return capture.tools["netbox_graphql_schema_search"]


def test_schema_search_matches_type_names(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__schema": {
                "types": [
                    {
                        "name": "DeviceType",
                        "kind": "OBJECT",
                        "description": "A network device",
                        "fields": [],
                    }
                ]
            }
        }
    }

    tool = _make_schema_search_tool(mock_netbox_client)
    result = tool(keyword="device")

    assert any(t["name"] == "DeviceType" for t in result["matching_types"])


def test_schema_search_matches_field_names(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__schema": {
                "types": [
                    {
                        "name": "IPAddressType",
                        "kind": "OBJECT",
                        "description": "IP address",
                        "fields": [
                            {"name": "ip_address", "description": "Address"},
                            {"name": "dns_name", "description": "DNS"},
                        ],
                    }
                ]
            }
        }
    }

    tool = _make_schema_search_tool(mock_netbox_client)
    result = tool(keyword="ip")

    assert any(f["field_name"] == "ip_address" for f in result["matching_fields"])


def test_schema_search_excludes_internal_types_by_default(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__schema": {
                "types": [
                    {
                        "name": "__Schema",
                        "kind": "OBJECT",
                        "description": "Internal schema type",
                        "fields": [],
                    }
                ]
            }
        }
    }

    tool = _make_schema_search_tool(mock_netbox_client)
    result = tool(keyword="schema")

    type_names = {t["name"] for t in result["matching_types"]}
    assert "__Schema" not in type_names


def test_schema_search_includes_internal_types_when_requested(
    mock_netbox_client: MagicMock,
):
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__schema": {
                "types": [
                    {
                        "name": "__Schema",
                        "kind": "OBJECT",
                        "description": "Internal schema type",
                        "fields": [],
                    }
                ]
            }
        }
    }

    tool = _make_schema_search_tool(mock_netbox_client)
    result = tool(keyword="schema", include_internal_types=True)

    type_names = {t["name"] for t in result["matching_types"]}
    assert "__Schema" in type_names


def test_schema_search_no_matches_returns_message(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__schema": {
                "types": [
                    {
                        "name": "DeviceType",
                        "kind": "OBJECT",
                        "description": "A network device",
                        "fields": [{"name": "name", "description": "Device name"}],
                    }
                ]
            }
        }
    }

    tool = _make_schema_search_tool(mock_netbox_client)
    result = tool(keyword="xyznonexistent")

    assert result["matching_types"] == []
    assert result["matching_fields"] == []
    assert "message" in result


def test_schema_search_introspection_failure_returns_error(
    mock_netbox_client: MagicMock,
):
    mock_netbox_client.graphql.side_effect = requests.HTTPError("503 Service Unavailable")

    tool = _make_schema_search_tool(mock_netbox_client)
    result = tool(keyword="device")

    assert "error" in result
    assert "introspection failed" in result["error"]


def test_schema_search_empty_keyword_raises(mock_netbox_client: MagicMock):
    tool = _make_schema_search_tool(mock_netbox_client)

    with pytest.raises(ValueError, match="non-empty search string"):
        tool(keyword="")


def test_schema_search_max_types_limits_results(mock_netbox_client: MagicMock):
    many_types = [
        {
            "name": f"DeviceType{i}",
            "kind": "OBJECT",
            "description": "Device-like type",
            "fields": [],
        }
        for i in range(20)
    ]
    mock_netbox_client.graphql.return_value = {"data": {"__schema": {"types": many_types}}}

    tool = _make_schema_search_tool(mock_netbox_client)
    result = tool(keyword="device", max_types=3)

    assert len(result["matching_types"]) <= 3


def _make_type_details_tool(mock_client: MagicMock) -> Callable[..., dict[str, Any]]:
    capture = _ToolCapture()
    register_graphql_tools(capture, mock_client)
    return capture.tools["netbox_graphql_type_details"]


def test_type_details_valid_type_returns_fields(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__type": {
                "name": "DeviceType",
                "kind": "OBJECT",
                "fields": [{"name": "id"}],
                "enumValues": None,
                "inputFields": None,
            }
        }
    }

    tool = _make_type_details_tool(mock_netbox_client)
    result = tool(type_name="DeviceType")

    assert result["name"] == "DeviceType"
    assert isinstance(result["fields"], list)


def test_type_details_type_not_found_returns_error(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.return_value = {"data": {"__type": None}}

    tool = _make_type_details_tool(mock_netbox_client)
    result = tool(type_name="NonExistentType")

    assert "error" in result
    assert "NonExistentType" in result["error"]


def test_type_details_introspection_failure_returns_error(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.side_effect = requests.HTTPError("503")

    tool = _make_type_details_tool(mock_netbox_client)
    result = tool(type_name="DeviceType")

    assert "error" in result
    assert "introspection failed" in result["error"]


def test_type_details_empty_type_name_raises(mock_netbox_client: MagicMock):
    tool = _make_type_details_tool(mock_netbox_client)

    with pytest.raises(ValueError, match="non-empty string"):
        tool(type_name="")


def test_type_details_enum_type_returns_enum_values(mock_netbox_client: MagicMock):
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__type": {
                "name": "StatusEnum",
                "kind": "ENUM",
                "enumValues": [{"name": "active", "description": "Active"}],
                "fields": None,
                "inputFields": None,
            }
        }
    }

    tool = _make_type_details_tool(mock_netbox_client)
    result = tool(type_name="StatusEnum")

    assert result["kind"] == "ENUM"
    assert result["enumValues"][0]["name"] == "active"


def test_type_details_query_string_has_quoted_type_name(mock_netbox_client: MagicMock):
    """The introspection query must quote the type name (valid GraphQL syntax)."""
    mock_netbox_client.graphql.return_value = {
        "data": {
            "__type": {
                "name": "DeviceType",
                "kind": "OBJECT",
                "description": None,
                "fields": [],
                "enumValues": None,
                "inputFields": None,
            }
        }
    }
    tool = _make_type_details_tool(mock_netbox_client)
    tool(type_name="DeviceType")

    call_args = mock_netbox_client.graphql.call_args
    query_sent = call_args[0][0]
    assert '"DeviceType"' in query_sent, (
        f"Type name must be quoted in query. Got: {query_sent[:200]}"
    )
