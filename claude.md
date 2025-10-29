# NetBox MCP Server

## Core Concept

A read-only [Model Context Protocol](https://modelcontextprotocol.io/) server that enables LLMs to interact with NetBox infrastructure data. Built with FastMCP and designed for use by NetBox operators.

**Your role**: Help contributors design and implement features following open-source best practices. Ask clarifying questions and challenge assumptions when needed.

## Tech Stack

- **Python**: 3.13.x (3.14+ not supported)
- **Package Manager**: uv
- **MCP Framework**: FastMCP 2.12.x
- **HTTP Client**: requests + httpx
- **NetBox API**: REST API via token authentication

## Project Structure

```text
.
├── src/
│   └── netbox_mcp_server/
│       ├── __init__.py          # Package initialization with __version__
│       ├── __main__.py          # Entry point for module execution
│       ├── server.py            # Main MCP server with tool definitions
│       ├── netbox_client.py     # NetBox REST API client abstraction
│       ├── netbox_types.py      # NetBox object type mappings
│       └── config.py            # Settings and logging configuration
├── tests/                        # Test suite
├── .github/workflows/            # CI/CD automation
├── pyproject.toml               # Dependencies and project metadata
├── README.md                    # User-facing documentation
├── CHANGELOG.md                 # Auto-generated release notes
└── LICENSE                      # Apache 2.0 license
```

**Design Pattern**: Clean separation between MCP server logic (`server.py`) and NetBox API client (`netbox_client.py`) to support future plugin-based implementations.

## Common Commands

```bash
# Install dependencies (ONLY use uv, NEVER pip)
uv sync

# Run the server locally (requires env vars)
NETBOX_URL=https://netbox.example.com/ NETBOX_TOKEN=<token> uv run server.py

# Add to Claude Code (for development/testing)
claude mcp add --transport stdio netbox \
  --env NETBOX_URL=https://netbox.example.com/ \
  --env NETBOX_TOKEN=<token> \
  -- uv --directory /path/to/netbox-mcp-server run server.py
```

## Development Philosophy

- **Simplicity over cleverness**: Write simple, straightforward code that's easy to understand
- **Readability first**: Code is read 10x more than it's written - optimize for the reader
- **Build iteratively**: Start with minimal functionality, verify it works, then add complexity
- **DRY (Don't Repeat Yourself)**: Extract common patterns, but only after the third occurrence
- **Early returns**: Use early returns to avoid nested conditions and improve readability
- **Descriptive names**: Use clear variable and function names that explain intent
- **Less code = less debt**: Minimize code footprint; the best code is no code at all
- **Test frequently**: Test with realistic inputs and validate outputs as you build
- **Functional where clear**: Use functional, stateless approaches when they improve clarity
- **Clean core logic**: Keep business logic clean; push implementation details to the edges

## Code Standards

### Python Conventions

- **Type hints required**: All function parameters and return types must be annotated
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Line length**: 88 characters maximum (Ruff/Black standard)
- **Naming conventions**:
  - Functions and variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **String formatting**: Use f-strings for string formatting
- **Imports**: Absolute imports preferred, group standard library → third-party → local
- **Error handling**: Never use bare `except` - specify exception types (e.g., `except ValueError:`); raise descriptive exceptions and let FastMCP handle error responses

### Code Style

```python
# ✅ Good: Clear types, descriptive names, proper error handling, comprehensive docstrings
def netbox_get_objects(object_type: str, filters: dict) -> list[dict]:
    """Get objects from NetBox based on their type and filters.

    Args:
        object_type: String representing the NetBox object type (e.g. "devices")
        filters: Dictionary of filters to apply to the API call

    Returns:
        Either a single object dict or a list of object dicts
    """
    if object_type not in NETBOX_OBJECT_TYPES:
        valid_types = "\n".join(f"- {t}" for t in sorted(NETBOX_OBJECT_TYPES.keys()))
        raise ValueError(f"Invalid object_type. Must be one of:\n{valid_types}")
    return netbox.get(NETBOX_OBJECT_TYPES[object_type], params=filters)

# ❌ Avoid: Missing types, generic names, silent failures, no docstrings
def get_stuff(t, f):
    try:
        return netbox.get(types[t], params=f)
    except:
        return None
```

### Architecture Patterns

- **Abstraction layer**: `NetBoxClientBase` defines interface for future ORM implementation
- **Read-only by design**: Only GET operations exposed; no create/update/delete tools
- **Environment-based config**: All secrets via environment variables, never hardcoded
- **Explicit object mapping**: `NETBOX_OBJECT_TYPES` dictionary maintains allowed types

## Tool Development Guidelines

### Adding New Tools

1. Define tool function with `@mcp.tool` decorator
2. Include comprehensive docstring with args, return types, and examples
3. Validate inputs before calling NetBox client
4. Return structured data (dict or list); let FastMCP handle serialization

### Tool Naming Convention

- Use `netbox_` prefix for all tools (e.g., `netbox_get_objects`)
- Use descriptive action verbs: `get`, `list`, `search`
- Keep names intuitive for LLM consumption

### Supported NetBox Objects

Tools support core NetBox object types across these modules:

- **DCIM**: devices, sites, racks, interfaces, cables, etc.
- **IPAM**: IP addresses, prefixes, VLANs, VRFs, ASNs
- **Circuits**: circuits, providers, circuit terminations
- **Virtualization**: VMs, clusters, VM interfaces
- **Tenancy**: tenants, contacts, contact groups
- **VPN**: tunnels, IPsec policies, IKE policies
- **Wireless**: wireless LANs, wireless links
- **Extras**: config contexts, custom fields, export templates, image attachments, jobs, saved filters, scripts, tags, webhooks

See `NETBOX_OBJECT_TYPES` in `server.py` for complete list.

## Environment Variables

- `NETBOX_URL`: Base URL of NetBox instance (e.g., `https://netbox.example.com/`)
- `NETBOX_TOKEN`: Read-only API token with appropriate permissions
- `LOG_LEVEL`: Logging verbosity (default: `INFO`, options: `DEBUG`, `WARNING`, `ERROR`)

## Security Considerations

- **Read-only tokens**: Always use read-only API tokens with minimal required permissions
- **No credential storage**: Tokens passed via environment, never stored or logged
- **SSL verification**: Enabled by default in REST client
- **No plugin support**: Deliberately excludes plugin object types to limit attack surface
- **Open source**: All code auditable; report security issues per SECURITY.md

## Testing Philosophy

Currently no automated test suite. When adding tests:

- Test tool behavior with real NetBox instance (Docker-based test environment)
- Mock external NetBox API calls only when necessary
- Validate error handling (invalid object types, missing credentials, API errors)
- Test pagination handling for large result sets

## Do Not

### Package Management

- ❌ **NEVER use pip** - Only use `uv` for package management
- ❌ **NEVER use `uv pip install`** - This is forbidden; use `uv add` instead
- ❌ **NEVER use `@latest` syntax** - Specify versions explicitly or let uv manage them

### Code Quality

- ❌ Add write operations (create/update/delete) without explicit project maintainer approval
- ❌ Add support for plugin object types (scope limited to core NetBox)
- ❌ Hardcode credentials or NetBox URLs
- ❌ Bypass the `NetBoxClientBase` abstraction
- ❌ Remove type hints or comprehensive docstrings
- ❌ Use print statements (use proper logging via `LOG_LEVEL`)

## Open Source Best Practices

- **Professional communication**: Be courteous and constructive
- **Documentation is mandatory**: A user-facing feature doesn't exist unless documented in README.md
- **Licensing**: Apache 2.0; ensure all contributions are compatible
- **Issue-driven development**: Reference issues in commits and PRs

### Communication Style

- **Be direct**: State what things ARE (avoid "This isn't X, it's Y" constructions)
- **Be brief**: Optimize for reader comprehension, not writer expression
- **Be clear**: Avoid defensive writing patterns and ambiguous language

## Git Workflow

### Branch Strategy

- **Always use feature branches** - NEVER commit directly to `main`
- **Branch naming**: Use descriptive names with prefixes:
  - `fix/auth-timeout` - Bug fixes
  - `feat/api-pagination` - New features
  - `chore/ruff-fixes` - Maintenance tasks
- **One logical change per branch** - Simplifies review and rollback

### Commit Practices

- **Conventional commit format** (preferred):

  ```bash
  type(scope): short description

  Examples:
  feat(tools): add netbox_search_objects tool
  fix(client): handle pagination correctly
  chore(deps): upgrade fastmcp to 2.13.0
  ```

- **Commit trailers** for attribution:

  ```bash
  # Link to GitHub issue
  git commit --trailer "Github-Issue:#123"

  # Credit bug reporter
  git commit --trailer "Reported-by:Jane Doe"
  ```

- **Make atomic commits** - One logical change per commit
- **Keep granular history** on feature branch; squash only when merging to `main`

### Pull Request Workflow

1. **Create or reference an issue** before starting work
2. **Create feature branch**: `git checkout -b feat/issue-123-description`
3. **Commit in small, logical increments** as you work
4. **Push and open draft PR early** for visibility
5. **Convert to ready PR** when functionally complete and tests pass
6. **Wait for reviews** and address feedback
7. **Merge after approval** and CI checks pass

### PR Guidelines

**PR Description Format**:

- 1-2 paragraphs: State the problem/need and your solution
- Include a focused code example if adding new functionality
- Keep it concise for minor fixes (1-2 sentences is fine)

**What to Avoid**:

- Bullet-point summaries of every file changed
- Marketing language or excessive justification
- Repeating what the code diff already shows

**What to Include**:

- Link related issues: `Fixes #123` or `Relates to #456`
- Why this change matters (not just what changed)

### Critical Rules

- ❌ **NEVER commit directly to `main`** - Always use feature branches
- ✅ **DO keep commits professional and concise** and focused on the change


## Decision Heuristics

### When to Add a New Tool

✅ **Add if**:

- Exposes core NetBox functionality not currently accessible
- Has clear use case for LLM-driven queries
- Maintains read-only contract
- Follows existing tool patterns

❌ **Don't add if**:

- Duplicates existing tool functionality
- Requires write operations
- Only benefits niche use cases
- Adds complexity without clear value

### When to Modify the Client Abstraction

Only modify `NetBoxClientBase` if:

- Planning to add plugin-based ORM implementation
- All CRUD methods must remain in sync
- Changes must not break REST implementation

### Progressive Complexity

**Level 1 (New Contributors)**: Add tools, fix bugs, improve documentation

**Level 2 (Maintainers)**: Modify client abstraction, add new object type categories

**Level 3 (Core Team)**: Architectural changes, security-sensitive code

## Common Patterns

### Querying NetBox Objects

These examples show how LLMs interact with MCP tools (conceptual format):

```python
# Get all devices in a site
mcp_tool("netbox_get_objects", {
    "object_type": "devices",
    "filters": {"site": "equinix-dc14"}
})

# Get specific device by ID
mcp_tool("netbox_get_object_by_id", {
    "object_type": "devices",
    "object_id": 123
})

# Find recent changes
mcp_tool("netbox_get_changelogs", {
    "filters": {
        "action": "update",
        "time_after": "2025-01-01T00:00:00Z"
    }
})
```

## Troubleshooting

**"NETBOX_URL and NETBOX_TOKEN environment variables must be set"**
→ Set environment variables before running server

**"Invalid object_type"**
→ Check `NETBOX_OBJECT_TYPES` dictionary for supported types
→ Plugin object types are not supported

**"Connection refused" or timeout**
→ Verify NETBOX_URL is accessible and includes protocol (https://)
→ Check firewall rules and network connectivity

**"Authentication failed"**
→ Verify API token is valid and not expired
→ Ensure token has read permissions for requested objects

## References

- [NetBox API Documentation](https://docs.netbox.dev/en/stable/integrations/rest-api/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Project README](./README.md) - User-facing setup and usage
- [Security Policy](./SECURITY.md) - Vulnerability reporting
