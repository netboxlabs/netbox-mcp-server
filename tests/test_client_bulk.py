"""Exercise bulk helpers through HTTPX's real request serialization."""

import json
from collections.abc import Iterator

import httpx
import pytest

from netbox_mcp_server.netbox_client import NetBoxRestClient


@pytest.fixture
def bulk_client() -> Iterator[tuple[NetBoxRestClient, list[httpx.Request]]]:
    """Provide the documented list endpoint without a live NetBox server."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path != "/api/dcim/sites/":
            return httpx.Response(404)
        if request.method == "DELETE":
            return httpx.Response(204)
        status = 201 if request.method == "POST" else 200
        return httpx.Response(status, json=json.loads(request.content))

    client = NetBoxRestClient("https://netbox.example", "test-token")
    headers = client.session.headers
    client.session.close()
    client.session = httpx.Client(transport=httpx.MockTransport(handler), headers=headers)
    try:
        yield client, requests
    finally:
        client.session.close()


@pytest.mark.parametrize(
    ("operation", "method", "values", "payload"),
    [
        ("bulk_create", "POST", [{"name": "one"}], [{"name": "one"}]),
        ("bulk_update", "PATCH", [{"id": 1, "name": "one"}], [{"id": 1, "name": "one"}]),
        ("bulk_delete", "DELETE", [1, 2], [{"id": 1}, {"id": 2}]),
    ],
)
def test_bulk_requests_use_list_endpoint(
    bulk_client: tuple[NetBoxRestClient, list[httpx.Request]],
    operation: str,
    method: str,
    values: list[dict[str, object]] | list[int],
    payload: list[dict[str, object]],
) -> None:
    """Send each operation's JSON body to the model's list URL."""
    client, requests = bulk_client

    result = getattr(client, operation)("dcim/sites", values)

    assert result == (True if method == "DELETE" else payload)
    assert len(requests) == 1
    assert requests[0].method == method
    assert str(requests[0].url) == "https://netbox.example/api/dcim/sites/"
    assert requests[0].headers["authorization"] == "Token test-token"
    assert json.loads(requests[0].content) == payload


@pytest.mark.parametrize("operation", ["bulk_create", "bulk_update", "bulk_delete"])
def test_bulk_requests_propagate_api_errors(
    bulk_client: tuple[NetBoxRestClient, list[httpx.Request]], operation: str
) -> None:
    """Keep the client's existing HTTP error behavior for bulk requests."""
    client, _ = bulk_client
    client.session.close()
    client.session = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403)))

    with pytest.raises(httpx.HTTPStatusError) as error:
        getattr(client, operation)("dcim/sites", [])

    assert error.value.response.status_code == 403
