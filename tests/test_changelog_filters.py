"""Exercise changelog filtering through a loopback HTTP endpoint."""

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from netbox_mcp_server import server
from netbox_mcp_server.netbox_client import NetBoxRestClient


@pytest.fixture
def changelog_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[list[dict[str, list[str]]]]:
    """Capture requests made by the real REST client."""
    requests: list[dict[str, list[str]]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            assert parsed.path == "/api/core/object-changes/"
            requests.append(parse_qs(parsed.query))
            body = json.dumps({"count": 0, "results": [], "next": None, "previous": None}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        client = NetBoxRestClient(f"http://127.0.0.1:{httpd.server_port}", "test-token")
        monkeypatch.setattr(server, "netbox", client)
        try:
            yield requests
        finally:
            client.session.close()
            httpd.shutdown()
            thread.join()


@pytest.mark.parametrize(
    "filters",
    [
        {"changed_object_id__in": [1, 2]},
        {"changed_object__device__site": "example"},
    ],
)
def test_changelog_rejects_unsupported_filters_before_http(
    filters: dict[str, object],
    changelog_requests: list[dict[str, list[str]]],
) -> None:
    """Changelog queries obey the same filter rules as object queries."""
    with pytest.raises(ValueError, match="Invalid filter"):
        server.netbox_get_changelogs(filters)
    assert changelog_requests == []


@pytest.mark.parametrize(
    ("filters", "expected"),
    [
        (
            {"changed_object_id": [1, 2], "action": "update", "limit": 5},
            {"changed_object_id": ["1", "2"], "action": ["update"], "limit": ["5"]},
        ),
        ({"object_repr__ic": "router"}, {"object_repr__ic": ["router"]}),
    ],
)
def test_changelog_preserves_supported_filters_over_http(
    filters: dict[str, object],
    expected: dict[str, list[str]],
    changelog_requests: list[dict[str, list[str]]],
) -> None:
    """Supported exact/list/lookup filters still reach the API unchanged."""
    assert server.netbox_get_changelogs(filters)["results"] == []
    assert changelog_requests == [expected]
