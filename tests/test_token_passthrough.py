"""Tests for per-user NetBox token passthrough on the HTTP transport."""

import asyncio
from unittest.mock import MagicMock, patch

import httpx2
import pytest
from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken
from pydantic import ValidationError
from starlette.testclient import TestClient

from netbox_mcp_server import server
from netbox_mcp_server.config import Settings
from netbox_mcp_server.netbox_client import NetBoxRestClient
from netbox_mcp_server.server import (
    NetBoxTokenVerifier,
    NetBoxUnavailableError,
    get_netbox_client,
    passthrough_warnings,
)

URL = "https://netbox.example.com/"


def _settings(**kwargs) -> Settings:
    with patch.dict("os.environ", {}, clear=True):
        return Settings(netbox_url=URL, _env_file=None, **kwargs)


# ===== Config =====


def test_passthrough_without_shared_token_is_valid():
    settings = _settings(transport="http", token_passthrough=True)
    assert settings.token_passthrough
    assert settings.netbox_token is None
    summary = settings.get_effective_config_summary()
    assert summary["token_passthrough"] is True


def test_passthrough_requires_http_transport():
    with pytest.raises(ValidationError, match="TRANSPORT=http"):
        _settings(transport="stdio", token_passthrough=True)


def test_passthrough_rejects_shared_token():
    with pytest.raises(ValidationError, match="NETBOX_TOKEN must not be set"):
        _settings(transport="http", token_passthrough=True, netbox_token="shared")


def test_passthrough_rejects_mcp_auth_token():
    with pytest.raises(ValidationError, match="MCP_AUTH_TOKEN"):
        _settings(transport="http", token_passthrough=True, mcp_auth_token="secret")


def test_passthrough_rejects_plugin_discovery():
    with pytest.raises(ValidationError, match="ENABLE_PLUGIN_DISCOVERY"):
        _settings(transport="http", token_passthrough=True, enable_plugin_discovery=True)


@pytest.mark.parametrize(
    ("url", "verify_ssl", "expected"),
    [
        ("https://netbox.example.com/", True, []),
        ("http://127.0.0.1:8080/", True, []),
        ("http://localhost:8080/", True, []),
        ("http://netbox.example.com/", True, ["plain HTTP"]),
        ("https://netbox.example.com/", False, ["VERIFY_SSL"]),
    ],
)
def test_passthrough_warns_when_tokens_could_be_exposed(url, verify_ssl, expected):
    with patch.dict("os.environ", {}, clear=True):
        settings = Settings(
            netbox_url=url,
            transport="http",
            token_passthrough=True,
            verify_ssl=verify_ssl,
            _env_file=None,
        )
    warnings = passthrough_warnings(settings)
    assert len(warnings) == len(expected)
    for warning, text in zip(warnings, expected, strict=True):
        assert text in warning


# ===== Client =====


def test_with_token_shares_session_and_uses_own_auth():
    base = NetBoxRestClient(URL, token=None)
    v1 = base.with_token("0123456789abcdef")
    v2 = base.with_token("nbt_key.secret")

    assert v1.session is base.session
    assert v2.session is base.session
    assert base.request_headers == {}
    assert v1.request_headers == {"Authorization": "Token 0123456789abcdef"}
    assert v2.request_headers == {"Authorization": "Bearer nbt_key.secret"}
    assert "Authorization" not in base.session.headers


def test_requests_send_the_clients_own_token():
    base = NetBoxRestClient(URL, token=None)
    user_client = base.with_token("nbt_key.secret")
    response = MagicMock(status_code=200)
    response.json.return_value = {"results": []}

    with patch.object(base.session, "request", return_value=response) as mock_request:
        user_client.get("dcim/sites")

    assert mock_request.call_args.kwargs["headers"] == {"Authorization": "Bearer nbt_key.secret"}


# ===== Verifier =====


def _verifier_with(get: MagicMock) -> NetBoxTokenVerifier:
    client = MagicMock()
    client.with_token.return_value.get = get
    return NetBoxTokenVerifier(client)


def _http_error(status: int) -> httpx2.HTTPStatusError:
    request = httpx2.Request("GET", f"{URL}api/authentication-check/")
    return httpx2.HTTPStatusError(
        "error", request=request, response=httpx2.Response(status, request=request)
    )


def test_verifier_accepts_token_netbox_accepts():
    get = MagicMock(return_value={"id": 7, "username": "alice"})
    verifier = _verifier_with(get)

    access_token = asyncio.run(verifier.verify_token("nbt_alice.secret"))

    assert access_token is not None
    assert access_token.token == "nbt_alice.secret"
    assert access_token.client_id == "alice"
    assert access_token.subject == "netbox-user:7"
    get.assert_called_once_with("authentication-check", fallback_endpoint="users/config")


def test_verifier_gives_each_token_its_own_subject_on_old_netbox():
    # users/config (the NetBox < 4.5 fallback) returns user preferences, no user;
    # sessions are bound to the subject, so it must still differ per caller.
    verifier = _verifier_with(MagicMock(return_value={"tables": {}}))
    alice = asyncio.run(verifier.verify_token("0123456789abcdef"))
    bob = asyncio.run(verifier.verify_token("fedcba9876543210"))
    assert alice is not None
    assert bob is not None
    assert alice.subject is not None
    assert alice.client_id == bob.client_id == "unknown"
    assert alice.subject.startswith("netbox-token:")
    assert alice.subject != bob.subject
    assert "0123456789abcdef" not in alice.subject


