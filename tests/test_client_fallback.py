"""Tests for NetBoxRestClient fallback mechanism.

The fallback mechanism allows the client to try an alternative endpoint
when the primary endpoint returns 404. This is used for NetBox version
compatibility when endpoints move between API versions.
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


# ============================================================================
# Fallback Trigger Conditions
# ============================================================================


def test_fallback_triggered_on_404_with_fallback_endpoint(client):
    """When primary returns 404 and fallback provided, should try fallback."""
    primary_response = MagicMock()
    primary_response.status_code = 404

    fallback_response = MagicMock()
    fallback_response.status_code = 200
    fallback_response.json.return_value = {"count": 1, "results": [{"id": 1}]}
    fallback_response.raise_for_status = MagicMock()

    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = [primary_response, fallback_response]

        result = client.get(
            "core/object-types",
            params={"limit": 5},
            fallback_endpoint="extras/object-types",
        )

        assert mock_get.call_count == 2
        # Verify first call was to primary endpoint
        assert "core/object-types" in mock_get.call_args_list[0][0][0]
        # Verify second call was to fallback endpoint
        assert "extras/object-types" in mock_get.call_args_list[1][0][0]
        assert result == {"count": 1, "results": [{"id": 1}]}


def test_fallback_not_triggered_on_success(client):
    """When primary succeeds, fallback should never be called."""
    primary_response = MagicMock()
    primary_response.status_code = 200
    primary_response.json.return_value = {"count": 5, "results": []}
    primary_response.raise_for_status = MagicMock()

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value = primary_response

        result = client.get(
            "core/object-types",
            params={"limit": 5},
            fallback_endpoint="extras/object-types",
        )

        # Only one call should be made
        assert mock_get.call_count == 1
        assert result == {"count": 5, "results": []}


def test_fallback_not_triggered_on_non_404_error(client):
    """When primary returns 500/403/etc, should NOT try fallback."""
    primary_response = MagicMock()
    primary_response.status_code = 500
    primary_response.raise_for_status.side_effect = requests.HTTPError("Server error")

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value = primary_response

        with pytest.raises(requests.HTTPError):
            client.get(
                "core/object-types",
                fallback_endpoint="extras/object-types",
            )

        # Only primary should be called, not fallback
        assert mock_get.call_count == 1


def test_fallback_not_triggered_on_403_forbidden(client):
    """When primary returns 403 Forbidden, should NOT try fallback."""
    primary_response = MagicMock()
    primary_response.status_code = 403
    primary_response.raise_for_status.side_effect = requests.HTTPError("Forbidden")

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value = primary_response

        with pytest.raises(requests.HTTPError):
            client.get(
                "core/object-types",
                fallback_endpoint="extras/object-types",
            )

        assert mock_get.call_count == 1


def test_fallback_not_triggered_without_fallback_endpoint(client):
    """When no fallback provided, 404 should propagate immediately."""
    primary_response = MagicMock()
    primary_response.status_code = 404
    primary_response.raise_for_status.side_effect = requests.HTTPError("Not found")

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value = primary_response

        with pytest.raises(requests.HTTPError):
            client.get("core/object-types", fallback_endpoint=None)

        assert mock_get.call_count == 1


def test_fallback_not_triggered_with_empty_fallback(client):
    """When fallback is empty string, should not trigger fallback."""
    primary_response = MagicMock()
    primary_response.status_code = 404
    primary_response.raise_for_status.side_effect = requests.HTTPError("Not found")

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value = primary_response

        with pytest.raises(requests.HTTPError):
            client.get("core/object-types", fallback_endpoint="")

        # Empty string is falsy, so no fallback attempted
        assert mock_get.call_count == 1


# ============================================================================
# Fallback Error Handling
# ============================================================================


def test_fallback_error_propagates(client):
    """When fallback also fails, its error should propagate."""
    primary_response = MagicMock()
    primary_response.status_code = 404

    fallback_response = MagicMock()
    fallback_response.status_code = 500
    fallback_response.raise_for_status.side_effect = requests.HTTPError("Fallback failed")

    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = [primary_response, fallback_response]

        with pytest.raises(requests.HTTPError, match="Fallback failed"):
            client.get(
                "core/object-types",
                fallback_endpoint="extras/object-types",
            )

        assert mock_get.call_count == 2


def test_both_endpoints_404_propagates_fallback_error(client):
    """When both primary and fallback return 404, fallback 404 propagates."""
    primary_response = MagicMock()
    primary_response.status_code = 404

    fallback_response = MagicMock()
    fallback_response.status_code = 404
    fallback_response.raise_for_status.side_effect = requests.HTTPError("Not found")

    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = [primary_response, fallback_response]

        with pytest.raises(requests.HTTPError):
            client.get(
                "core/object-types",
                fallback_endpoint="extras/object-types",
            )

        assert mock_get.call_count == 2


# ============================================================================
# Parameter Passing
# ============================================================================


def test_fallback_preserves_params(client):
    """Fallback request should use same params as primary."""
    primary_response = MagicMock()
    primary_response.status_code = 404

    fallback_response = MagicMock()
    fallback_response.status_code = 200
    fallback_response.json.return_value = {"results": []}
    fallback_response.raise_for_status = MagicMock()

    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = [primary_response, fallback_response]

        client.get(
            "core/object-types",
            params={"limit": 10, "name__ic": "test"},
            fallback_endpoint="extras/object-types",
        )

        # Both calls should have same params
        primary_params = mock_get.call_args_list[0][1]["params"]
        fallback_params = mock_get.call_args_list[1][1]["params"]
        assert primary_params == fallback_params == {"limit": 10, "name__ic": "test"}


def test_fallback_preserves_id_in_url(client):
    """When fetching by ID, fallback should include same ID."""
    primary_response = MagicMock()
    primary_response.status_code = 404

    fallback_response = MagicMock()
    fallback_response.status_code = 200
    fallback_response.json.return_value = {"id": 123, "name": "test"}
    fallback_response.raise_for_status = MagicMock()

    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = [primary_response, fallback_response]

        client.get(
            "core/object-types",
            id=123,
            fallback_endpoint="extras/object-types",
        )

        # Both URLs should include the ID
        primary_url = mock_get.call_args_list[0][0][0]
        fallback_url = mock_get.call_args_list[1][0][0]
        assert "/123/" in primary_url
        assert "/123/" in fallback_url


def test_fallback_preserves_verify_ssl(client):
    """Fallback request should use same SSL verification setting."""
    primary_response = MagicMock()
    primary_response.status_code = 404

    fallback_response = MagicMock()
    fallback_response.status_code = 200
    fallback_response.json.return_value = {"results": []}
    fallback_response.raise_for_status = MagicMock()

    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = [primary_response, fallback_response]

        client.get(
            "core/object-types",
            fallback_endpoint="extras/object-types",
        )

        # Both calls should have same verify setting
        primary_verify = mock_get.call_args_list[0][1]["verify"]
        fallback_verify = mock_get.call_args_list[1][1]["verify"]
        assert primary_verify == fallback_verify == True  # noqa: E712


# ============================================================================
# URL Construction
# ============================================================================


def test_fallback_builds_correct_url(client):
    """Fallback should build proper API URL."""
    primary_response = MagicMock()
    primary_response.status_code = 404

    fallback_response = MagicMock()
    fallback_response.status_code = 200
    fallback_response.json.return_value = {"results": []}
    fallback_response.raise_for_status = MagicMock()

    with patch.object(client.session, "get") as mock_get:
        mock_get.side_effect = [primary_response, fallback_response]

        client.get(
            "core/object-types",
            fallback_endpoint="extras/object-types",
        )

        fallback_url = mock_get.call_args_list[1][0][0]
        assert fallback_url == "https://netbox.example.com/api/extras/object-types/"
