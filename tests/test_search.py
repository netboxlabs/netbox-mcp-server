"""Tests for global search functionality (netbox_search_objects tool)."""

from unittest.mock import patch

import pytest
from pydantic import TypeAdapter, ValidationError

from server import NETBOX_OBJECT_TYPES, netbox_search_objects


# ============================================================================
# Parameter Validation Tests
# ============================================================================


def test_limit_validation_rejects_invalid_values():
    """Limit must be between 1 and 100."""
    limit_annotation = netbox_search_objects.fn.__annotations__["limit"]
    adapter = TypeAdapter(limit_annotation)

    # Test boundaries
    with pytest.raises(ValidationError):
        adapter.validate_python(0)

    with pytest.raises(ValidationError):
        adapter.validate_python(101)

    # Valid boundaries should pass
    adapter.validate_python(1)
    adapter.validate_python(100)


def test_invalid_object_type_raises_error():
    """Invalid object type should raise ValueError with helpful message."""
    with pytest.raises(ValueError, match="Invalid object_type"):
        netbox_search_objects.fn(query="test", object_types=["invalid_type_xyz"])


# ============================================================================
# Default Behavior Tests
# ============================================================================


@patch("server.netbox")
def test_searches_default_types_when_none_specified(mock_netbox):
    """When object_types=None, should search 8 default common types."""
    mock_netbox.get.return_value = []

    result = netbox_search_objects.fn(query="test")

    # Should search 8 default types
    assert mock_netbox.get.call_count == 8
    assert isinstance(result, dict)
    assert len(result) == 8


@patch("server.netbox")
def test_custom_object_types_limits_search_scope(mock_netbox):
    """When object_types specified, should only search those types."""
    mock_netbox.get.return_value = []

    result = netbox_search_objects.fn(query="test", object_types=["devices", "sites"])

    # Should only search specified types
    assert mock_netbox.get.call_count == 2
    assert set(result.keys()) == {"devices", "sites"}


# ============================================================================
# Field Projection Tests
# ============================================================================


@patch("server.netbox")
def test_field_projection_applied_to_queries(mock_netbox):
    """When fields specified, should apply to all queries as comma-separated string."""
    mock_netbox.get.return_value = []

    netbox_search_objects.fn(
        query="test", object_types=["devices", "sites"], fields=["id", "name"]
    )

    # All calls should include fields parameter
    for call_args in mock_netbox.get.call_args_list:
        params = call_args[1]["params"]
        assert params["fields"] == "id,name"


# ============================================================================
# Result Structure Tests
# ============================================================================


@patch("server.netbox")
def test_result_structure_with_empty_and_populated_results(mock_netbox):
    """Should return dict with all types as keys, empty lists for no matches."""

    def mock_get_side_effect(endpoint, params):
        if "devices" in endpoint:
            return [{"id": 1, "name": "device01"}]
        return []

    mock_netbox.get.side_effect = mock_get_side_effect

    result = netbox_search_objects.fn(
        query="test", object_types=["devices", "sites", "racks"]
    )

    # All types present
    assert set(result.keys()) == {"devices", "sites", "racks"}
    # Populated results contain data
    assert result["devices"] == [{"id": 1, "name": "device01"}]
    # Empty results are empty lists, not missing keys
    assert result["sites"] == []
    assert result["racks"] == []


# ============================================================================
# Error Resilience Tests
# ============================================================================


@patch("server.netbox")
def test_continues_searching_when_one_type_fails(mock_netbox):
    """If one object type fails, should continue searching others."""

    def mock_get_side_effect(endpoint, params):
        if "devices" in endpoint:
            raise Exception("API error")
        elif "sites" in endpoint:
            return [{"id": 1, "name": "site01"}]
        return []

    mock_netbox.get.side_effect = mock_get_side_effect

    result = netbox_search_objects.fn(query="test", object_types=["devices", "sites"])

    # Should continue despite error
    assert result["sites"] == [{"id": 1, "name": "site01"}]
    # Failed type has empty list
    assert result["devices"] == []


# ============================================================================
# NetBox API Integration Tests
# ============================================================================


@patch("server.netbox")
def test_api_parameters_passed_correctly(mock_netbox):
    """Should pass query, limit, and fields to NetBox API correctly."""
    mock_netbox.get.return_value = []

    netbox_search_objects.fn(
        query="switch01", object_types=["devices"], fields=["id"], limit=25
    )

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    assert params["q"] == "switch01"
    assert params["limit"] == 25
    assert params["fields"] == "id"


@patch("server.netbox")
def test_uses_correct_api_endpoints(mock_netbox):
    """Should use correct API endpoints from NETBOX_OBJECT_TYPES mapping."""
    mock_netbox.get.return_value = []

    netbox_search_objects.fn(query="test", object_types=["devices", "ip-addresses"])

    called_endpoints = [call[0][0] for call in mock_netbox.get.call_args_list]
    assert NETBOX_OBJECT_TYPES["devices"] in called_endpoints
    assert NETBOX_OBJECT_TYPES["ip-addresses"] in called_endpoints
