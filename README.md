# NetBox MCP Server

This is a simple read-only [Model Context Protocol](https://modelcontextprotocol.io/) server for NetBox.  It enables you to interact with your data in NetBox directly via LLMs that support MCP.

## Tools

| Tool | Description |
|------|-------------|
| get_objects | Retrieves NetBox core objects based on their type and filters |
| get_object_by_id | Gets detailed information about a specific NetBox object by its ID |
| get_changelogs | Retrieves change history records (audit trail) based on filters |

> Note: the set of supported object types is explicitly defined and limited to the core NetBox objects for now, and won't work with object types from plugins.

## Usage

1. Create a read-only API token in NetBox with sufficient permissions for the tool to access the data you want to make available via MCP.

2. Install dependencies:

    ```bash
    # Using UV (recommended)
    uv sync

    # Or using pip
    pip install -e .
    ```

3. Verify the server can run: `NETBOX_URL=https://netbox.example.com/ NETBOX_TOKEN=<your-api-token> uv run server.py`

4. Add the MCP server to your LLM client. See below for some examples with Claude.

### Claude Code

#### Stdio Transport (Default)

Add the server using the `claude mcp add` command:

```bash
claude mcp add --transport stdio netbox \
  --env NETBOX_URL=https://netbox.example.com/ \
  --env NETBOX_TOKEN=<your-api-token> \
  -- uv --directory /path/to/netbox-mcp-server run server.py
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
uv run server.py
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
                "server.py"
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
devices = netbox_get_objects('devices', {'site': 'datacenter-1'})

# With fields: ~500 tokens (90% reduction)
devices = netbox_get_objects(
    'devices',
    {'site': 'datacenter-1'},
    fields=['id', 'name', 'status', 'site']
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
| `NETBOX_TOKEN` | String | - | Yes | API token for authentication |
| `TRANSPORT` | `stdio` \| `http` | `stdio` | No | MCP transport protocol |
| `HOST` | String | `127.0.0.1` | If HTTP | Host address for HTTP server |
| `PORT` | Integer | `8000` | If HTTP | Port for HTTP server |
| `VERIFY_SSL` | Boolean | `true` | No | Whether to verify SSL certificates |
| `LOG_LEVEL` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL` | `INFO` | No | Logging verbosity |

### Transport Examples

#### Stdio Transport (Claude Desktop/Code)

For local Claude Desktop or Claude Code usage with stdio transport:

```json
{
    "mcpServers": {
        "netbox": {
            "command": "uv",
            "args": ["--directory", "/path/to/netbox-mcp-server", "run", "server.py"],
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

uv run server.py

# Or using CLI arguments
uv run server.py \
  --netbox-url https://netbox.example.com/ \
  --netbox-token <your-api-token> \
  --transport http \
  --host 127.0.0.1 \
  --port 8000
```

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

# Security (optional, defaults to true)
VERIFY_SSL=true

# Logging (optional, defaults to INFO)
LOG_LEVEL=INFO
```

### CLI Arguments

All configuration options can be overridden via CLI arguments:

```bash
uv run server.py --help

# Common examples:
uv run server.py --log-level DEBUG --no-verify-ssl  # Development
uv run server.py --transport http --port 9000       # Custom HTTP port
```

## Development

Contributions are welcome!  Please open an issue or submit a PR.

## License

This project is licensed under the Apache 2.0 license.  See the LICENSE file for details.
