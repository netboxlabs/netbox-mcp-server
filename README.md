# NetBox MCP Server

> **⚠️ Breaking Change in v1.0.0**: The project structure has changed.
> If upgrading from v0.1.0, update your configuration:
> - Change `uv run server.py` to `uv run netbox-mcp-server`
> - Update Claude Desktop/Code configs to use `netbox-mcp-server` instead of `server.py`
> - Docker users: rebuild images with updated CMD
> - See [CHANGELOG.md](CHANGELOG.md) for full details

This is a simple read-only [Model Context Protocol](https://modelcontextprotocol.io/) server for NetBox. It enables you to interact with your data in NetBox directly via LLMs that support MCP.

The server is intentionally simple: easy to get started with, hard to misuse (read-only by default, no plugin surface), and easy to fork and adapt. Forking under Apache 2.0 is a first-class path for users who need capabilities beyond the project's scope.

## Community

For chat, use cases, and general MCP discussion, join the NetBox community at [netdev.chat](https://netdev.chat). The **#ai** channel is the right home for MCP integrations, questions, and sharing use cases. Bugs and feature ideas specific to this server go in [issues](https://github.com/netboxlabs/netbox-mcp-server/issues).

## Tools

| Tool | Description |
|------|-------------|
| get_objects | Retrieves NetBox core objects based on their type and filters |
| get_object_by_id | Gets detailed information about a specific NetBox object by its ID |
| get_changelogs | Retrieves change history records (audit trail) based on filters |

> Note: Core NetBox object types are always available. Plugin object types can be auto-discovered. See [Plugin Object Type Discovery](#plugin-object-type-discovery). Advanced features (GraphQL, dynamic model discovery, etc.) are deliberately out of scope. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full scope statement and rationale.

## Usage

1. Create a read-only API token in NetBox with sufficient permissions for the tool to access the data you want to make available via MCP.

2. Install dependencies:

    ```bash
    # Using UV (recommended)
    uv sync

    # Or using pip
    pip install -e .
    ```

3. Verify the server can run: `NETBOX_URL=https://netbox.example.com/ NETBOX_TOKEN=<your-api-token> uv run netbox-mcp-server`

4. Add the MCP server to your LLM client. See below for some examples with Claude.

### Claude Code

#### Stdio Transport (Default)

Add the server using the `claude mcp add` command:

```bash
claude mcp add --transport stdio netbox \
  --env NETBOX_URL=https://netbox.example.com/ \
  --env NETBOX_TOKEN=<your-api-token> \
  -- uv --directory /path/to/netbox-mcp-server run netbox-mcp-server
```

**Important notes:**

- Replace `/path/to/netbox-mcp-server` with the absolute path to your local clone
- The `--` separator distinguishes Claude Code flags from the server command
- Use `--scope project` to share the configuration via `.mcp.json` in version control
- Use `--scope user` to make it available across all your projects (default is `local`)

After adding, verify with `/mcp` in Claude Code or `claude mcp list` in your terminal.

#### HTTP Transport

For HTTP transport, first start the server manually:

```bash
# Start the server with HTTP transport (using .env or environment variables)
NETBOX_URL=https://netbox.example.com/ \
NETBOX_TOKEN=<your-api-token> \
TRANSPORT=http \
uv run netbox-mcp-server
```

Then add the running server to Claude Code:

```bash
# Add the HTTP MCP server (note: URL must include http:// or https:// prefix)
claude mcp add --transport http netbox http://127.0.0.1:8000/mcp
```

**Important notes:**

- The URL **must** include the protocol prefix (`http://` or `https://`)
- The default endpoint is `/mcp` when using HTTP transport
- The server must be running before Claude Code can connect
- Verify the connection with `claude mcp list` - you should see a ✓ next to the server name

### Claude Desktop

Add the server configuration to your Claude Desktop config file. On Mac, edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "netbox": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/netbox-mcp-server",
                "run",
                "netbox-mcp-server"
            ],
            "env": {
                "NETBOX_URL": "https://netbox.example.com/",
                "NETBOX_TOKEN": "<your-api-token>"
            }
        }
    }
}
```

> On Windows, use full, escaped path to your instance, such as `C:\\Users\\myuser\\.local\\bin\\uv` and `C:\\Users\\myuser\\netbox-mcp-server`.
> For detailed troubleshooting, consult the [MCP quickstart](https://modelcontextprotocol.io/quickstart/user).

5. Use the tools in your LLM client.  For example:

```text
> Get all devices in the 'Equinix DC14' site
...
> Tell me about my IPAM utilization
...
> What Cisco devices are in my network?
...
> Who made changes to the NYC site in the last week?
...
> Show me all configuration changes to the core router in the last month
```

### Field Filtering (Token Optimization)

Both `netbox_get_objects()` and `netbox_get_object_by_id()` support an optional `fields` parameter to reduce token usage:

```python
# Without fields: ~5000 tokens for 50 devices
devices = netbox_get_objects("devices", {"site": "datacenter-1"})

