"""Tests for write tool behavior (create/update/delete)."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from netbox_mcp_server.server import (
    netbox_create_object,
    netbox_delete_object,
    netbox_update_object,
)


# ============================================================================
# Create
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_create_object_happy_path(mock_netbox):
    mock_netbox.create.return_value = {"id": 42, "name": "test-site"}

    result = netbox_create_object(
        object_type="dcim.site",
        data={"name": "test-site", "slug": "test-site"},
    )

    mock_netbox.create.assert_called_once_with(
        "dcim/sites",
        {"name": "test-site", "slug": "test-site"},
        fallback_endpoint=None,
    )
    assert result == {"id": 42, "name": "test-site"}


@patch("netbox_mcp_server.server.netbox")
def test_create_object_invalid_type(mock_netbox):
    with pytest.raises(ValueError, match="Invalid object_type"):
        netbox_create_object(object_type="not.a.real.type", data={"name": "x"})
    mock_netbox.create.assert_not_called()


@patch("netbox_mcp_server.server.netbox")
def test_create_object_empty_data(mock_netbox):
    with pytest.raises(ValueError, match="non-empty"):
        netbox_create_object(object_type="dcim.site", data={})
    mock_netbox.create.assert_not_called()


@patch("netbox_mcp_server.server.NETBOX_OBJECT_TYPES")
@patch("netbox_mcp_server.server.netbox")
def test_create_object_passes_fallback_endpoint(mock_netbox, mock_types):
    """fallback_endpoint from NETBOX_OBJECT_TYPES is forwarded to the client."""
    mock_types.__contains__.return_value = True
    mock_types.__getitem__.return_value = {
        "endpoint": "vpn/tunnels",
        "fallback_endpoint": "plugins/vpn/tunnels",
    }
    mock_netbox.create.return_value = {"id": 1}

    netbox_create_object(object_type="vpn.tunnel", data={"name": "t"})

    mock_netbox.create.assert_called_once_with(
        "vpn/tunnels", {"name": "t"}, fallback_endpoint="plugins/vpn/tunnels"
    )


# ============================================================================
# Update
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_update_object_happy_path(mock_netbox):
    mock_netbox.update.return_value = {"id": 7, "name": "renamed"}

    result = netbox_update_object(
        object_type="dcim.site",
        object_id=7,
        data={"name": "renamed"},
    )

    mock_netbox.update.assert_called_once_with(
        "dcim/sites", 7, {"name": "renamed"}, fallback_endpoint=None
    )
    assert result == {"id": 7, "name": "renamed"}


@patch("netbox_mcp_server.server.netbox")
def test_update_object_invalid_type(mock_netbox):
    with pytest.raises(ValueError, match="Invalid object_type"):
        netbox_update_object(object_type="not.real", object_id=1, data={"name": "x"})
    mock_netbox.update.assert_not_called()


@patch("netbox_mcp_server.server.netbox")
def test_update_object_empty_data(mock_netbox):
    with pytest.raises(ValueError, match="non-empty"):
        netbox_update_object(object_type="dcim.site", object_id=1, data={})
    mock_netbox.update.assert_not_called()


@patch("netbox_mcp_server.server.netbox")
def test_update_object_dry_run_returns_diff_without_patch(mock_netbox):
    """dry_run=True fetches the current object and never calls update."""
    mock_netbox.get.return_value = {
        "id": 7,
        "name": "old",
        "description": "unchanged",
    }

    result = netbox_update_object(
        object_type="dcim.site",
        object_id=7,
        data={"name": "new"},
        dry_run=True,
    )

    mock_netbox.get.assert_called_once_with("dcim/sites", id=7, fallback_endpoint=None)
    mock_netbox.update.assert_not_called()
    assert result == {
        "dry_run": True,
        "object_type": "dcim.site",
        "object_id": 7,
        "current": {"name": "old"},
        "proposed": {"name": "new"},
    }


# ============================================================================
# Delete
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_delete_object_happy_path(mock_netbox):
    mock_netbox.delete.return_value = True

    result = netbox_delete_object(
        object_type="dcim.site", object_id=99, confirm=True
    )

    mock_netbox.delete.assert_called_once_with(
        "dcim/sites", 99, fallback_endpoint=None
    )
    assert result == {"deleted": True, "object_type": "dcim.site", "object_id": 99}


@patch("netbox_mcp_server.server.netbox")
def test_delete_object_requires_confirm(mock_netbox):
    """Without confirm=True, delete refuses and never hits the client."""
    with pytest.raises(ValueError, match="confirm=True"):
        netbox_delete_object(object_type="dcim.site", object_id=99)
    mock_netbox.delete.assert_not_called()


@patch("netbox_mcp_server.server.netbox")
def test_delete_object_raises_when_client_returns_false(mock_netbox):
    """Non-204 success must surface as an error, not a silent 'deleted: True'."""
    mock_netbox.delete.return_value = False

    with pytest.raises(RuntimeError, match="non-204"):
        netbox_delete_object(object_type="dcim.site", object_id=99, confirm=True)


@patch("netbox_mcp_server.server.netbox")
def test_delete_object_invalid_type(mock_netbox):
    with pytest.raises(ValueError, match="Invalid object_type"):
        netbox_delete_object(object_type="not.real", object_id=1, confirm=True)
    mock_netbox.delete.assert_not_called()


@patch("netbox_mcp_server.server.netbox")
def test_delete_object_dry_run_returns_target_without_deleting(mock_netbox):
    """dry_run=True fetches the target and never calls delete (confirm irrelevant)."""
    mock_netbox.get.return_value = {"id": 99, "name": "doomed"}

    result = netbox_delete_object(
        object_type="dcim.site", object_id=99, dry_run=True
    )

    mock_netbox.get.assert_called_once_with("dcim/sites", id=99, fallback_endpoint=None)
    mock_netbox.delete.assert_not_called()
    assert result == {
        "dry_run": True,
        "object_type": "dcim.site",
        "object_id": 99,
        "target": {"id": 99, "name": "doomed"},
    }


# ============================================================================
# Error translation
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_http_error_translated_to_value_error_with_json_body(mock_netbox):
    response = MagicMock(spec=httpx.Response)
    response.status_code = 400
    response.json.return_value = {"name": ["This field is required."]}
    mock_netbox.create.side_effect = httpx.HTTPStatusError(
        "400 Bad Request", request=MagicMock(), response=response
    )

    with pytest.raises(ValueError, match="This field is required"):
        netbox_create_object(object_type="dcim.site", data={"slug": "x"})


@patch("netbox_mcp_server.server.netbox")
def test_http_error_falls_back_to_text_when_body_not_json(mock_netbox):
    response = MagicMock(spec=httpx.Response)
    response.status_code = 500
    response.json.side_effect = ValueError("not json")
    response.text = "Internal Server Error"
    mock_netbox.update.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=MagicMock(), response=response
    )

    with pytest.raises(ValueError, match="Internal Server Error"):
        netbox_update_object(object_type="dcim.site", object_id=1, data={"name": "x"})
