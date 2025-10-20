"""Tests for configuration management."""

import logging
import sys
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from config import Settings, configure_logging
from server import parse_cli_args


def test_settings_requires_netbox_url():
    """Test that Settings requires NETBOX_URL."""
    # Isolate from .env file by patching model_config
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValidationError, match="netbox_url"):
            Settings(netbox_token="test-token", _env_file=None)


def test_settings_requires_netbox_token():
    """Test that Settings requires NETBOX_TOKEN."""
    # Isolate from .env file by patching model_config
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValidationError, match="netbox_token"):
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

    settings = Settings(
        netbox_url="https://netbox.example.com/", netbox_token="super-secret-token"
    )

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


# ===== Logging Configuration Tests =====


def test_configure_logging_suppresses_http_clients():
    """Test that HTTP client loggers are suppressed at INFO level."""

    configure_logging("INFO")

    urllib3_logger = logging.getLogger("urllib3")
    httpx_logger = logging.getLogger("httpx")
    requests_logger = logging.getLogger("requests")

    assert urllib3_logger.level == logging.WARNING
    assert httpx_logger.level == logging.WARNING
    assert requests_logger.level == logging.WARNING


def test_configure_logging_shows_http_clients_at_debug():
    """Test that HTTP client loggers are shown at DEBUG level."""
    configure_logging("DEBUG")

    root_logger = logging.getLogger()
    urllib3_logger = logging.getLogger("urllib3")
    httpx_logger = logging.getLogger("httpx")
    requests_logger = logging.getLogger("requests")

    assert root_logger.level == logging.DEBUG
    assert urllib3_logger.level == logging.DEBUG
    assert httpx_logger.level == logging.DEBUG
    assert requests_logger.level == logging.DEBUG
