"""Tests for filter validation."""

import pytest

from netbox_mcp_server.server import validate_filters


def test_direct_field_filters_pass():
    """Direct field filters should pass validation."""
    validate_filters({"site_id": 1, "name": "router", "status": "active"})


def test_lookup_suffixes_pass():
    """Lookup suffixes should pass validation."""
    validate_filters({"name__ic": "switch", "id__in": [1, 2, 3], "vid__gte": 100})


def test_special_parameters_ignored():
    """Special parameters like limit, offset should be ignored."""
    validate_filters({"limit": 10, "offset": 5, "fields": "id,name", "q": "search"})


def test_multi_hop_filters_rejected():
    """Multi-hop relationship traversal should be rejected."""
    with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
        validate_filters({"device__site_id": 1})


def test_nested_relationships_rejected():
    """Deeply nested relationships should be rejected."""
    with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
        validate_filters({"interface__device__site": "dc1"})


def test_error_message_helpful():
    """Error message should mention the invalid filter and suggest alternatives."""
    with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
        validate_filters({"device__site_id": 1})
