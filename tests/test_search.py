"""Tests for global search functionality (netbox_search_objects tool)."""

from unittest.mock import patch

import pytest
from pydantic import TypeAdapter, ValidationError

from netbox_mcp_server.netbox_types import NETBOX_OBJECT_TYPES
from netbox_mcp_server.server import netbox_search_objects

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


@patch("netbox_mcp_server.server.netbox")
def test_searches_default_types_when_none_specified(mock_netbox):
    """When object_types=None, should search 8 default common types."""
    mock_netbox.get.return_value = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }

    result = netbox_search_objects.fn(query="test")

    # Should search 8 default types
    assert mock_netbox.get.call_count == 8
    assert isinstance(result, dict)
    assert len(result) == 8


@patch("netbox_mcp_server.server.netbox")
def test_custom_object_types_limits_search_scope(mock_netbox):
    """When object_types specified, should only search those types."""
    mock_netbox.get.return_value = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }

    result = netbox_search_objects.fn(
        query="test", object_types=["dcim.device", "dcim.site"]
    )

    # Should only search specified types
    assert mock_netbox.get.call_count == 2
    assert set(result.keys()) == {"dcim.device", "dcim.site"}


# ============================================================================
# Field Projection Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_field_projection_applied_to_queries(mock_netbox):
    """When fields specified, should apply to all queries as comma-separated string."""
    mock_netbox.get.return_value = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }

    netbox_search_objects.fn(
        query="test", object_types=["dcim.device", "dcim.site"], fields=["id", "name"]
    )

    # All calls should include fields parameter
    for call_args in mock_netbox.get.call_args_list:
        params = call_args[1]["params"]
        assert params["fields"] == "id,name"


# ============================================================================
# Result Structure Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_result_structure_with_empty_and_populated_results(mock_netbox):
    """Should return dict with all types as keys, empty lists for no matches."""

    def mock_get_side_effect(endpoint, params):
        if "devices" in endpoint:
            return {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [{"id": 1, "name": "device01"}],
            }
        return {"count": 0, "next": None, "previous": None, "results": []}

    mock_netbox.get.side_effect = mock_get_side_effect

    result = netbox_search_objects.fn(
        query="test", object_types=["dcim.device", "dcim.site", "dcim.rack"]
    )

    # All types present
    assert set(result.keys()) == {"dcim.device", "dcim.site", "dcim.rack"}
    # Populated results contain data
    assert result["dcim.device"] == [{"id": 1, "name": "device01"}]
    # Empty results are empty lists, not missing keys
    assert result["dcim.site"] == []
    assert result["dcim.rack"] == []


# ============================================================================
# Error Resilience Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_continues_searching_when_one_type_fails(mock_netbox):
    """If one object type fails, should continue searching others."""

    def mock_get_side_effect(endpoint, params):
        if "devices" in endpoint:
            raise Exception("API error")
        elif "sites" in endpoint:
            return {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [{"id": 1, "name": "site01"}],
            }
        return {"count": 0, "next": None, "previous": None, "results": []}

    mock_netbox.get.side_effect = mock_get_side_effect

    result = netbox_search_objects.fn(
        query="test", object_types=["dcim.device", "dcim.site"]
    )

    # Should continue despite error
    assert result["dcim.site"] == [{"id": 1, "name": "site01"}]
    # Failed type has empty list
    assert result["dcim.device"] == []


# ============================================================================
# NetBox API Integration Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_api_parameters_passed_correctly(mock_netbox):
    """Should pass query, limit, and fields to NetBox API correctly."""
    mock_netbox.get.return_value = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }

    netbox_search_objects.fn(
        query="switch01", object_types=["dcim.device"], fields=["id"], limit=25
    )

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    assert params["q"] == "switch01"
    assert params["limit"] == 25
    assert params["fields"] == "id"


@patch("netbox_mcp_server.server.netbox")
def test_uses_correct_api_endpoints(mock_netbox):
    """Should use correct API endpoints from NETBOX_OBJECT_TYPES mapping."""
    mock_netbox.get.return_value = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }

    netbox_search_objects.fn(
        query="test", object_types=["dcim.device", "ipam.ipaddress"]
    )

    called_endpoints = [call[0][0] for call in mock_netbox.get.call_args_list]
    assert NETBOX_OBJECT_TYPES["dcim.device"]["endpoint"] in called_endpoints
    assert NETBOX_OBJECT_TYPES["ipam.ipaddress"]["endpoint"] in called_endpoints


# ============================================================================
# Paginated Response Handling Tests
# ============================================================================


@patch("netbox_mcp_server.server.netbox")
def test_extracts_results_from_paginated_response(mock_netbox):
    """Should extract 'results' array from NetBox paginated response structure.

    NetBox API returns paginated responses with structure:
    {
        "count": <total>,
        "next": <url or null>,
        "previous": <url or null>,
        "results": [<objects>]
    }

    The tool should return just the results arrays, not the full response.
    """
    # Mock realistic paginated response from NetBox API
    mock_netbox.get.return_value = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {"id": 1, "name": "device01"},
            {"id": 2, "name": "device02"},
        ],
    }

    result = netbox_search_objects.fn(query="test", object_types=["dcim.device"])

    # Should return dict with object type as key
    assert "dcim.device" in result
    # Value should be a list (array), not a dict
    assert isinstance(result["dcim.device"], list)
    # Should contain just the results, not the paginated response wrapper
    assert result["dcim.device"] == [
        {"id": 1, "name": "device01"},
        {"id": 2, "name": "device02"},
    ]
