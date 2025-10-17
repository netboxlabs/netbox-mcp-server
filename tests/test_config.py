"""Tests for configuration management."""

import pytest
from pydantic import ValidationError

from config import Settings


def test_settings_requires_netbox_url():
    """Test that Settings requires NETBOX_URL."""

    with pytest.raises(ValidationError, match="netbox_url"):
        Settings(netbox_token="test-token")


def test_settings_requires_netbox_token():
    """Test that Settings requires NETBOX_TOKEN."""

    with pytest.raises(ValidationError, match="netbox_token"):
        Settings(netbox_url="https://netbox.example.com/")


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
