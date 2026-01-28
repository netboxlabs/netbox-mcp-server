"""Tests for fallback endpoint integration in MCP tools.

These tests verify that the server tools correctly pass fallback endpoints
to the NetBox client for types that have version-dependent endpoints.
"""

from unittest.mock import patch

from netbox_mcp_server.server import (
    netbox_get_object_by_id,
    netbox_get_objects,
    netbox_search_objects,
)

# ============================================================================
# netbox_get_objects Fallback Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_get_objects_passes_fallback_for_objecttype(mock_netbox):
    """netbox_get_objects should pass fallback_endpoint for core.objecttype."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="core.objecttype", filters={})

    mock_netbox.get.assert_called_once()
    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] == "extras/object-types"


@patch("netbox_mcp_server.server.netbox")
def test_get_objects_no_fallback_for_regular_types(mock_netbox):
    """netbox_get_objects should pass None fallback for types without fallback."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="dcim.device", filters={})

    mock_netbox.get.assert_called_once()
    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] is None


@patch("netbox_mcp_server.server.netbox")
def test_get_objects_uses_primary_endpoint_for_objecttype(mock_netbox):
    """netbox_get_objects should use core/object-types as primary endpoint."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="core.objecttype", filters={})

    call_args = mock_netbox.get.call_args
    # First positional arg is the endpoint
    primary_endpoint = call_args[0][0]
    assert primary_endpoint == "core/object-types"


# ============================================================================
# netbox_get_object_by_id Fallback Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_get_object_by_id_passes_fallback_for_objecttype(mock_netbox):
    """netbox_get_object_by_id should pass fallback_endpoint for core.objecttype."""
    mock_netbox.get.return_value = {"id": 1, "name": "dcim.device"}

    netbox_get_object_by_id.fn(object_type="core.objecttype", object_id=1)

    mock_netbox.get.assert_called_once()
    call_kwargs = mock_netbox.get.call_args[1]
    # Fallback should include the object ID in the path
    assert call_kwargs["fallback_endpoint"] == "extras/object-types/1"


@patch("netbox_mcp_server.server.netbox")
def test_get_object_by_id_no_fallback_for_regular_types(mock_netbox):
    """netbox_get_object_by_id should pass None fallback for types without fallback."""
    mock_netbox.get.return_value = {"id": 1, "name": "Test Device"}

    netbox_get_object_by_id.fn(object_type="dcim.device", object_id=1)

    mock_netbox.get.assert_called_once()
    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] is None


@patch("netbox_mcp_server.server.netbox")
def test_get_object_by_id_uses_primary_endpoint_with_id(mock_netbox):
    """netbox_get_object_by_id should use correct primary endpoint with ID."""
    mock_netbox.get.return_value = {"id": 42, "name": "dcim.site"}

    netbox_get_object_by_id.fn(object_type="core.objecttype", object_id=42)

    call_args = mock_netbox.get.call_args
    # First positional arg is the endpoint with ID
    primary_endpoint = call_args[0][0]
    assert primary_endpoint == "core/object-types/42"


# ============================================================================
# netbox_search_objects Fallback Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_search_objects_passes_fallback_for_objecttype(mock_netbox):
    """netbox_search_objects should pass fallback_endpoint when searching objecttype."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_search_objects.fn(query="device", object_types=["core.objecttype"])

    mock_netbox.get.assert_called_once()
    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] == "extras/object-types"


@patch("netbox_mcp_server.server.netbox")
def test_search_objects_no_fallback_for_regular_types(mock_netbox):
    """netbox_search_objects should pass None fallback for types without fallback."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_search_objects.fn(query="switch", object_types=["dcim.device"])

    mock_netbox.get.assert_called_once()
    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] is None


@patch("netbox_mcp_server.server.netbox")
def test_search_objects_mixed_types_with_and_without_fallback(mock_netbox):
    """When searching mixed types, each should get correct fallback."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_search_objects.fn(query="test", object_types=["dcim.device", "core.objecttype"])

    assert mock_netbox.get.call_count == 2

    # Find which call was for which type by checking endpoint
    calls = mock_netbox.get.call_args_list
    for call in calls:
        endpoint = call[0][0]
        fallback = call[1]["fallback_endpoint"]
        if "devices" in endpoint:
            assert fallback is None, "dcim.device should have no fallback"
        elif "object-types" in endpoint:
            assert fallback == "extras/object-types", "core.objecttype should have fallback"


# ============================================================================
# New Object Types Tests (NetBox 4.4/4.5 additions)
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_config_context_profile_no_fallback(mock_netbox):
    """extras.configcontextprofile (new in 4.4) should have no fallback."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="extras.configcontextprofile", filters={})

    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] is None


@patch("netbox_mcp_server.server.netbox")
def test_owner_no_fallback(mock_netbox):
    """users.owner (new in 4.5) should have no fallback."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="users.owner", filters={})

    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] is None


@patch("netbox_mcp_server.server.netbox")
def test_owner_group_no_fallback(mock_netbox):
    """users.ownergroup (new in 4.5) should have no fallback."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="users.ownergroup", filters={})

    call_kwargs = mock_netbox.get.call_args[1]
    assert call_kwargs["fallback_endpoint"] is None
