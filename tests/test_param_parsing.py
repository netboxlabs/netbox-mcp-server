"""Tests for parameter parsing helper functions."""

import pytest

from netbox_mcp_server.server import _parse_filters, _parse_list_param


class TestParseFilters:
    """Tests for _parse_filters function."""

    def test_returns_dict_unchanged(self):
        """Should return dict unchanged."""
        filters = {"status": "active", "site_id": 1}
        assert _parse_filters(filters) == filters

    def test_parses_json_string(self):
        """Should parse valid JSON string."""
        assert _parse_filters('{"status": "active"}') == {"status": "active"}

    def test_strips_whitespace_from_json(self):
        """Should strip whitespace from JSON string before parsing."""
        assert _parse_filters('  {"status": "active"}  ') == {"status": "active"}

    @pytest.mark.parametrize(
        "value",
        [None, "", "   ", "undefined", "UNDEFINED", "null", "NULL", "none", "None"],
    )
    def test_returns_empty_dict_for_empty_values(self, value):
        """Should return empty dict for None, empty string, or n8n-style nulls."""
        assert _parse_filters(value) == {}

    def test_raises_on_invalid_json(self):
        """Should raise ValueError for invalid JSON."""
        with pytest.raises(ValueError, match="Invalid filters JSON"):
            _parse_filters("not valid json")


class TestParseListParam:
    """Tests for _parse_list_param function."""

    def test_returns_list_unchanged(self):
        """Should return list unchanged."""
        value = ["id", "name", "status"]
        assert _parse_list_param(value) == value

    def test_parses_comma_separated_string(self):
        """Should parse comma-separated string into list."""
        assert _parse_list_param("id,name,status") == ["id", "name", "status"]

    def test_strips_whitespace_around_items(self):
        """Should strip whitespace around items."""
        assert _parse_list_param("id, name, status") == ["id", "name", "status"]

    def test_filters_empty_items(self):
        """Should filter out empty items from comma-separated string."""
        assert _parse_list_param("id,,name,") == ["id", "name"]

    def test_handles_single_item(self):
        """Should handle single item without comma."""
        assert _parse_list_param("id") == ["id"]

    @pytest.mark.parametrize(
        "value",
        [None, "", "   ", "undefined", "null"],
    )
    def test_returns_empty_list_for_empty_values(self, value):
        """Should return empty list for None, empty string, or n8n-style nulls."""
        assert _parse_list_param(value) == []
