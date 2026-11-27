"""Tests for the netbox_get_available_prefixes tool."""

from unittest.mock import patch

import pytest

from netbox_mcp_server.server import netbox_get_available_prefixes


def _block(prefix, family=4, vrf=None):
    return {"family": family, "prefix": prefix, "vrf": vrf}


@patch("netbox_mcp_server.server.netbox")
def test_returns_blocks_as_reported_truncated_to_limit(mock_netbox):
    mock_netbox.get.return_value = [_block("10.0.4.0/22"), _block("10.0.16.0/20")]

    result = netbox_get_available_prefixes(parent_id=42, limit=1)

    assert result == [_block("10.0.4.0/22")]
    mock_netbox.get.assert_called_once()
    assert mock_netbox.get.call_args.args[0] == "ipam/prefixes/42/available-prefixes"


@patch("netbox_mcp_server.server.netbox")
def test_prefix_length_subdivides_blocks(mock_netbox):
    mock_netbox.get.return_value = [_block("10.0.4.0/22")]

    result = netbox_get_available_prefixes(parent_id=42, prefix_length=26, limit=3)

    assert result == [
        _block("10.0.4.0/26"),
        _block("10.0.4.64/26"),
        _block("10.0.4.128/26"),
    ]


@patch("netbox_mcp_server.server.netbox")
def test_prefix_length_drops_small_blocks_and_continues(mock_netbox):
    mock_netbox.get.return_value = [_block("10.0.0.0/28"), _block("10.0.1.0/25")]

    result = netbox_get_available_prefixes(parent_id=1, prefix_length=26, limit=5)

    assert result == [_block("10.0.1.0/26"), _block("10.0.1.64/26")]


@patch("netbox_mcp_server.server.netbox")
def test_prefix_length_spans_multiple_blocks_up_to_limit(mock_netbox):
    mock_netbox.get.return_value = [_block("10.0.0.0/25"), _block("10.0.1.0/24")]

    result = netbox_get_available_prefixes(parent_id=1, prefix_length=25, limit=3)

    assert [r["prefix"] for r in result] == ["10.0.0.0/25", "10.0.1.0/25", "10.0.1.128/25"]


@patch("netbox_mcp_server.server.netbox")
def test_ipv6_blocks_and_oversized_mask(mock_netbox):
    mock_netbox.get.return_value = [_block("2001:db8::/64", family=6)]

    result = netbox_get_available_prefixes(parent_id=1, prefix_length=66, limit=2)
    assert [r["prefix"] for r in result] == ["2001:db8::/66", "2001:db8:0:0:4000::/66"]
    assert all(r["family"] == 6 for r in result)

    mock_netbox.get.return_value = [_block("10.0.0.0/24")]
    assert netbox_get_available_prefixes(parent_id=1, prefix_length=33) == []


@patch("netbox_mcp_server.server.netbox")
def test_empty_result_is_valid(mock_netbox):
    mock_netbox.get.return_value = []

    assert netbox_get_available_prefixes(parent_id=1, prefix_length=26) == []


@patch("netbox_mcp_server.server.netbox")
def test_vrf_assertion_passes_without_extra_request_when_omitted(mock_netbox):
    mock_netbox.get.return_value = []

    netbox_get_available_prefixes(parent_id=1)

    assert mock_netbox.get.call_count == 1


@patch("netbox_mcp_server.server.netbox")
def test_vrf_assertion_matches(mock_netbox):
    mock_netbox.get.side_effect = [
        {"id": 1, "prefix": "10.0.0.0/16", "vrf": {"id": 5, "name": "cust"}},
        [_block("10.0.0.0/16", vrf={"id": 5})],
    ]

    result = netbox_get_available_prefixes(parent_id=1, vrf_id=5)

    assert len(result) == 1
    first = mock_netbox.get.call_args_list[0]
    assert first.kwargs["id"] == 1
    assert first.kwargs["params"] == {"fields": "id,prefix,vrf"}


@patch("netbox_mcp_server.server.netbox")
def test_vrf_assertion_mismatch_names_actual_vrf(mock_netbox):
    mock_netbox.get.return_value = {"id": 1, "prefix": "10.0.0.0/16", "vrf": {"id": 9}}

    with pytest.raises(ValueError, match="VRF 9"):
        netbox_get_available_prefixes(parent_id=1, vrf_id=5)
    assert mock_netbox.get.call_count == 1


@patch("netbox_mcp_server.server.netbox")
def test_vrf_global_assertion_both_directions(mock_netbox):
    mock_netbox.get.side_effect = [
        {"id": 1, "prefix": "10.0.0.0/16", "vrf": None},
        [],
    ]
    assert netbox_get_available_prefixes(parent_id=1, vrf_id="global") == []

    mock_netbox.get.side_effect = [{"id": 1, "prefix": "10.0.0.0/16", "vrf": {"id": 9}}]
    with pytest.raises(ValueError, match="VRF 9"):
        netbox_get_available_prefixes(parent_id=1, vrf_id="global")

    mock_netbox.get.side_effect = [{"id": 1, "prefix": "10.0.0.0/16", "vrf": None}]
    with pytest.raises(ValueError, match="global table"):
        netbox_get_available_prefixes(parent_id=1, vrf_id=5)
