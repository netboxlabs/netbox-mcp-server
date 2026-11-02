"""End-to-end tests for token passthrough against the local testbed NetBox.

Starts the real server over HTTP with TOKEN_PASSTHROUGH and connects as the users
created by testbed/seed.py, checking that each one only sees what NetBox lets them.

Skipped unless the testbed is seeded:
    docker compose -f testbed/docker-compose.yml up -d --wait
    uv run python testbed/seed.py
"""

import asyncio
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError

NETBOX_URL = os.environ.get("NETBOX_TESTBED_URL", "http://127.0.0.1:18080")
TOKENS_FILE = Path(__file__).parents[2] / "testbed" / "tokens.json"


def _testbed_tokens() -> dict[str, str] | None:
    if not TOKENS_FILE.exists():
        return None
    try:
        httpx.get(f"{NETBOX_URL}/api/status/", timeout=5)
    except httpx.HTTPError:
        return None
    return json.loads(TOKENS_FILE.read_text())


TOKENS = _testbed_tokens() or {}
pytestmark = pytest.mark.skipif(not TOKENS, reason="testbed NetBox not running or seeded")


def token(name: str) -> str:
    if name not in TOKENS:
        pytest.skip(f"this NetBox version has no {name} token (see testbed/seed.py)")
    return TOKENS[name]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def run_server(
    *args: str, env: dict[str, str] | None = None, netbox_url: str = NETBOX_URL
) -> Iterator[tuple[str, Path]]:
    """Run the server with token passthrough; yield its MCP URL and log file."""
    port = _free_port()
    server_env = {
        k: v for k, v in os.environ.items() if k not in ("NETBOX_TOKEN", "MCP_AUTH_TOKEN")
    }
    server_env.update(env or {})
    log_path = Path(tempfile.mkdtemp()) / "server.log"
    with log_path.open("wb") as log:
        proc = subprocess.Popen(  # noqa: S603 - fixed args, test only
            [
                sys.executable,
                "-m",
                "netbox_mcp_server",
                "--netbox-url",
                netbox_url,
                "--transport",
                "http",
                "--port",
                str(port),
                "--token-passthrough",
                "--log-level",
                "DEBUG",
                *args,
            ],
            env=server_env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    socket.create_connection(("127.0.0.1", port), timeout=1).close()
                    break
                except OSError:
                    if proc.poll() is not None or time.monotonic() > deadline:
                        pytest.fail(f"MCP server did not start:\n{log_path.read_text()}")
                    time.sleep(0.2)
            yield f"http://127.0.0.1:{port}/mcp", log_path
        finally:
            proc.terminate()
            proc.wait(timeout=10)


@pytest.fixture(scope="module")
def server() -> Iterator[tuple[str, Path]]:
    with run_server() as running:
        yield running


@pytest.fixture(scope="module")
def mcp_url(server) -> str:
    return server[0]


async def _call(url: str, bearer: str, tool: str, args: dict, headers: dict | None) -> dict:
    async with Client(StreamableHttpTransport(url, headers=headers, auth=bearer)) as client:
        result = await client.call_tool(tool, args)
    return result.structured_content or json.loads(result.content[0].text)


def call(url: str, user: str, tool: str, args: dict, headers: dict[str, str] | None = None) -> dict:
    return asyncio.run(_call(url, token(user), tool, args, headers))


def names(response: dict) -> set[str]:
    return {obj["name"] for obj in response["results"]}


def get_objects(object_type: str) -> dict:
    return {"object_type": object_type, "filters": {}, "fields": ["id", "name"], "limit": 100}


def site_names(url: str, user: str, headers: dict[str, str] | None = None) -> set[str]:
    return names(call(url, user, "netbox_get_objects", get_objects("dcim.site"), headers))


def http_status(url: str, bearer: str | None, headers: dict[str, str] | None = None) -> int:
    """Status of a bare MCP initialize request, which only exercises authentication."""
    all_headers = {"Accept": "application/json, text/event-stream", **(headers or {})}
    if bearer is not None:
        all_headers["Authorization"] = f"Bearer {bearer}"
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    }
    return httpx.post(url, json=initialize, headers=all_headers).status_code


@pytest.fixture
def admin() -> Iterator[httpx.Client]:
    response = httpx.post(
        f"{NETBOX_URL}/api/users/tokens/provision/",
        json={"username": "admin", "password": "admin", "description": "mcp test"},
    )
    response.raise_for_status()
    data = response.json()
    bearer = f"nbt_{data['key']}.{data['token']}" if data.get("version") == 2 else None
    auth = f"Bearer {bearer}" if bearer else f"Token {data.get('token') or data['key']}"
    with httpx.Client(
        base_url=NETBOX_URL, headers={"Authorization": auth, "Accept": "application/json"}
    ) as client:
        yield client
        client.delete(f"/api/users/tokens/{data['id']}/")


