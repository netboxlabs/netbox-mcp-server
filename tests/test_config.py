"""Tests for configuration management."""

import logging
import sys
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from netbox_mcp_server.config import Settings, configure_logging
from netbox_mcp_server.server import parse_cli_args


def test_settings_requires_netbox_url():
    """Test that Settings requires NETBOX_URL."""
    # Isolate from .env file by patching model_config
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(ValidationError, match="netbox_url"),
    ):
        Settings(netbox_token="test-token", _env_file=None)


def test_settings_requires_netbox_token():
    """Test that Settings requires NETBOX_TOKEN."""
    # Isolate from .env file by patching model_config
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(ValidationError, match="netbox_token"),
    ):
        Settings(netbox_url="https://netbox.example.com/", _env_file=None)


def test_settings_validates_url_format():
    """Test that invalid URLs are rejected."""

    with pytest.raises(ValidationError, match="Input should be a valid URL"):
        Settings(netbox_url="not-a-valid-url", netbox_token="test-token")


def test_settings_validates_port_range():
    """Test that port must be in valid range."""

    with pytest.raises(ValidationError, match="port"):
        Settings(
            netbox_url="https://netbox.example.com/",
            netbox_token="test-token",
            port=99999,
        )


def test_settings_masks_secrets_in_summary():
    """Test that get_effective_config_summary masks secrets."""

    settings = Settings(netbox_url="https://netbox.example.com/", netbox_token="super-secret-token")

    summary = settings.get_effective_config_summary()

    assert summary["netbox_token"] == "***REDACTED***"
    assert "super-secret-token" not in str(summary)


# ===== CLI Argument Parsing Tests =====


def test_parse_cli_args_multiple():
    """Test that multiple arguments are captured."""

    original_argv = sys.argv
    try:
        sys.argv = [
            "server.py",
            "--netbox-url",
            "https://test.example.com/",
            "--transport",
            "http",
            "--port",
            "9000",
            "--log-level",
            "DEBUG",
            "--no-verify-ssl",
        ]
        result = parse_cli_args()
        assert result["netbox_url"] == "https://test.example.com/"
        assert result["transport"] == "http"
        assert result["port"] == 9000
        assert result["log_level"] == "DEBUG"
        assert result["verify_ssl"] is False
    finally:
        sys.argv = original_argv


# ===== n8n Compatibility Flag Tests =====


def test_settings_n8n_compat_defaults_false():
    """Default value of n8n_compat is False (strict types are default)."""
    settings = Settings(
        netbox_url="https://netbox.example.com/",
        netbox_token="test-token",
        _env_file=None,
    )
    assert settings.n8n_compat is False


def test_settings_n8n_compat_from_env():
    """NETBOX_MCP_N8N_COMPAT=true env var enables compat mode."""
    with patch.dict(
        "os.environ",
        {
            "NETBOX_URL": "https://netbox.example.com/",
            "NETBOX_TOKEN": "test-token",
            "NETBOX_MCP_N8N_COMPAT": "true",
        },
        clear=True,
    ):
        settings = Settings(_env_file=None)
        assert settings.n8n_compat is True


def test_settings_n8n_compat_not_set_by_bare_env_var():
    """Bare N8N_COMPAT env var is NOT recognised — only the prefixed form.

    We intentionally do not accept a bare-name alias to avoid namespace
    collisions in multi-service deploys.
    """
    with patch.dict(
        "os.environ",
        {
            "NETBOX_URL": "https://netbox.example.com/",
            "NETBOX_TOKEN": "test-token",
            "N8N_COMPAT": "true",
        },
        clear=True,
    ):
        settings = Settings(_env_file=None)
        assert settings.n8n_compat is False


def test_settings_n8n_compat_appears_in_summary():
    """get_effective_config_summary includes n8n_compat so it's logged at startup."""
    settings = Settings(
        netbox_url="https://netbox.example.com/",
        netbox_token="test-token",
        n8n_compat=True,
    )
    assert settings.get_effective_config_summary()["n8n_compat"] is True


def test_parse_cli_args_n8n_compat_flag():
    """--n8n-compat CLI flag is captured in the overlay."""
    original_argv = sys.argv
    try:
        sys.argv = ["server.py", "--n8n-compat"]
        result = parse_cli_args()
        assert result["n8n_compat"] is True
    finally:
        sys.argv = original_argv


def test_parse_cli_args_n8n_compat_default_absent():
    """Without --n8n-compat, the key is absent from the overlay."""
    original_argv = sys.argv
    try:
        sys.argv = ["server.py"]
        result = parse_cli_args()
        assert "n8n_compat" not in result
    finally:
        sys.argv = original_argv


# ===== Logging Configuration Tests =====


def test_configure_logging_suppresses_http_clients():
    """Test that HTTP client loggers are suppressed at INFO level."""

    configure_logging("INFO")

    urllib3_logger = logging.getLogger("urllib3")
    httpx_logger = logging.getLogger("httpx")

    assert urllib3_logger.level == logging.WARNING
    assert httpx_logger.level == logging.WARNING


def test_configure_logging_shows_http_clients_at_debug():
    """Test that HTTP client loggers are shown at DEBUG level."""
    configure_logging("DEBUG")

    root_logger = logging.getLogger()
    urllib3_logger = logging.getLogger("urllib3")
    httpx_logger = logging.getLogger("httpx")

    assert root_logger.level == logging.DEBUG
    assert urllib3_logger.level == logging.DEBUG
    assert httpx_logger.level == logging.DEBUG