# With fields: ~500 tokens (90% reduction)
devices = netbox_get_objects(
    "devices", {"site": "datacenter-1"}, fields=["id", "name", "status", "site"]
)
```

**Common field patterns:**

- **Devices:** `['id', 'name', 'status', 'device_type', 'site', 'primary_ip4']`
- **IP Addresses:** `['id', 'address', 'status', 'dns_name', 'description']`
- **Interfaces:** `['id', 'name', 'type', 'enabled', 'device']`
- **Sites:** `['id', 'name', 'status', 'region', 'description']`

The `fields` parameter uses NetBox's native field filtering. See the [NetBox API documentation](https://docs.netbox.dev/en/stable/integrations/rest-api/) for details.

## Configuration

The server supports multiple configuration sources with the following precedence (highest to lowest):

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **`.env` file** in the project root
4. **Default values** (lowest priority)

### Configuration Reference

| Setting | Type | Default | Required | Description |
|---------|------|---------|----------|-------------|
| `NETBOX_URL` | URL | - | Yes | Base URL of your NetBox instance (e.g., https://netbox.example.com/) |
| `NETBOX_TOKEN` | String | - | Unless `TOKEN_PASSTHROUGH` | API token for authentication. Must not be set with `TOKEN_PASSTHROUGH`. |
| `TRANSPORT` | `stdio` \| `http` | `stdio` | No | MCP transport protocol |
| `HOST` | String | `127.0.0.1` | If HTTP | Host address for HTTP server |
| `PORT` | Integer | `8000` | If HTTP | Port for HTTP server |
| `MCP_AUTH_TOKEN` | String | - | No | Bearer token required on the HTTP endpoint. When unset, the HTTP transport is unauthenticated. Clients send `Authorization: Bearer <token>`. |
| `TOKEN_PASSTHROUGH` | Boolean | `false` | No | HTTP only. Each client sends its own NetBox token and NetBox applies that user's permissions. See [Per-User NetBox Tokens](#per-user-netbox-tokens-token-passthrough). |
| `TOKEN_CACHE_TTL` | Float | `60` | No | With `TOKEN_PASSTHROUGH`: seconds to remember an accepted token, `0` to check every request |
| `FORWARD_CLIENT_IP` | Boolean | `false` | No | With `TOKEN_PASSTHROUGH`: send each client's IP to NetBox so token allowed-IP rules apply to the user |
| `VERIFY_SSL` | Boolean | `true` | No | Whether to verify SSL certificates |
| `ENABLE_PLUGIN_DISCOVERY` | Boolean | `false` | No | Auto-discover plugin object types at startup |
| `LOG_LEVEL` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL` | `INFO` | No | Logging verbosity |

### Transport Examples

#### Stdio Transport (Claude Desktop/Code)

For local Claude Desktop or Claude Code usage with stdio transport:

```json
{
    "mcpServers": {
        "netbox": {
            "command": "uv",
            "args": ["--directory", "/path/to/netbox-mcp-server", "run", "netbox-mcp-server"],
            "env": {
                "NETBOX_URL": "https://netbox.example.com/",
                "NETBOX_TOKEN": "<your-api-token>"
            }
        }
    }
}
```

