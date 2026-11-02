"""Seed the local testbed NetBox with sample data and users with different permissions.

Users created (password = TESTBED_PASSWORD):
    alice - can view all sites and devices, nothing else
    bob   - can view only site "site-a", and all prefixes
    carol - no permissions at all

Writes fresh read-only API tokens to testbed/tokens.json: one per user (v2 on NetBox
4.5+, v1 before), plus extra tokens for alice to test edge cases (see ALICE_EXTRA_TOKENS).
Edge cases a NetBox version cannot express are left out of the file.

Usage:
    uv run python testbed/seed.py [--url http://127.0.0.1:18080]
"""

import argparse
import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"  # noqa: S105 - local testbed only
TESTBED_PASSWORD = "Testbed-Password-123"  # noqa: S105 - local testbed only

USERS: dict[str, list[dict[str, Any]]] = {
    "alice": [
        {"name": "alice-dcim-view", "object_types": ["dcim.site", "dcim.device"]},
    ],
    "bob": [
        {
            "name": "bob-site-a-view",
            "object_types": ["dcim.site"],
            "constraints": {"slug": "site-a"},
        },
        {"name": "bob-prefix-view", "object_types": ["ipam.prefix"]},
    ],
    "carol": [],
}

EXPIRING = "expiring"  # placeholder replaced with a time a few seconds from now
EXPIRY_DELAY = 5

# Extra tokens for alice: name -> (minimum NetBox version, token fields)
ALICE_EXTRA_TOKENS: dict[str, tuple[tuple[int, int], dict[str, Any]]] = {
    "alice_v1": ((4, 5), {"version": 1}),
    "alice_disabled": ((4, 5), {"enabled": False}),
    # NetBox only accepts future expiry times, so this expires shortly after creation
    "alice_expired": ((4, 0), {"expires": EXPIRING}),
    # The MCP server sees test clients as 127.0.0.1; NetBox sees it as a Docker IP
    "alice_ip_local": ((4, 0), {"allowed_ips": ["127.0.0.1/32"]}),
    "alice_ip_other": ((4, 0), {"allowed_ips": ["192.0.2.0/24"]}),
}


def token_string(token: dict[str, Any], supplied_key: str | None = None) -> str:
    """Return the plaintext to authenticate with from a token API response."""
    if token.get("version") == 2:
        return f"nbt_{token['key']}.{token['token']}"
    # v1: plaintext is "token" on NetBox 4.5+; before that NetBox only echoes "key"
    # when the client chose it (or from the provision endpoint)
    return token.get("token") or token.get("key") or supplied_key


def auth_header(token: str) -> str:
    """Return the Authorization header value for a v1 or v2 token."""
    return f"Bearer {token}" if token.startswith("nbt_") else f"Token {token}"


def get_or_create(
    client: httpx.Client, endpoint: str, lookup: dict[str, Any], data: dict[str, Any]
) -> dict[str, Any]:
    """Return the first object matching lookup, creating it from data if missing."""
    response = client.get(f"/api/{endpoint}/", params=lookup)
    response.raise_for_status()
    results = response.json()["results"]
    if results:
        return results[0]
    response = client.post(f"/api/{endpoint}/", json=data)
    response.raise_for_status()
    return response.json()


def admin_client(url: str) -> httpx.Client:
    """Provision a token for the admin user and return a client that uses it."""
    response = httpx.post(
        f"{url}/api/users/tokens/provision/",
        json={"username": ADMIN_USER, "password": ADMIN_PASSWORD, "description": "seed"},
    )
    response.raise_for_status()
    return httpx.Client(
        base_url=url,
        headers={
            "Authorization": auth_header(token_string(response.json())),
            "Accept": "application/json",
        },
    )


def netbox_version(client: httpx.Client) -> tuple[int, int]:
    """Return the (major, minor) NetBox version."""
    response = client.get("/api/status/")
    response.raise_for_status()
    major, minor = response.json()["netbox-version"].split(".")[:2]
    return int(major), int(minor)


