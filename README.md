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

## Development

Contributions are welcome!  Please open an issue or submit a PR.

## License

This project is licensed under the Apache 2.0 license.  See the LICENSE file for details.
