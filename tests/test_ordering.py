"""Tests for ordering parameter validation and behavior."""

from unittest.mock import patch

import pytest
from pydantic import TypeAdapter, ValidationError

from netbox_mcp_server.server import netbox_get_objects


def test_ordering_rejects_invalid_types():
    """Ordering parameter should reject non-string types."""
    ordering_annotation = netbox_get_objects.fn.__annotations__["ordering"]
    adapter = TypeAdapter(ordering_annotation)

    with pytest.raises(ValidationError):
        adapter.validate_python(123)

    with pytest.raises(ValidationError):
        adapter.validate_python({"field": "name"})

    # Lists are no longer accepted (removed for n8n compatibility)
    with pytest.raises(ValidationError):
        adapter.validate_python(["name", "-id"])

@patch("netbox_mcp_server.server.netbox")
def test_ordering_default_omits_parameter(mock_netbox):
    """When ordering is not specified (default empty string), should not include ordering in API params."""
    mock_netbox.get.return_value = {"count": 0, "results": [], "next": None, "previous": None}

    netbox_get_objects.fn(object_type="dcim.site", filters={})

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # ordering should not be in params when using default empty string
    assert "ordering" not in params


@patch("netbox_mcp_server.server.netbox")
def test_ordering_empty_string_omits_parameter(mock_netbox):
    """When ordering='', should not include ordering in API params."""
    mock_netbox.get.return_value = {"count": 0, "results": [], "next": None, "previous": None}

    netbox_get_objects.fn(object_type="dcim.site", filters={}, ordering="")

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # ordering should not be in params when empty string
    assert "ordering" not in params


@patch("netbox_mcp_server.server.netbox")
def test_ordering_single_field_ascending(mock_netbox):
    """When ordering='name', should pass 'name' to API params."""
    mock_netbox.get.return_value = {"count": 0, "results": [], "next": None, "previous": None}

    netbox_get_objects.fn(object_type="dcim.site", filters={}, ordering="name")

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    assert params["ordering"] == "name"


@patch("netbox_mcp_server.server.netbox")
def test_ordering_single_field_descending(mock_netbox):
    """When ordering='-id', should pass '-id' to API params."""
    mock_netbox.get.return_value = {"count": 0, "results": [], "next": None, "previous": None}

    netbox_get_objects.fn(object_type="dcim.site", filters={}, ordering="-id")

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    assert params["ordering"] == "-id"


@patch("netbox_mcp_server.server.netbox")
def test_ordering_multiple_fields_comma_separated(mock_netbox):
    """When ordering='facility,-name', should pass comma-separated string to API."""
    mock_netbox.get.return_value = {"count": 0, "results": [], "next": None, "previous": None}

    netbox_get_objects.fn(object_type="dcim.site", filters={}, ordering="facility,-name")

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # Comma-separated string should be passed as-is
    assert params["ordering"] == "facility,-name"


@patch("netbox_mcp_server.server.netbox")
def test_ordering_whitespace_only_omits_parameter(mock_netbox):
    """When ordering contains only whitespace, should not include ordering in API params."""
    mock_netbox.get.return_value = {"count": 0, "results": [], "next": None, "previous": None}

    netbox_get_objects.fn(object_type="dcim.site", filters={}, ordering="   ")

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # Whitespace-only string should be omitted
    assert "ordering" not in params