def new_alice_token(admin: httpx.Client) -> tuple[int, str]:
    """Create a fresh token for alice; return its ID and plaintext."""
    alice = admin.get("/api/users/users/", params={"username": "alice"}).json()["results"][0]
    key = secrets.token_hex(20)  # only used by NetBox < 4.5, which never reveals keys
    response = admin.post(
        "/api/users/tokens/", json={"user": alice["id"], "key": key, "write_enabled": False}
    )
    response.raise_for_status()
    data = response.json()
    if data.get("version") == 2:
        return data["id"], f"nbt_{data['key']}.{data['token']}"
    return data["id"], data.get("token") or data.get("key") or key


# ===== Authentication =====


def test_request_without_token_is_rejected(mcp_url):
    assert http_status(mcp_url, None) == 401


def test_request_with_invalid_token_is_rejected(mcp_url):
    assert http_status(mcp_url, "nbt_bogus.token") == 401
    assert http_status(mcp_url, "deadbeef" * 5) == 401


def test_v1_token_works(mcp_url):
    assert site_names(mcp_url, "alice_v1") == {"site-a", "site-b"}


@pytest.mark.parametrize("name", ["alice_disabled", "alice_expired"])
def test_disabled_and_expired_tokens_are_rejected(mcp_url, name):
    assert http_status(mcp_url, token(name)) == 401


def test_unreachable_netbox_gives_503():
    with run_server(netbox_url=f"http://127.0.0.1:{_free_port()}") as (url, _):
        assert http_status(url, token("alice")) == 503


# ===== Permissions follow the NetBox user =====


def test_alice_sees_all_sites_and_devices(mcp_url):
    assert site_names(mcp_url, "alice") == {"site-a", "site-b"}
    assert names(call(mcp_url, "alice", "netbox_get_objects", get_objects("dcim.device"))) == {
        "sw-a1",
        "sw-b1",
    }


def test_alice_cannot_see_prefixes(mcp_url):
    with pytest.raises(ToolError, match="403"):
        call(mcp_url, "alice", "netbox_get_objects", get_objects("ipam.prefix"))


def test_bob_sees_only_his_constrained_site(mcp_url):
    sites = call(mcp_url, "bob", "netbox_get_objects", get_objects("dcim.site"))
    assert sites["count"] == 1
    assert names(sites) == {"site-a"}


def test_bob_cannot_fetch_hidden_site_by_id(mcp_url):
    site_b = call(
        mcp_url,
        "alice",
        "netbox_get_objects",
        {"object_type": "dcim.site", "filters": {"slug": "site-b"}, "fields": ["id"]},
    )["results"][0]
    with pytest.raises(ToolError, match="404"):
        call(
            mcp_url,
            "bob",
            "netbox_get_object_by_id",
            {"object_type": "dcim.site", "object_id": site_b["id"]},
        )


def test_bob_sees_prefixes_but_not_devices(mcp_url):
    prefixes = call(
        mcp_url,
        "bob",
        "netbox_get_objects",
        {"object_type": "ipam.prefix", "filters": {}, "fields": ["prefix"]},
    )
    assert {p["prefix"] for p in prefixes["results"]} == {"10.0.0.0/24", "10.1.0.0/24"}
    with pytest.raises(ToolError, match="403"):
        call(mcp_url, "bob", "netbox_get_objects", get_objects("dcim.device"))


def test_carol_sees_nothing(mcp_url):
    with pytest.raises(ToolError, match="403"):
        call(mcp_url, "carol", "netbox_get_objects", get_objects("dcim.site"))
    with pytest.raises(ToolError, match="403"):
        call(mcp_url, "carol", "netbox_get_changelogs", {"filters": {}})
    search = call(mcp_url, "carol", "netbox_search_objects", {"query": "s"})
    assert all(results == [] for results in search.values())


def test_search_results_follow_user_permissions(mcp_url):
    alice = call(mcp_url, "alice", "netbox_search_objects", {"query": "site", "fields": ["name"]})
    bob = call(mcp_url, "bob", "netbox_search_objects", {"query": "site", "fields": ["name"]})
    assert {s["name"] for s in alice["dcim.site"]} == {"site-a", "site-b"}
    assert {s["name"] for s in bob["dcim.site"]} == {"site-a"}


def test_concurrent_users_do_not_share_tokens(mcp_url):
    """Interleave many calls from two users; each must only ever get their own view."""

    async def site_counts(user: str) -> set[int]:
        counts: set[int] = set()
        async with Client(mcp_url, auth=TOKENS[user]) as client:
            # Rounds of 5 keep both users together under the testbed NetBox's
            # 16-request concurrency limit (granian backpressure), past which
            # extra keep-alive connections stall for ~30s.
            for _ in range(4):
                results = await asyncio.gather(
                    *(
                        client.call_tool("netbox_get_objects", get_objects("dcim.site"))
                        for _ in range(5)
                    )
                )
                counts |= {r.structured_content["count"] for r in results}
        return counts

    async def run() -> tuple[set[int], set[int]]:
        return await asyncio.gather(site_counts("alice"), site_counts("bob"))

    alice_counts, bob_counts = asyncio.run(run())
    assert alice_counts == {2}
    assert bob_counts == {1}


