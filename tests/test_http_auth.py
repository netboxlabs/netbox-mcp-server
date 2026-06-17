"""Tests for optional Bearer token authentication on the HTTP transport.

These verify the auth gate built by ``build_http_auth``: when a token is set,
FastMCP rejects unauthenticated or mis-authenticated requests to the MCP
endpoint with 401, and accepts requests carrying the correct token.
"""

import asyncio

from fastmcp import FastMCP
from pydantic import SecretStr
from starlette.testclient import TestClient

from netbox_mcp_server.server import build_http_auth

TOKEN = "test-secret-token"

_INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"},
    },
}
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _make_client(token: SecretStr | None) -> TestClient:
    """Build a TestClient for an MCP HTTP app, optionally protected by a token."""
    mcp: FastMCP = FastMCP(name="test-netbox-mcp")

    @mcp.tool
    def ping() -> str:
        return "pong"

    auth = build_http_auth(token)
    if auth is not None:
        mcp.auth = auth
    return TestClient(mcp.http_app())


def test_request_without_token_is_rejected() -> None:
    with _make_client(SecretStr(TOKEN)) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=_HEADERS)
    assert response.status_code == 401


def test_request_with_wrong_token_is_rejected() -> None:
    headers = {**_HEADERS, "Authorization": "Bearer wrong-token"}
    with _make_client(SecretStr(TOKEN)) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=headers)
    assert response.status_code == 401


def test_request_with_valid_token_is_accepted() -> None:
    headers = {**_HEADERS, "Authorization": f"Bearer {TOKEN}"}
    with _make_client(SecretStr(TOKEN)) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=headers)
    assert response.status_code < 400


def test_empty_bearer_rejected_when_token_configured() -> None:
    headers = {**_HEADERS, "Authorization": "Bearer "}
    with _make_client(SecretStr(TOKEN)) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=headers)
    assert response.status_code == 401


def test_unauthenticated_transport_allows_requests() -> None:
    with _make_client(None) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=_HEADERS)
    assert response.status_code != 401


def test_non_ascii_bearer_is_rejected_not_errored() -> None:
    # A non-ASCII bearer must be rejected, not raise (compare_digest rejects
    # non-ASCII str). Driven directly: the httpx TestClient blocks such headers.
    verifier = build_http_auth(SecretStr(TOKEN))
    assert verifier is not None
    assert asyncio.run(verifier.verify_token("\xff")) is None
    assert asyncio.run(verifier.verify_token("caf\xe9")) is None
    # Correct token still authenticates.
    assert asyncio.run(verifier.verify_token(TOKEN)) is not None
