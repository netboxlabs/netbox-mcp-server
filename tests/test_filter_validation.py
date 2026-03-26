"""Tests for filter validation."""

import pytest

from netbox_mcp_server.server import (
    UNSUPPORTED_COMPONENT_FILTERS,
    validate_filters,
)


class TestGenericFilterValidation:
    """Tests for generic filter syntax validation (no endpoint context)."""

    def test_direct_field_filters_pass(self):
        """Direct field filters should pass validation."""
        validate_filters({"site_id": 1, "name": "router", "status": "active"})

    def test_lookup_suffixes_pass(self):
        """Lookup suffixes should pass validation."""
        validate_filters({"name__ic": "switch", "id__in": [1, 2, 3], "vid__gte": 100})

    def test_special_parameters_ignored(self):
        """Special parameters like limit, offset should be ignored."""
        validate_filters({"limit": 10, "offset": 5, "fields": "id,name", "q": "search"})

    def test_multi_hop_filters_rejected(self):
        """Multi-hop relationship traversal should be rejected."""
        with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
            validate_filters({"device__site_id": 1})

    def test_nested_relationships_rejected(self):
        """Deeply nested relationships should be rejected."""
        with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
            validate_filters({"interface__device__site": "dc1"})

    def test_error_message_helpful(self):
        """Error message should mention the invalid filter and suggest alternatives."""
        with pytest.raises(ValueError, match="device_id"):
            validate_filters({"device__site_id": 1})

    def test_all_valid_suffixes_accepted(self):
        """All documented lookup suffixes should pass validation."""
        for suffix in [
            "n",
            "ic",
            "nic",
            "isw",
            "nisw",
            "iew",
            "niew",
            "ie",
            "nie",
            "empty",
            "regex",
            "iregex",
            "lt",
            "lte",
            "gt",
            "gte",
            "in",
        ]:
            validate_filters({f"name__{suffix}": "test"})

    def test_invalid_suffix_rejected(self):
        """An unrecognized suffix should be rejected as potential multi-hop."""
        with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
            validate_filters({"name__bogus": "test"})


class TestEndpointAwareFilterValidation:
    """Tests for endpoint-specific filter validation (component endpoints)."""

    def test_device_id_filter_allowed_on_interfaces(self):
        """device_id is the correct filter for component endpoints."""
        validate_filters({"device_id": 42}, object_type="dcim.interface")

    def test_device_name_blocked_on_interfaces(self):
        """device__name is silently ignored on interfaces — must be blocked."""
        with pytest.raises(ValueError, match="silently ignores"):
            validate_filters({"device__name": "switch01"}, object_type="dcim.interface")

    def test_device_name_isw_blocked_on_interfaces(self):
        """device__name__isw is silently ignored on interfaces — must be blocked."""
        with pytest.raises(ValueError, match="silently ignores"):
            validate_filters({"device__name__isw": "switch"}, object_type="dcim.interface")

    def test_device_name_ic_blocked_on_interfaces(self):
        """device__name__ic is silently ignored on interfaces — must be blocked."""
        with pytest.raises(ValueError, match="silently ignores"):
            validate_filters({"device__name__ic": "switch"}, object_type="dcim.interface")

    def test_device_name_blocked_on_console_ports(self):
        """device__name is silently ignored on console ports."""
        with pytest.raises(ValueError, match="silently ignores"):
            validate_filters({"device__name": "switch01"}, object_type="dcim.consoleport")

    def test_device_name_blocked_on_power_ports(self):
        """device__name is silently ignored on power ports."""
        with pytest.raises(ValueError, match="silently ignores"):
            validate_filters({"device__name": "pdu01"}, object_type="dcim.powerport")

    def test_device_name_blocked_on_rear_ports(self):
        """device__name is silently ignored on rear ports."""
        with pytest.raises(ValueError, match="silently ignores"):
            validate_filters({"device__name": "patch01"}, object_type="dcim.rearport")

    def test_device_name_blocked_on_device_bays(self):
        """device__name is silently ignored on device bays."""
        with pytest.raises(ValueError, match="silently ignores"):
            validate_filters({"device__name": "chassis01"}, object_type="dcim.devicebay")

    def test_safe_filters_pass_on_component_endpoints(self):
        """Filters that ARE supported on component endpoints should pass."""
        validate_filters({"device_id": 1, "name__ic": "eth"}, object_type="dcim.interface")

    def test_no_object_type_skips_endpoint_check(self):
        """Without object_type, endpoint-specific checks are skipped."""
        # device__name with 2 parts and 'name' not in valid_suffixes -> multi-hop error
        # This is caught by the generic check, not the endpoint check
        with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
            validate_filters({"device__name": "foo"})

    def test_non_component_endpoint_skips_check(self):
        """Non-component endpoints should not trigger endpoint-specific checks."""
        # device__name still fails the generic check (name is not a valid suffix)
        with pytest.raises(ValueError, match="Multi-hop relationship traversal"):
            validate_filters({"device__name": "foo"}, object_type="dcim.device")

    def test_error_suggests_two_step_pattern(self):
        """Error message should explain the two-step device_id pattern."""
        with pytest.raises(ValueError, match="device_id"):
            validate_filters({"device__name__ic": "foo"}, object_type="dcim.interface")

    def test_all_component_endpoints_covered(self):
        """All component endpoints in the blocklist should block device__name."""
        for object_type in UNSUPPORTED_COMPONENT_FILTERS:
            with pytest.raises(ValueError, match="silently ignores"):
                validate_filters({"device__name": "test"}, object_type=object_type)
