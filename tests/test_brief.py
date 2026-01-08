"""Tests for brief parameter validation and behavior."""

from unittest.mock import patch

from netbox_mcp_server.server import netbox_get_object_by_id, netbox_get_objects


@patch("netbox_mcp_server.server.netbox")
def test_brief_false_omits_parameter_get_objects(mock_netbox):
    """When brief=False (default), should not include brief in API params for netbox_get_objects."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="dcim.site", filters={}, brief=False)

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # brief should not be in params when False
    assert "brief" not in params


@patch("netbox_mcp_server.server.netbox")
def test_brief_default_omits_parameter_get_objects(mock_netbox):
    """When brief not specified (uses default False), should not include brief in API params."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="dcim.site", filters={})

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # brief should not be in params when using default
    assert "brief" not in params


@patch("netbox_mcp_server.server.netbox")
def test_brief_true_includes_parameter_get_objects(mock_netbox):
    """When brief=True, should pass 'brief': '1' to API params for netbox_get_objects."""
    mock_netbox.get.return_value = {
        "count": 0,
        "results": [],
        "next": None,
        "previous": None,
    }

    netbox_get_objects.fn(object_type="dcim.site", filters={}, brief=True)

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    assert params["brief"] == "1"


@patch("netbox_mcp_server.server.netbox")
def test_brief_false_omits_parameter_get_by_id(mock_netbox):
    """When brief=False (default), should not include brief in API params for netbox_get_object_by_id."""
    mock_netbox.get.return_value = {"id": 1, "name": "Test Site"}

    netbox_get_object_by_id.fn(object_type="dcim.site", object_id=1, brief=False)

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # brief should not be in params when False
    assert "brief" not in params


@patch("netbox_mcp_server.server.netbox")
def test_brief_default_omits_parameter_get_by_id(mock_netbox):
    """When brief not specified (uses default False), should not include brief in API params."""
    mock_netbox.get.return_value = {"id": 1, "name": "Test Site"}

    netbox_get_object_by_id.fn(object_type="dcim.site", object_id=1)

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    # brief should not be in params when using default
    assert "brief" not in params


@patch("netbox_mcp_server.server.netbox")
def test_brief_true_includes_parameter_get_by_id(mock_netbox):
    """When brief=True, should pass 'brief': '1' to API params for netbox_get_object_by_id."""
    mock_netbox.get.return_value = {
        "id": 1,
        "url": "http://example.com/api/dcim/sites/1/",
    }

    netbox_get_object_by_id.fn(object_type="dcim.site", object_id=1, brief=True)

    call_args = mock_netbox.get.call_args
    params = call_args[1]["params"]

    assert params["brief"] == "1"
