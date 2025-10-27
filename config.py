"""Configuration management for NetBox MCP Server."""

import logging
import logging.config
from typing import Any, Literal

from pydantic import AnyUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration for NetBox MCP Server.

    Configuration precedence: CLI > Environment > .env file > Defaults

    Environment variables should match field names (e.g., NETBOX_URL, TRANSPORT).
    """

    # ===== Core NetBox Settings =====
    netbox_url: AnyUrl
    """Base URL of the NetBox instance (e.g., https://netbox.example.com/)"""

    netbox_token: SecretStr
    """API token for NetBox authentication (treated as secret)"""

    # ===== Transport Settings =====
    transport: Literal["stdio", "http"] = "stdio"
    """MCP transport protocol to use (stdio for Claude Desktop, http for web clients)"""

    host: str = "127.0.0.1"
    """Host address to bind HTTP server (only used when transport='http')"""

    port: int = 8000
    """Port to bind HTTP server (only used when transport='http')"""

    # ===== Security Settings =====
    verify_ssl: bool = True
    """Whether to verify SSL certificates when connecting to NetBox"""

    # ===== Observability Settings =====
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    """Logging verbosity level"""

    # ===== Pydantic Configuration =====
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",  # No prefix, use field names directly
        extra="ignore",  # Ignore unknown environment variables
        case_sensitive=False,  # Environment variables are case-insensitive
    )

    # ===== Validators =====

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Ensure port is in valid range."""
        if not (0 < v < 65536):
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v

    @field_validator("netbox_url")
    @classmethod
    def validate_netbox_url(cls, v: AnyUrl) -> AnyUrl:
        """Ensure NetBox URL has a scheme and host."""
        if not v.scheme or not v.host:
            raise ValueError(
                "NETBOX_URL must include scheme and host (e.g., https://netbox.example.com/)"
            )
        return v

    @model_validator(mode="after")
    def validate_http_transport_requirements(self) -> "Settings":
        """No additional validation needed for HTTP transport; defaults are appropriate."""
        return self

    def get_effective_config_summary(self) -> dict:
        """
        Return a non-secret summary of effective configuration for logging.

        Returns:
            Dictionary with configuration values (secrets masked)
        """
        return {
            "netbox_url": str(self.netbox_url),
            "netbox_token": "***REDACTED***",
            "transport": self.transport,
            "host": self.host if self.transport == "http" else "N/A",
            "port": self.port if self.transport == "http" else "N/A",
            "verify_ssl": self.verify_ssl,
            "log_level": self.log_level,
        }


def configure_logging(
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
) -> None:
    """
    Configure structured logging using dictConfig.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            # Suppress noisy HTTP client logs unless DEBUG
            "urllib3": {
                "level": "WARNING" if log_level != "DEBUG" else "DEBUG",
            },
            "httpx": {
                "level": "WARNING" if log_level != "DEBUG" else "DEBUG",
            },
            "requests": {
                "level": "WARNING" if log_level != "DEBUG" else "DEBUG",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(config)
