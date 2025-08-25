# NetBox MCP Server

This is a simple read-only [Model Context Protocol](https://modelcontextprotocol.io/) server for NetBox. It enables you to interact with your data in NetBox directly via LLMs that support MCP.

The server supports both **stdio** (for local/CLI usage) and **streamable-http** (for web services) transport protocols, with flexible configuration via environment variables or CLI arguments.

## Tools

| Tool | Description |
|------|-------------|
| get_objects | Retrieves NetBox core objects based on their type and filters |
| get_object_by_id | Gets detailed information about a specific NetBox object by its ID |
| get_changelogs | Retrieves change history records (audit trail) based on filters |

> Note: the set of supported object types is explicitly defined and limited to the core NetBox objects for now, and won't work with object types from plugins.

## Configuration

The server can be configured using either a `.env` file or CLI arguments. CLI arguments take precedence over `.env` file values.

### Environment Variables (.env file)

Create a `.env` file in the project directory (see `env.sample` for reference):

```bash
# NetBox connection settings
NETBOX_URL=https://netbox.example.com/
NETBOX_TOKEN=your-api-token-here

# MCP server settings
MCP_TRANSPORT=stdio                    # stdio or streamable-http
MCP_SERVER_HOST=localhost              # Only used for streamable-http
MCP_SERVER_PORT=8000                   # Only used for streamable-http

# Optional settings
LOG_LEVEL=INFO                         # DEBUG, INFO, WARNING, ERROR
VERIFY_SSL=true                        # SSL certificate verification
```

### CLI Arguments

All configuration options can be overridden via command line:

```bash
python3 server.py --help

# Examples:
python3 server.py --netbox-url https://netbox.example.com/ --netbox-token your-token
python3 server.py --transport streamable-http --host 0.0.0.0 --port 8080
python3 server.py --log-level DEBUG --no-verify-ssl
```

## Usage

### Prerequisites

1. Create a read-only API token in NetBox with sufficient permissions for the tool to access the data you want to make available via MCP.

2. Install dependencies: `pip install -r requirements.txt` or `uv add -r requirements.txt`

### Running the Server

#### Option 1: Using .env file (Recommended)

1. Copy `env.sample` to `.env` and configure your settings
2. Run the server: `python3 server.py`

#### Option 2: Using CLI arguments

```bash
python3 server.py --netbox-url https://netbox.example.com/ --netbox-token your-token
```

#### Option 3: Using environment variables

```bash
NETBOX_URL=https://netbox.example.com/ NETBOX_TOKEN=your-token python3 server.py
```

### Transport Protocols

#### stdio Transport (Default)
For local usage with LLM clients like Claude Desktop:

```bash
python3 server.py --transport stdio
```

#### streamable-http Transport
For web services and remote access:

```bash
python3 server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

### LLM Client Configuration

#### For stdio transport (Claude Desktop example):

```json
{
  "mcpServers": {
    "netbox": {
      "command": "python3",
      "args": ["/path/to/netbox-mcp-server/server.py"],
      "env": {
        "NETBOX_URL": "https://netbox.example.com/",
        "NETBOX_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

Or using uv:
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
        "NETBOX_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

#### For streamable-http transport

When using streamable-http transport, the server runs as a web service. Configure your MCP client to connect to the HTTP endpoint:

```json
{
  "mcpServers": {
    "netbox": {
      "url": "http://localhost:8000"
    }
  }
}
```

> **Note**: On Windows, use full, escaped paths such as `C:\\Users\\myuser\\.local\\bin\\uv` and `C:\\Users\\myuser\\netbox-mcp-server`. 
> For detailed troubleshooting, consult the [MCP quickstart](https://modelcontextprotocol.io/quickstart/user).

### Example Usage

Once configured, you can use the tools in your LLM client:

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

## Debugging and Logging

The server includes comprehensive logging to help troubleshoot issues:

### Enable Debug Logging

```bash
# Via .env file
echo "LOG_LEVEL=DEBUG" >> .env

# Via CLI argument
python3 server.py --log-level DEBUG

# Via environment variable
LOG_LEVEL=DEBUG python3 server.py
```

### Debug Output

With debug logging enabled, you'll see detailed information about:
- Configuration loading and validation
- NetBox API requests and responses
- MCP tool calls and parameters
- HTTP request/response details
- Error stack traces

### Common Issues

**"No Host Supplied" Error**: This typically indicates a networking or SSL issue. Try:
```bash
python3 server.py --no-verify-ssl --log-level DEBUG
```

**Connection Refused**: Verify your NetBox URL and network connectivity:
```bash
curl -H "Authorization: Token your-token" https://your-netbox-url/api/
```

## Development

Contributions are welcome! Please open an issue or submit a PR.

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `env.sample` to `.env` and configure
4. Run tests: `python3 -m pytest` (when available)
5. Run the server: `python3 server.py --log-level DEBUG`

## License

This project is licensed under the Apache 2.0 license.  See the LICENSE file for details.
