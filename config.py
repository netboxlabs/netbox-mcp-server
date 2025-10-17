"""Configuration management for NetBox MCP Server."""

from typing import Literal

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
        """Ensure host/port are set when using HTTP transport."""
        if self.transport == "http":
            if not self.host:
                raise ValueError("HOST is required when TRANSPORT='http'")
            if not self.port:
                raise ValueError("PORT is required when TRANSPORT='http'")
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