#### HTTP Transport (Web Clients)

For web-based MCP clients using HTTP/SSE transport:

```bash
# Using environment variables
export NETBOX_URL=https://netbox.example.com/
export NETBOX_TOKEN=<your-api-token>
export TRANSPORT=http
export HOST=127.0.0.1
export PORT=8000

uv run netbox-mcp-server

# Or using CLI arguments
uv run netbox-mcp-server \
  --netbox-url https://netbox.example.com/ \
  --netbox-token <your-api-token> \
  --transport http \
  --host 127.0.0.1 \
  --port 8000
```

#### Per-User NetBox Tokens (Token Passthrough)

By default every client shares the permissions of `NETBOX_TOKEN`. With
`TOKEN_PASSTHROUGH=true`, each client sends its own NetBox API token instead, and the
server makes every NetBox call with that token. NetBox then applies that user's
object permissions, so two people using the same server only see what they could see
in NetBox itself.

```bash
export NETBOX_URL=https://netbox.example.com/
export TRANSPORT=http
export TOKEN_PASSTHROUGH=true
# NETBOX_TOKEN must not be set

uv run netbox-mcp-server
```

Each user creates an API token in NetBox (read-only is enough) and adds it to their
client. Send it as `Bearer` even for v1 tokens; the server uses the right scheme
towards NetBox.

```bash
claude mcp add --transport http netbox https://mcp.example.com/mcp \
  --header "Authorization: Bearer <your-netbox-token>"
```

How it works:

- The server checks each bearer against NetBox (`/api/authentication-check/`, or
  `/api/users/config/` on NetBox < 4.5). A token NetBox rejects (invalid, disabled,
  expired, or not allowed from this IP) gets `401`. If NetBox cannot be reached or
  fails, the client gets `503` with `Retry-After`, not a misleading `401`.
- Accepted tokens are remembered for `TOKEN_CACHE_TTL` seconds (default 60). A token
  revoked in that window still gets no data, because NetBox rejects the tool calls
  made with it. Set `TOKEN_CACHE_TTL=0` to check NetBox on every request.
- An MCP session belongs to the user who opened it; another user's token cannot use it.
- Tokens are kept in memory only (hashed as cache keys) and are never logged.
- Clients send their NetBox token to this server, so always put it behind TLS.

Additional settings for this mode:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `TOKEN_CACHE_TTL` | Float | `60` | Seconds to remember an accepted token. `0` checks every request. |
| `FORWARD_CLIENT_IP` | Boolean | `false` | Send each client's IP to NetBox as `X-Forwarded-For`, so tokens with **Allowed IPs** are checked against the real user. |

**Tokens with Allowed IPs.** NetBox checks a token's allowed IPs against the address
that connects to it, which is this server, not the user. Without
`FORWARD_CLIENT_IP`, such tokens only work if the allowed range includes this
server. With it, the server sends the client's address, taken from the TCP
connection, never from headers the client sends. If this server runs behind a
reverse proxy, set `FORWARDED_ALLOW_IPS` to the proxy's address so the user's IP is
read from the proxy's `X-Forwarded-For`. It defaults to `127.0.0.1,::1`; set it to an
empty string when no proxy is used, so local clients cannot claim another address. On the NetBox side, the forwarded address
only counts if NetBox's own proxy keeps it: NetBox reads `X-Real-IP` first, then the
first `X-Forwarded-For` entry, so a proxy that overwrites these makes NetBox see
this server again (tokens then fail, they are never let through).

Limitations:

- `MCP_AUTH_TOKEN` and `ENABLE_PLUGIN_DISCOVERY` cannot be combined with this mode,
  since both rely on a shared token. Plugin object types are not available.
- Clients must be able to send a static `Authorization` header. MCP clients that
  only support OAuth sign-in cannot use this mode.
- Each request with an unknown token costs one NetBox API call, so rate-limit this
  server at your proxy if it is exposed widely.

### Example .env File

Create a `.env` file in the project root:

```env
# Core NetBox Configuration
NETBOX_URL=https://netbox.example.com/
NETBOX_TOKEN=your_api_token_here

# Transport Configuration (optional, defaults to stdio)
TRANSPORT=stdio

# HTTP Transport Settings (only used if TRANSPORT=http)
# HOST=127.0.0.1
# PORT=8000
# Bearer token required on the HTTP endpoint. When unset, the endpoint is unauthenticated.
# MCP_AUTH_TOKEN=a-strong-random-token
# Use each client's own NetBox token instead of NETBOX_TOKEN (HTTP only)
# TOKEN_PASSTHROUGH=true

# Security (optional, defaults to true)
VERIFY_SSL=true

# Plugin Discovery (optional, defaults to false)
# ENABLE_PLUGIN_DISCOVERY=true

# Logging (optional, defaults to INFO)
LOG_LEVEL=INFO
```

### CLI Arguments

All configuration options can be overridden via CLI arguments:

```bash
uv run netbox-mcp-server --help

# Common examples:
uv run netbox-mcp-server --log-level DEBUG --no-verify-ssl  # Development
uv run netbox-mcp-server --transport http --port 9000       # Custom HTTP port
```

## Docker Usage

### Pre-built Image (Docker Hub)

Pre-built multi-arch images (`linux/amd64`, `linux/arm64`) are published to Docker Hub on every tagged release:

```bash
docker pull netboxlabs/netbox-mcp-server:latest
```

