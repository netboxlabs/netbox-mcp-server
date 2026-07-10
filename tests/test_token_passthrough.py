"""Test for Netbox token passthrough (issue #170)."""

from unittest.mock import MagicMock, patch

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from netbox_mcp_server.netbox_client import (
    NetBoxRestClient,
    reset_forward_token,
    set_forward_token,
)
from netbox_mcp_server.server import TokenPassthroughMiddleware


@pytest.fixture
def client():
    """Creates NetboxRestClient with some defaults."""
    return NetBoxRestClient(
        url="https://netbox.example.com",
        token="server-token",
        verify_ssl=True
    )

def _mock_get_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"count": 0, "results": []}
    response.raise_for_status = MagicMock()
    return response

def test_default_token_used_when_no_forward_token(client):
    """Verifies that the client uses its default configured token when no override is present."""
    with patch.object(client.session, "get", return_value=_mock_get_response()) as mock_get:
        client.get("dcim/sites")

    assert mock_get.call_args.kwargs["headers"] is None
    assert client.session.headers["Authorization"] == "Token server-token"

def test_forward_token_overrides_client_token(client):
    """Ensures a manually forwarded token correctly overrides the client's
    default header for API calls."""
    reset_handle = set_forward_token("user-personal-token")
    try:
        with patch.object(client.session, "get", return_value=_mock_get_response()) as mock_get:
            client.get("dcim/sites")
    finally:
        reset_forward_token(reset_handle)

    assert mock_get.call_args.kwargs["headers"] == {"Authorization": "Token user-personal-token"}
    # The client's own default header is untouched.
    assert client.session.headers["Authorization"] == "Token server-token"

def test_forward_nbt_token_users_bearer_schema(client):
    """Validates that the system formats NBT tokens using the required Bearer schema."""
    reset_handle = set_forward_token("nbt_abc123")
    try:
        with patch.object(client.session, "get", return_value=_mock_get_response()) as mock_get:
            client.get("dcim/sites")
    finally:
        reset_forward_token(reset_handle)

    assert mock_get.call_args.kwargs["headers"] == {"Authorization": "Bearer nbt_abc123"}

def test_forward_token_is_request_scoped(client):
    """Confirms that forwarded tokens only apply to the specific request
    and are not global/sticky."""
    reset_handle = set_forward_token("user-personal-token")
    reset_forward_token(reset_handle)

    with patch.object(client.session, "get", return_value=_mock_get_response()) as mock_get:
        client.get("dcim/sites")

    assert mock_get.call_args.kwargs["headers"] is None

def _make_app() -> TestClient:
    captured: dict[str, str | None] = {}

    async def endpoint(request):
        from netbox_mcp_server.netbox_client import _forwarded_token

        captured["token"] = _forwarded_token.get()
        return JSONResponse({"token": captured["token"]})

    app = Starlette(
        routes=[Route("/echo", endpoint)],
        middleware=[Middleware(TokenPassthroughMiddleware)],
    )
    return TestClient(app)

def test_middleware_extracts_bearer_token():
    """Tests that the middleware successfully extracts
    a valid Bearer token from incoming headers."""
    with _make_app() as client:
        response = client.get("/echo", headers={"Authorization": "Bearer my-token"})
    assert response.json() == {"token": "my-token"}

def test_middleware_leave_token_unset_without_headers():
    """Verifies that if no Authorization header is provided,
    the middleware passes `None` for the token."""
    with _make_app() as client:
        response = client.get("/echo")
    assert response.json() == {"token": None}

def test_middleware_ignores_non_bearer_authorization():
    """Checks that tokens supplied using schemas other than
    Bearer (e.g., Basic) are ignored by the middleware."""
    with _make_app() as client:
        response = client.get("/echo", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert response.json() == {"token": None}