def seed_data(client: httpx.Client) -> None:
    """Create sites, devices and prefixes."""
    sites = {
        slug: get_or_create(
            client, "dcim/sites", {"slug": slug}, {"name": slug, "slug": slug, "status": "active"}
        )
        for slug in ("site-a", "site-b")
    }
    manufacturer = get_or_create(
        client, "dcim/manufacturers", {"slug": "acme"}, {"name": "Acme", "slug": "acme"}
    )
    device_type = get_or_create(
        client,
        "dcim/device-types",
        {"slug": "acme-switch"},
        {"manufacturer": manufacturer["id"], "model": "Acme Switch", "slug": "acme-switch"},
    )
    role = get_or_create(
        client, "dcim/device-roles", {"slug": "switch"}, {"name": "Switch", "slug": "switch"}
    )
    for name, site in (("sw-a1", "site-a"), ("sw-b1", "site-b")):
        get_or_create(
            client,
            "dcim/devices",
            {"name": name},
            {
                "name": name,
                "site": sites[site]["id"],
                "device_type": device_type["id"],
                "role": role["id"],
                "status": "active",
            },
        )
    for prefix in ("10.0.0.0/24", "10.1.0.0/24"):
        get_or_create(client, "ipam/prefixes", {"prefix": prefix}, {"prefix": prefix})


def create_token(client: httpx.Client, user_id: int, **fields: Any) -> str:
    """Create a read-only token for a user and return its plaintext."""
    # NetBox < 4.5 never reveals a generated key, so choose one; newer versions ignore it
    key = secrets.token_hex(20)
    response = client.post(
        "/api/users/tokens/",
        json={
            "user": user_id,
            "key": key,
            "write_enabled": False,
            "description": "mcp testbed",
            **fields,
        },
    )
    response.raise_for_status()
    return token_string(response.json(), key)


def seed_user(client: httpx.Client, username: str, permissions: list[dict[str, Any]]) -> int:
    """Create a user with the given object permissions, drop old tokens, return its ID."""
    user = get_or_create(
        client,
        "users/users",
        {"username": username},
        {"username": username, "password": TESTBED_PASSWORD},
    )
    for perm in permissions:
        get_or_create(
            client,
            "users/permissions",
            {"name": perm["name"]},
            {**perm, "actions": ["view"], "users": [user["id"]]},
        )

    # Replace any old tokens so tokens.json always matches what NetBox has
    old_tokens = client.get("/api/users/tokens/", params={"user_id": user["id"]})
    old_tokens.raise_for_status()
    for token in old_tokens.json()["results"]:
        client.delete(f"/api/users/tokens/{token['id']}/").raise_for_status()
    return user["id"]


def main() -> None:
    """Seed the testbed and write user tokens to tokens.json."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18080")
    args = parser.parse_args()

    with admin_client(args.url.rstrip("/")) as client:
        version = netbox_version(client)
        seed_data(client)
        user_ids = {name: seed_user(client, name, perms) for name, perms in USERS.items()}
        tokens = {name: create_token(client, user_id) for name, user_id in user_ids.items()}
        expires_at = datetime.now(UTC) + timedelta(seconds=EXPIRY_DELAY)
        for name, (min_version, fields) in ALICE_EXTRA_TOKENS.items():
            if version >= min_version:
                if fields.get("expires") == EXPIRING:
                    fields = {**fields, "expires": expires_at.isoformat()}
                tokens[name] = create_token(client, user_ids["alice"], **fields)
        # Let the expiring token expire before anyone uses tokens.json
        time.sleep(max(0.0, (expires_at - datetime.now(UTC)).total_seconds() + 1))

    out = Path(__file__).parent / "tokens.json"
    out.write_text(json.dumps(tokens, indent=2) + "\n")
    print(f"Seeded NetBox {version[0]}.{version[1]} at {args.url}; tokens written to {out}")  # noqa: T201


if __name__ == "__main__":
    main()
