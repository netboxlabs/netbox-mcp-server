# NetBox MCP Server (Golang)

This is a Golang implementation of the NetBox MCP (Model Context Protocol) Server, converted from the original Python implementation.

## Overview

The NetBox MCP Server provides a read-only interface to NetBox through the Model Context Protocol. This Golang version offers the same functionality as the Python version with improved performance and easier deployment as a single binary.

## Features

- **Read-only NetBox API access** via MCP tools
- **Object querying** with filtering, pagination, and field selection
- **Global search** across multiple NetBox object types
- **Changelog access** for tracking changes
- **Configurable via** environment variables or CLI arguments
- **Support for** both stdio and HTTP transports (stdio recommended)

## Building

```bash
# Build the binary
go build -o netbox-mcp-server

# Or install directly
go install
```

## Configuration

Configuration follows this precedence (highest to lowest):
1. Command-line arguments
2. Environment variables
3. Default values

### Required Settings

- `NETBOX_URL` / `--netbox-url`: Base URL of your NetBox instance (e.g., https://netbox.example.com/)
- `NETBOX_TOKEN` / `--netbox-token`: API token for authentication

### Optional Settings

- `TRANSPORT` / `--transport`: Transport protocol (`stdio` or `http`, default: `stdio`)
- `HOST` / `--host`: Host for HTTP server (default: `127.0.0.1`)
- `PORT` / `--port`: Port for HTTP server (default: `8000`)
- `VERIFY_SSL` / `--verify-ssl` / `--no-verify-ssl`: Verify SSL certificates (default: `true`)
- `LOG_LEVEL` / `--log-level`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, default: `INFO`)

## Usage

### Using Environment Variables

```bash
export NETBOX_URL="https://netbox.example.com"
export NETBOX_TOKEN="your_api_token_here"
./netbox-mcp-server
```

### Using Command-Line Arguments

```bash
./netbox-mcp-server --netbox-url https://netbox.example.com --netbox-token your_api_token_here
```

### Example with .env file

The application automatically loads environment variables from a `.env` file if it exists in:
- The current directory (`.env`)
- The parent directory (`../.env`)
- Your home directory (`$HOME/.env`)

Create a `.env` file (you can copy `.env.example`):

```bash
cp .env.example .env
# Edit .env with your values
```

Example `.env` file:

```env
NETBOX_URL=https://netbox.example.com
NETBOX_TOKEN=your_api_token_here
VERIFY_SSL=true
LOG_LEVEL=INFO
```

Then simply run:

```bash
./netbox-mcp-server
```

The `.env` file will be automatically loaded!

## Available MCP Tools

### 1. `netbox_get_objects`

Get objects from NetBox based on their type and filters.

**Parameters:**
- `object_type` (string, required): NetBox object type (e.g., "dcim.device", "ipam.ipaddress")
- `filters` (object, required): Dictionary of filters to apply
- `fields` (array, optional): List of specific fields to return
- `brief` (boolean, optional): Return minimal representation
- `limit` (integer, optional): Maximum results to return (default: 5, max: 100)
- `offset` (integer, optional): Skip this many results for pagination
- `ordering` (string/array, optional): Fields for sort order

### 2. `netbox_get_object_by_id`

Get detailed information about a specific NetBox object by its ID.

**Parameters:**
- `object_type` (string, required): NetBox object type
- `object_id` (integer, required): The numeric ID of the object
- `fields` (array, optional): List of specific fields to return
- `brief` (boolean, optional): Return minimal representation

### 3. `netbox_search_objects`

Perform global search across NetBox infrastructure.

**Parameters:**
- `query` (string, required): Search term
- `object_types` (array, optional): Limit search to specific types
- `fields` (array, optional): List of specific fields to return
- `limit` (integer, optional): Max results per type (default: 5, max: 100)

### 4. `netbox_get_changelogs`

Get object change records (changelogs) from NetBox.

**Parameters:**
- `filters` (object, required): Dictionary of filters to apply

## Supported Object Types

The server supports all NetBox object types including:

- **Circuits**: circuit, circuittype, provider, etc.
- **DCIM**: device, site, rack, interface, cable, etc.
- **IPAM**: ipaddress, prefix, vlan, vrf, aggregate, etc.
- **Virtualization**: virtualmachine, cluster, etc.
- **Tenancy**: tenant, contact, etc.
- **Extras**: tag, customfield, webhook, etc.
- And many more...

For a complete list, see `types.go`.

## Development

### Project Structure

```
golang/
├── main.go       # Main entry point and MCP tools
├── client.go     # NetBox REST API client
├── config.go     # Configuration management
├── types.go      # NetBox object type definitions
├── go.mod        # Go module dependencies
├── go.sum        # Dependency checksums
└── README.md     # This file
```

### Dependencies

- [mcp-go](https://github.com/mark3labs/mcp-go) - Go implementation of Model Context Protocol

## Differences from Python Version

1. **Single Binary**: The Go version compiles to a single executable with no runtime dependencies
2. **Performance**: Generally faster startup time and lower memory footprint
3. **Type Safety**: Compile-time type checking for better reliability
4. **Simplified Deployment**: No Python virtual environment or package management needed

## Security Notes

- **SSL Verification**: Always keep SSL verification enabled in production (`VERIFY_SSL=true`)
- **Token Security**: Never commit your NetBox token to version control
- **Network Exposure**: Be careful when binding HTTP transport to non-localhost addresses

## License

Same as the original Python implementation - see LICENSE file in the parent directory.

## Troubleshooting

### SSL Certificate Errors

If you encounter SSL certificate errors with a self-signed certificate:

```bash
./netbox-mcp-server --netbox-url https://netbox.example.com --netbox-token YOUR_TOKEN --no-verify-ssl
```

**Warning**: Only use `--no-verify-ssl` in development/testing environments.

### Connection Refused

Ensure your NetBox instance is accessible and the URL is correct:

```bash
curl -H "Authorization: Token YOUR_TOKEN" https://netbox.example.com/api/
```

## Contributing

Contributions are welcome! Please ensure your code:
- Follows Go conventions and formatting (`go fmt`)
- Includes appropriate error handling
- Maintains compatibility with the Python version's MCP interface