@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_verifier_rejects_token_netbox_rejects(status):
    verifier = _verifier_with(MagicMock(side_effect=_http_error(status)))
    assert asyncio.run(verifier.verify_token("nbt_bad.token")) is None


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_verifier_reports_netbox_failure_as_unavailable(status):
    verifier = _verifier_with(MagicMock(side_effect=_http_error(status)))
    with pytest.raises(NetBoxUnavailableError):
        asyncio.run(verifier.verify_token("nbt_any.token"))


@pytest.mark.parametrize(
    "error", [httpx2.ConnectError("down"), httpx2.ReadTimeout("slow")], ids=["connect", "timeout"]
)
def test_verifier_reports_unreachable_netbox_as_unavailable(error):
    verifier = _verifier_with(MagicMock(side_effect=error))
    with pytest.raises(NetBoxUnavailableError):
        asyncio.run(verifier.verify_token("nbt_any.token"))


@pytest.mark.parametrize(
    "token",
    ["", "caf\xe9", "a b", "abc\x01def", "abc\tdef", "x" * 257],
    ids=["empty", "non-ascii", "space", "control", "tab", "too-long"],
)
def test_verifier_rejects_malformed_token_without_calling_netbox(token):
    get = MagicMock()
    verifier = _verifier_with(get)
    assert asyncio.run(verifier.verify_token(token)) is None
    get.assert_not_called()


def test_verifier_caches_accepted_tokens():
    get = MagicMock(return_value={"username": "alice"})
    verifier = _verifier_with(get)

    asyncio.run(verifier.verify_token("nbt_alice.secret"))
    asyncio.run(verifier.verify_token("nbt_alice.secret"))

    get.assert_called_once()


def test_verifier_does_not_cache_rejected_tokens():
    get = MagicMock(side_effect=_http_error(403))
    verifier = _verifier_with(get)

    asyncio.run(verifier.verify_token("nbt_bad.token"))
    asyncio.run(verifier.verify_token("nbt_bad.token"))

    assert get.call_count == 2


def test_verifier_checks_netbox_again_after_cache_expires():
    get = MagicMock(return_value={"username": "alice"})
    verifier = _verifier_with(get)
    start = 1000.0

    with patch.object(server.time, "monotonic", return_value=start):
        asyncio.run(verifier.verify_token("nbt_alice.secret"))
    with patch.object(
        server.time, "monotonic", return_value=start + server.TOKEN_CACHE_SECONDS - 1
    ):
        asyncio.run(verifier.verify_token("nbt_alice.secret"))
    assert get.call_count == 1

    with patch.object(
        server.time, "monotonic", return_value=start + server.TOKEN_CACHE_SECONDS + 1
    ):
        asyncio.run(verifier.verify_token("nbt_alice.secret"))
    assert get.call_count == 2


def _app_with(verifier: NetBoxTokenVerifier) -> TestClient:
    mcp: FastMCP = FastMCP(name="test")

    @mcp.tool
    def ping() -> str:
        return "pong"

    mcp.auth = verifier
    return TestClient(mcp.http_app())


_INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"},
    },
}
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": "Bearer nbt_alice.secret",
}


def test_unreachable_netbox_gives_503_not_401():
    verifier = _verifier_with(MagicMock(side_effect=httpx2.ConnectError("down")))
    with _app_with(verifier) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=_HEADERS)
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.json()["error"] == "temporarily_unavailable"


def test_rejected_token_gives_401():
    verifier = _verifier_with(MagicMock(side_effect=_http_error(403)))
    with _app_with(verifier) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=_HEADERS)
    assert response.status_code == 401


def test_accepted_token_reaches_mcp():
    verifier = _verifier_with(MagicMock(return_value={"username": "alice"}))
    with _app_with(verifier) as client:
        response = client.post("/mcp/", json=_INITIALIZE, headers=_HEADERS)
    assert response.status_code == 200


# ===== Per-request client =====


def test_get_netbox_client_uses_shared_client_without_passthrough():
    shared = MagicMock()
    with patch.object(server, "netbox", shared), patch.object(server, "token_passthrough", False):
        assert get_netbox_client() is shared
    shared.with_token.assert_not_called()


def test_get_netbox_client_uses_callers_token_with_passthrough():
    base = MagicMock()
    access_token = AccessToken(token="nbt_bob.secret", client_id="bob", scopes=[])
    with (
        patch.object(server, "netbox", base),
        patch.object(server, "token_passthrough", True),
        patch.object(server, "get_access_token", return_value=access_token),
    ):
        client = get_netbox_client()

    base.with_token.assert_called_once_with("nbt_bob.secret")
    assert client is base.with_token.return_value


def test_get_netbox_client_refuses_request_without_token():
    with (
        patch.object(server, "netbox", MagicMock()),
        patch.object(server, "token_passthrough", True),
        patch.object(server, "get_access_token", return_value=None),
        pytest.raises(PermissionError),
    ):
        get_netbox_client()