def test_reused_session_id_still_uses_the_requests_own_token(mcp_url):
    """Bob reusing Alice's MCP session ID must get Bob's view, never Alice's."""
    headers = {"Accept": "application/json, text/event-stream"}
    init = httpx.post(
        mcp_url,
        headers={**headers, "Authorization": f"Bearer {token('alice')}"},
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "alice", "version": "1.0"},
            },
        },
    )
    session = {"mcp-session-id": init.headers["mcp-session-id"]}

    response = httpx.post(
        mcp_url,
        headers={**headers, **session, "Authorization": f"Bearer {token('bob')}"},
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "netbox_get_objects", "arguments": get_objects("dcim.site")},
        },
    )

    if response.status_code != 200:
        # The MCP SDK binds sessions to the user who opened them and answers 404
        assert response.status_code == 404
        return
    data = next(
        json.loads(line[5:]) for line in response.text.splitlines() if line.startswith("data:")
    )
    assert data["result"]["structuredContent"]["count"] == 1


# ===== Token lifecycle =====


def test_revoked_token_loses_access_even_while_cached(mcp_url, admin):
    token_id, fresh = new_alice_token(admin)

    async def run() -> None:
        async with Client(mcp_url, auth=fresh) as client:
            before = await client.call_tool("netbox_get_objects", get_objects("dcim.site"))
            assert before.structured_content["count"] == 2
            admin.delete(f"/api/users/tokens/{token_id}/").raise_for_status()
            # The server still remembers the token, but NetBox refuses it
            with pytest.raises(ToolError, match="403"):
                await client.call_tool("netbox_get_objects", get_objects("dcim.site"))

    asyncio.run(run())


def test_revoked_token_is_rejected_at_once_with_zero_ttl(admin):
    token_id, fresh = new_alice_token(admin)
    with run_server("--token-cache-ttl", "0") as (url, _):
        assert http_status(url, fresh) == 200
        admin.delete(f"/api/users/tokens/{token_id}/").raise_for_status()
        assert http_status(url, fresh) == 401


# ===== Token allowed IPs =====
#
# Test clients reach the MCP server from 127.0.0.1, but NetBox sees the MCP server
# as a Docker gateway address. alice_ip_local only allows 127.0.0.1;
# alice_ip_other only allows 192.0.2.0/24.


def test_ip_restricted_tokens_fail_without_forwarding(mcp_url):
    # NetBox sees the MCP server's address, so neither restriction matches
    assert http_status(mcp_url, token("alice_ip_local")) == 401
    assert http_status(mcp_url, token("alice_ip_other")) == 401


@pytest.fixture(scope="module")
def forwarding_url() -> Iterator[str]:
    # Trust no proxies, so a client's own X-Forwarded-For header is ignored
    with run_server("--forward-client-ip", env={"FORWARDED_ALLOW_IPS": ""}) as (url, _):
        yield url


def test_forwarding_lets_netbox_check_the_real_client_ip(forwarding_url):
    assert site_names(forwarding_url, "alice_ip_local") == {"site-a", "site-b"}
    assert http_status(forwarding_url, token("alice_ip_other")) == 401


def test_client_cannot_spoof_its_ip(forwarding_url):
    spoofed = {"X-Forwarded-For": "192.0.2.10", "X-Real-IP": "192.0.2.10"}
    assert http_status(forwarding_url, token("alice_ip_other"), spoofed) == 401
    # The spoofed header does not replace the real address either
    assert site_names(forwarding_url, "alice_ip_local", spoofed) == {"site-a", "site-b"}


def test_forwarding_uses_client_ip_from_trusted_proxy():
    # Pretend a reverse proxy on 127.0.0.1 says the user is 192.0.2.10
    with run_server("--forward-client-ip", env={"FORWARDED_ALLOW_IPS": "127.0.0.1"}) as (url, _):
        proxied = {"X-Forwarded-For": "192.0.2.10"}
        assert site_names(url, "alice_ip_other", proxied) == {"site-a", "site-b"}
        assert http_status(url, token("alice_ip_local"), proxied) == 401


# ===== Secrets =====


def test_tokens_never_appear_in_debug_logs(server):
    url, log_path = server
    site_names(url, "alice")
    log = log_path.read_text(errors="replace")
    assert "HTTP Request: GET" in log  # the log captured NetBox traffic
    for value in TOKENS.values():
        secret = value.split(".")[-1]
        assert secret not in log
