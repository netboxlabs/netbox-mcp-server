"""Tests for NetBoxRestClient GraphQL method.

The GraphQL method provides access to NetBox's GraphQL API endpoint,
which is located at /graphql/ (not under /api/).
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

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
