# NetBox MCP Server

MCP server for NetBox with full CRUD operations support.

## Installation

```bash
go build -o netbox-mcp-server
```

## Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your NetBox credentials:

```
NETBOX_URL=https://your-netbox-instance.com
NETBOX_TOKEN=your_api_token
```

## Usage

### Run with stdio transport (for Claude Desktop)

```bash
./netbox-mcp-server
```

### Run with HTTP transport

```env
TRANSPORT=http
HOST=0.0.0.0
PORT=8000
```

```bash
./netbox-mcp-server
```

Server will be available at `http://localhost:8000/mcp`

## MCP Tools

- `netbox_get_objects` - Query objects with filters
- `netbox_get_object_by_id` - Get specific object
- `netbox_search_objects` - Global search
- `netbox_get_changelogs` - Get change history
- `netbox_create_object` - Create new object
- `netbox_update_object` - Update existing object
- `netbox_delete_object` - Delete object

## Claude Desktop Configuration

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "netbox": {
      "command": "/path/to/netbox-mcp-server",
      "env": {
        "NETBOX_URL": "https://your-netbox.com",
        "NETBOX_TOKEN": "your_token"
      }
    }
  }
}
```
