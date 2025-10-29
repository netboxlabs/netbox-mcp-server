"""Tests for pagination parameter validation."""

import inspect

import pytest
from pydantic import TypeAdapter, ValidationError

from netbox_mcp_server.server import netbox_get_objects


def test_limit_validation_rejects_values_over_100():
    """Limit > 100 should be rejected by Pydantic validation."""
    # Get the actual annotation from the underlying function
    limit_annotation = netbox_get_objects.fn.__annotations__["limit"]
    adapter = TypeAdapter(limit_annotation)

    with pytest.raises(ValidationError):
        adapter.validate_python(150)


def test_limit_validation_rejects_zero_and_negative():
    """Limit <= 0 should be rejected by Pydantic validation."""
    limit_annotation = netbox_get_objects.fn.__annotations__["limit"]
    adapter = TypeAdapter(limit_annotation)

    with pytest.raises(ValidationError):
        adapter.validate_python(0)

    with pytest.raises(ValidationError):
        adapter.validate_python(-5)


def test_limit_validation_accepts_valid_range():
    """Limit between 1 and 100 should be accepted."""
    limit_annotation = netbox_get_objects.fn.__annotations__["limit"]
    adapter = TypeAdapter(limit_annotation)

    # Should not raise
    adapter.validate_python(1)
    adapter.validate_python(5)
    adapter.validate_python(50)
    adapter.validate_python(100)


def test_offset_validation_rejects_negative():
    """Negative offset should be rejected by Pydantic validation."""
    offset_annotation = netbox_get_objects.fn.__annotations__["offset"]
    adapter = TypeAdapter(offset_annotation)

    with pytest.raises(ValidationError):
        adapter.validate_python(-1)


def test_offset_validation_accepts_zero_and_positive():
    """Offset >= 0 should be accepted."""
    offset_annotation = netbox_get_objects.fn.__annotations__["offset"]
    adapter = TypeAdapter(offset_annotation)

    # Should not raise
    adapter.validate_python(0)
    adapter.validate_python(5)
    adapter.validate_python(100)


def test_netbox_get_objects_has_pagination_parameters():
    """netbox_get_objects should have limit and offset parameters with proper defaults."""
    get_objects_sig = inspect.signature(netbox_get_objects.fn)

    # Check netbox_get_objects has the parameters
    assert "limit" in get_objects_sig.parameters
    assert "offset" in get_objects_sig.parameters
    assert get_objects_sig.parameters["limit"].default == 5
    assert get_objects_sig.parameters["offset"].default == 0
