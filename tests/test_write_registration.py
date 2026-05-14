"""Tests that write tools are only registered when explicitly opted in.

This is the safety contract: if ENABLE_WRITES is unset (default), the three
write tools must not appear in tools/list. The gating boundary is the
_register_write_tools() helper — main() only calls it when
settings.enable_writes is True.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP

from netbox_mcp_server import server as server_module
from netbox_mcp_server.server import _register_write_tools

WRITE_TOOL_NAMES = {
    "netbox_create_object",
    "netbox_update_object",
    "netbox_delete_object",
}


def _tool_names(mcp_instance: FastMCP) -> set[str]:
    tools = asyncio.run(mcp_instance.list_tools())
    return {t.name for t in tools}


def test_writes_not_registered_when_helper_not_called():
    """When _register_write_tools is not called, write tools are absent."""
    mcp = FastMCP("test")
    assert _tool_names(mcp) & WRITE_TOOL_NAMES == set()


def test_module_level_mcp_has_no_write_tools_at_import():
    """Regression guard: nobody slapped @mcp.tool on the write functions.

    The module-level FastMCP instance must not carry write tools at import
    time — registration only happens in main() when settings.enable_writes
    is True. If this fails, someone added a decorator that defeats the gate.
    """
    assert _tool_names(server_module.mcp) & WRITE_TOOL_NAMES == set()


def test_writes_registered_when_helper_called():
    """When _register_write_tools is called, all three write tools are present."""
    mcp = FastMCP("test")
    _register_write_tools(mcp)
    assert WRITE_TOOL_NAMES.issubset(_tool_names(mcp))


@pytest.mark.parametrize("tool_name", sorted(WRITE_TOOL_NAMES))
def test_each_write_tool_registered_individually(tool_name):
    """Each write tool is reachable via get_tool after registration."""
    mcp = FastMCP("test")
    _register_write_tools(mcp)
    tool = asyncio.run(mcp.get_tool(tool_name))
    assert tool is not None
    assert tool.name == tool_name


# ============================================================================
# main() wiring: enable_writes setting controls registration
# ============================================================================


def _stub_main_deps(monkeypatch, *, enable_writes: bool):
    """Patch out main()'s side effects so we can assert only the gating logic."""
    settings = MagicMock()
    settings.log_level = "INFO"
    settings.verify_ssl = True
    settings.transport = "stdio"
    settings.host = "127.0.0.1"
    settings.port = 8000
    settings.enable_plugin_discovery = False
    settings.enable_writes = enable_writes
    settings.netbox_url = "https://nb.example.com/"
    settings.netbox_token = MagicMock()
    settings.netbox_token.get_secret_value.return_value = "tok"
    settings.get_effective_config_summary.return_value = {}

    monkeypatch.setattr(server_module, "parse_cli_args", lambda: {})
    monkeypatch.setattr(server_module, "Settings", lambda **_: settings)
    monkeypatch.setattr(server_module, "configure_logging", lambda _: None)
    monkeypatch.setattr(server_module, "NetBoxRestClient", lambda **_: MagicMock())

    # mcp.run would block; replace with no-op.
    monkeypatch.setattr(server_module.mcp, "run", lambda **_: None)


def test_main_does_not_register_writes_when_setting_false(monkeypatch):
    _stub_main_deps(monkeypatch, enable_writes=False)
    with patch.object(server_module, "_register_write_tools") as mock_reg:
        server_module.main()
        mock_reg.assert_not_called()


def test_main_registers_writes_when_setting_true(monkeypatch):
    _stub_main_deps(monkeypatch, enable_writes=True)
    with patch.object(server_module, "_register_write_tools") as mock_reg:
        server_module.main()
        mock_reg.assert_called_once_with(server_module.mcp)