Pin to a specific version in production. The `latest` tag tracks the most recent release and can change without notice. See the [releases page](https://github.com/netboxlabs/netbox-mcp-server/releases) for available versions:

```bash
docker pull netboxlabs/netbox-mcp-server:<X.Y.Z>   # exact version
docker pull netboxlabs/netbox-mcp-server:<X.Y>     # latest within a minor
docker pull netboxlabs/netbox-mcp-server:<X>       # latest within a major
```

**Verify image provenance (optional but recommended).** Images are signed with [cosign](https://github.com/sigstore/cosign) (keyless, via GitHub OIDC) and ship with SLSA build provenance:

```bash
cosign verify \
  --certificate-identity-regexp '^https://github.com/netboxlabs/netbox-mcp-server/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  netboxlabs/netbox-mcp-server:<tag>
```

### Standard Docker Image

Build and run the NetBox MCP server in a container:

```bash
# Build the image
docker build -t netbox-mcp-server:latest .

# Run with HTTP transport (required for Docker containers)
docker run --rm \
  -e NETBOX_URL=https://netbox.example.com/ \
  -e NETBOX_TOKEN=<your-api-token> \
  -e TRANSPORT=http \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -e MCP_AUTH_TOKEN=<a-strong-random-token> \
  -p 8000:8000 \
  netbox-mcp-server:latest
```

> **Note:** Docker containers require `TRANSPORT=http` since stdio transport doesn't work in containerized environments.

> **⚠️ Security:** The HTTP transport has **no authentication** unless you set `MCP_AUTH_TOKEN` or use [token passthrough](#per-user-netbox-tokens-token-passthrough). Binding to `HOST=0.0.0.0` exposes read access to all NetBox data your token can see to anyone who can reach the port. Set a strong `MCP_AUTH_TOKEN` (clients then send `Authorization: Bearer <token>`) and terminate TLS at a reverse proxy or gateway before exposing the server to a network. A bearer token sent over plain HTTP can be intercepted, so TLS is required for real deployments.

**Connecting to NetBox on your host machine:**

If your NetBox instance is running on your host machine (not in a container), you need to use `host.docker.internal` instead of `localhost` on macOS and Windows:

```bash
# For NetBox running on host (macOS/Windows)
docker run --rm \
  -e NETBOX_URL=http://host.docker.internal:18000/ \
  -e NETBOX_TOKEN=<your-api-token> \
  -e TRANSPORT=http \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -e MCP_AUTH_TOKEN=<a-strong-random-token> \
  -p 8000:8000 \
  netbox-mcp-server:latest
```

> **Note:** On Linux, you can use `--network host` instead, or use the host's IP address directly.

**With additional configuration options:**

```bash
docker run --rm \
  -e NETBOX_URL=https://netbox.example.com/ \
  -e NETBOX_TOKEN=<your-api-token> \
  -e TRANSPORT=http \
  -e HOST=0.0.0.0 \
  -e MCP_AUTH_TOKEN=<a-strong-random-token> \
  -e LOG_LEVEL=DEBUG \
  -e VERIFY_SSL=false \
  -p 8000:8000 \
  netbox-mcp-server:latest
```

**With per-user NetBox tokens (token passthrough):**

```bash
docker run --rm   -e NETBOX_URL=https://netbox.example.com/   -e TRANSPORT=http   -e HOST=0.0.0.0   -e TOKEN_PASSTHROUGH=true   -e FORWARDED_ALLOW_IPS=<your-proxy-ip>   -p 8000:8000   netbox-mcp-server:latest
```

Leave out `NETBOX_TOKEN` and `MCP_AUTH_TOKEN`; each client sends its own NetBox token.
Set `FORWARDED_ALLOW_IPS` only if a reverse proxy sits in front and you use `FORWARD_CLIENT_IP`.

The server will be accessible at `http://localhost:8000/mcp` for MCP clients. You can connect to it using your preferred method.

## Plugin Object Type Discovery

By default, only core NetBox object types are available. If your NetBox instance has plugins installed (e.g., `netbox-dns`, `netbox-inventory`), you can enable automatic discovery to make their object types available as well.

### Enabling Discovery

Set the `ENABLE_PLUGIN_DISCOVERY` environment variable or use the `--enable-plugin-discovery` CLI flag:

```bash
# Via environment variable
ENABLE_PLUGIN_DISCOVERY=true uv run netbox-mcp-server

# Via CLI flag
uv run netbox-mcp-server --enable-plugin-discovery

# In Claude Desktop config
{
    "mcpServers": {
        "netbox": {
            "command": "uv",
            "args": ["--directory", "/path/to/netbox-mcp-server", "run", "netbox-mcp-server"],
            "env": {
                "NETBOX_URL": "https://netbox.example.com/",
                "NETBOX_TOKEN": "<your-api-token>",
                "ENABLE_PLUGIN_DISCOVERY": "true"
            }
        }
    }
}
```

### How It Works

At startup, the server queries NetBox's `core/object-types` API endpoint (with `extras/object-types` fallback for NetBox < 4.4) to find all installed plugin models that have REST API endpoints. These are merged into the runtime type registry alongside the core types.

Discovered plugin types use the `app_label.model` naming convention (e.g., `netbox_dns.zone`, `netbox_inventory.asset`) and work with all existing tools (`netbox_get_objects`, `netbox_get_object_by_id`, `netbox_search_objects`).

### Requirements

- NetBox 4.2 or later
- API token must have read access to the object-types endpoint
- Plugin models must expose a REST API endpoint to be discovered

### Failure Behavior

If discovery fails for any reason (network error, insufficient permissions, unsupported NetBox version), the server logs a warning and continues with core types only. This ensures the server always starts successfully regardless of discovery outcome.

## Development

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing new features. We encourage filing an issue for discussion first to confirm scope fit.

If your use case needs capabilities outside this project's scope, forking under Apache 2.0 is an actively supported path.

### Local NetBox Testbed

`testbed/` has a Docker Compose file for a local NetBox and a script that creates
sample data plus users with different permissions. The tests in `tests/integration/`
use it to check token passthrough end to end, and are skipped when it is not running.

```bash
docker compose -f testbed/docker-compose.yml up -d --wait   # NetBox 4.7 on http://127.0.0.1:18080
uv run python testbed/seed.py                                # writes testbed/tokens.json
uv run pytest
```

Set `NETBOX_VERSION` (e.g. `NETBOX_VERSION=v4.4.10`) before `up` to test another
NetBox release; run `down -v` first when switching.

## License

This project is licensed under the Apache 2.0 license.  See the LICENSE file for details.
