# CHANGELOG

## v1.0.0 (2025-10-31)

### 🚨 BREAKING CHANGES

**Simpler installation and execution.** The server now uses a standard Python package layout with a dedicated command. You'll need to update your configuration:

- **Command change**: `uv run server.py` → `uv run netbox-mcp-server`
- **Claude Desktop/Code**: Update `args` to use `netbox-mcp-server` instead of `server.py`
- **Docker**: Rebuild images (CMD updated to use new entry point)

See [README.md](README.md) for updated configuration examples.

### What's New

#### Enhanced Search & Querying

- **Global search across object types**: New `netbox_search_objects` tool lets you search for devices, sites, IP addresses, and more in a single query
- **Selective field filtering**: Reduce token usage by requesting only the fields you need (e.g., just `name` and `status` instead of complete objects)
- **Smarter pagination**: Control result set sizes with `limit` and `offset` parameters, plus automatic `count`, `next`, and `previous` metadata for navigating large datasets
- **Custom result ordering**: Sort results by any field with the `ordering` parameter (e.g., `-name` for reverse alphabetical, or `['site', '-id']` for multi-field sorting)
- **Better error messages**: Input validation now catches unsupported filter patterns before they reach the NetBox API

#### Easier Deployment & Configuration

- **Simple command**: Run with `netbox-mcp-server` instead of `python server.py`
- **Docker support**: Official Dockerfile for containerized deployments
- **Flexible configuration**: Pass settings via environment variables or command-line arguments
- **Configurable logging**: Set `LOG_LEVEL` environment variable to control verbosity (default: INFO)

#### Security & Reliability

- **Security update**: Upgraded to FastMCP 2.13 to address security vulnerability
- **Production-ready**: Comprehensive CI/CD pipeline with automated testing against live NetBox instances

---

## v0.1.0 (2025-10-14)

- Initial Release
