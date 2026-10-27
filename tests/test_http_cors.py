"""Exercise the HTTP transport's actual CORS and session lifecycle."""

from collections.abc import Iterator

import pytest
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.testclient import TestClient
from starlette.types import ASGIApp

from netbox_mcp_server import server
from netbox_mcp_server.config import Settings

ORIGIN = "https://client.example"
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "cors-test", "version": "1.0"},
    },
}


@pytest.fixture
def http_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Use main's configured middleware with a real FastMCP HTTP app."""
    mcp = FastMCP(name="cors-test")
    apps: list[ASGIApp] = []

    def capture_run(*, transport: str, host: str, port: int, middleware: list[Middleware]) -> None:
        assert transport == "http"
        apps.append(mcp.http_app(middleware=middleware))

    settings = Settings(
        _env_file=None,
        netbox_url="http://127.0.0.1:9",
        netbox_token="test-token",
        transport="http",
        cors_origins=[ORIGIN],
        mcp_auth_token=None,
        enable_plugin_discovery=False,
    )
    monkeypatch.setattr(server, "mcp", mcp)
    monkeypatch.setattr(mcp, "run", capture_run)
    monkeypatch.setattr(server, "parse_cli_args", lambda: {})
    monkeypatch.setattr(server, "Settings", lambda **kwargs: settings)
    server.main()
    try:
        with TestClient(apps[0]) as client:
            yield client
    finally:
        server.netbox.session.close()


@pytest.mark.parametrize("method", ["GET", "POST", "DELETE"])
def test_allowed_origin_can_preflight_mcp_methods(http_client: TestClient, method: str) -> None:
    response = http_client.options(
        "/mcp/",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "mcp-session-id,mcp-protocol-version",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_unconfigured_origin_cannot_preflight_delete(http_client: TestClient) -> None:
    response = http_client.options(
        "/mcp/",
        headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "DELETE"},
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_delete_ends_the_mcp_session(http_client: TestClient) -> None:
    response = http_client.post(
        "/mcp/",
        json=INITIALIZE,
        headers={"Origin": ORIGIN, "Accept": "application/json, text/event-stream"},
    )
    assert response.status_code == 200
    session_id = response.headers["mcp-session-id"]
    headers = {"Origin": ORIGIN, "mcp-session-id": session_id, "mcp-protocol-version": "2024-11-05"}
    preflight = http_client.options(
        "/mcp/",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "mcp-session-id",
        },
    )
    assert preflight.status_code == 200
    ended = http_client.delete("/mcp/", headers=headers)
    assert ended.status_code == 200
    assert ended.headers["access-control-allow-origin"] == ORIGIN
