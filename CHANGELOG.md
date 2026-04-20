# CHANGELOG

<!-- version list -->

## v1.1.0 (2026-04-20)

### Bug Fixes

- Exclude requires-python from Renovate bumps
  ([`e7c7c44`](https://github.com/netboxlabs/netbox-mcp-server/commit/e7c7c4468fd2ee5507bb91e5087d564a06a663bd))

- Gracefully handle fork PR comment permissions
  ([`1c38983`](https://github.com/netboxlabs/netbox-mcp-server/commit/1c38983f0135f84aa50b839992d0b94d59dbdff9))

- Handle bearer authentication for v2 tokens
  ([`4a80e22`](https://github.com/netboxlabs/netbox-mcp-server/commit/4a80e22d0f1f418574369f57d8ebf84bbd0c51ce))

- Handle edge cases in filter parsing for n8n compatibility
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

- Improve n8n MCP ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

- Improve n8n MCP client compatibility with JSON Schema types
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

- Lower minimum supported Python version to 3.11
  ([#66](https://github.com/netboxlabs/netbox-mcp-server/pull/66),
  [`9120b22`](https://github.com/netboxlabs/netbox-mcp-server/commit/9120b22f4dc71787eb8108f1fcaa873dc8c761e7))

- Restore Dockerfile and lockfile from main
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

- Scope requires-python exclusion to pep621 manager only
  ([`e1f0ff5`](https://github.com/netboxlabs/netbox-mcp-server/commit/e1f0ff5c0a4797f8f3f3e67eb8ca6885b99cdbfc))

- Upgrade vulnerable dependencies and Alpine packages
  ([`9d908b0`](https://github.com/netboxlabs/netbox-mcp-server/commit/9d908b0aa0ed7d5b10d0380f38b1bab6d1fe2a17))

- Use string types for n8n MCP client compatibility
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

- **ci**: Add CHANGELOG insertion flag for python-semantic-release v10
  ([#116](https://github.com/netboxlabs/netbox-mcp-server/pull/116),
  [`6543edf`](https://github.com/netboxlabs/netbox-mcp-server/commit/6543edff6f9219f51e9ca005a2d5f81fdd9eb0e9))

- **ci**: Pin GitHub Actions to commit SHAs for security
  ([#67](https://github.com/netboxlabs/netbox-mcp-server/pull/67),
  [`8ce4429`](https://github.com/netboxlabs/netbox-mcp-server/commit/8ce442919ebb9aec374aa8e4e8f54cc5c04a0f39))

- **deps**: Update dependency fastmcp to >=3.2.0,<4
  ([`3178086`](https://github.com/netboxlabs/netbox-mcp-server/commit/317808694cec726883d33693e99270d57ef546ea))

- **deps**: Update non-major python dependencies
  ([`aba4862`](https://github.com/netboxlabs/netbox-mcp-server/commit/aba486257fd3b91d34c2138fae151b06ec431054))

- **docker**: Use Python 3.13 for pre-built wheel availability
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

- **tests**: Update for FastMCP 3.x API (remove .fn from tool calls)
  ([`9331910`](https://github.com/netboxlabs/netbox-mcp-server/commit/93319102f5e2789397d7c4a4e85d1b4dc9ad5715))

### Chores

- Add ruff as linter ([#65](https://github.com/netboxlabs/netbox-mcp-server/pull/65),
  [`56ff780`](https://github.com/netboxlabs/netbox-mcp-server/commit/56ff7807ccc8e2379663f002da70d4157361888f))

- Add ruff as linter ([#62](https://github.com/netboxlabs/netbox-mcp-server/pull/62),
  [`b1d1fe1`](https://github.com/netboxlabs/netbox-mcp-server/commit/b1d1fe1873e17feb398805b636b22696d63d0648))

- Added in full set of linting and applied lints
  ([#65](https://github.com/netboxlabs/netbox-mcp-server/pull/65),
  [`56ff780`](https://github.com/netboxlabs/netbox-mcp-server/commit/56ff7807ccc8e2379663f002da70d4157361888f))

- Moved ruff to dev and added pre-commit hook
  ([#65](https://github.com/netboxlabs/netbox-mcp-server/pull/65),
  [`56ff780`](https://github.com/netboxlabs/netbox-mcp-server/commit/56ff7807ccc8e2379663f002da70d4157361888f))

- Run ruff on repo ([#65](https://github.com/netboxlabs/netbox-mcp-server/pull/65),
  [`56ff780`](https://github.com/netboxlabs/netbox-mcp-server/commit/56ff7807ccc8e2379663f002da70d4157361888f))

- Set rangeStrategy to bump in Renovate config
  ([`7ab23dd`](https://github.com/netboxlabs/netbox-mcp-server/commit/7ab23dd3de1ce234e82bff4e3aa2635f3b6171d4))

- **ci**: Add Ruff and Python matrix in workflow
  ([#66](https://github.com/netboxlabs/netbox-mcp-server/pull/66),
  [`9120b22`](https://github.com/netboxlabs/netbox-mcp-server/commit/9120b22f4dc71787eb8108f1fcaa873dc8c761e7))

- **deps**: Bump cryptography in the uv group across 1 directory
  ([#110](https://github.com/netboxlabs/netbox-mcp-server/pull/110),
  [`a740f5a`](https://github.com/netboxlabs/netbox-mcp-server/commit/a740f5a6600f43d8db3a32fc6bae251abe3b1563))

- **deps**: Bump fastmcp to 2.14.x to address security concerns
  ([#60](https://github.com/netboxlabs/netbox-mcp-server/pull/60),
  [`bb32fe3`](https://github.com/netboxlabs/netbox-mcp-server/commit/bb32fe3f3e51b5c422bba7d8eb47b5a71336043a))

- **deps**: Bump filelock in the uv group across 1 directory
  ([#71](https://github.com/netboxlabs/netbox-mcp-server/pull/71),
  [`14ec2fe`](https://github.com/netboxlabs/netbox-mcp-server/commit/14ec2fe7fb7d1f998eb2bfc50aaa67382447cdd5))

- **deps**: Bump python-multipart in the uv group across 1 directory
  ([#70](https://github.com/netboxlabs/netbox-mcp-server/pull/70),
  [`9137450`](https://github.com/netboxlabs/netbox-mcp-server/commit/91374504f352f593028d97ba5c697dc68b8e478a))

- **deps**: Bump virtualenv in the uv group across 1 directory
  ([#68](https://github.com/netboxlabs/netbox-mcp-server/pull/68),
  [`9df2ced`](https://github.com/netboxlabs/netbox-mcp-server/commit/9df2ced11b13b9b100f5ad568cfcabce36d5e602))

- **deps**: Pin GitHub Actions digests in Renovate config
  ([`7920fe7`](https://github.com/netboxlabs/netbox-mcp-server/commit/7920fe7e563fb2b300ff53a6ceb45280e090b0d8))

- **deps**: Remove ruff dependency from main project deps and lock files
  ([`a128ddd`](https://github.com/netboxlabs/netbox-mcp-server/commit/a128ddd5a83c46bef0b79a3172dcc57950bfadb0))

- **deps**: Update actions/checkout action to v6
  ([`8e1088a`](https://github.com/netboxlabs/netbox-mcp-server/commit/8e1088a4be97bd0695b6836eddf4189a3246dc16))

- **deps**: Update actions/setup-python action to v6
  ([`0bc4c1a`](https://github.com/netboxlabs/netbox-mcp-server/commit/0bc4c1a1248274ed01fc004f6aa89018179898e8))

- **deps**: Update astral-sh/setup-uv action to v8
  ([`965ab93`](https://github.com/netboxlabs/netbox-mcp-server/commit/965ab93fad257c4058a895a0c628b2d464ba0ec0))

- **deps**: Update dependencies and Python support
  ([#63](https://github.com/netboxlabs/netbox-mcp-server/pull/63),
  [`92a923a`](https://github.com/netboxlabs/netbox-mcp-server/commit/92a923a3727bfd61c808f605addce979a8b9533a))

- **deps**: Update dependency fastmcp to v3.2.0 [security]
  ([`f165558`](https://github.com/netboxlabs/netbox-mcp-server/commit/f1655580980140370cd241c0565618e294f55601))

- **deps**: Update dependency pytest to v9.0.3 [security]
  ([#113](https://github.com/netboxlabs/netbox-mcp-server/pull/113),
  [`48bb7a6`](https://github.com/netboxlabs/netbox-mcp-server/commit/48bb7a6e2382679f05d774d20c97682c9981e240))

- **deps**: Update docker/build-push-action action to v7
  ([`c4cd483`](https://github.com/netboxlabs/netbox-mcp-server/commit/c4cd48319b1a39776b9661664284505d5c773c04))

- **deps**: Update docker/login-action action to v4
  ([`c975c32`](https://github.com/netboxlabs/netbox-mcp-server/commit/c975c324c54c981a0ef98b3e5e57ea9dd35603b0))

- **deps**: Update docker/metadata-action action to v6
  ([`f2208db`](https://github.com/netboxlabs/netbox-mcp-server/commit/f2208dbf856990171f4777f71868f74f6daae465))

- **deps**: Update docker/setup-buildx-action action to v4
  ([`be31cc8`](https://github.com/netboxlabs/netbox-mcp-server/commit/be31cc8ceeb418cfea863b3a55aa75a3d88cdfd6))

- **deps**: Update docker/setup-qemu-action action to v4
  ([`628dd4a`](https://github.com/netboxlabs/netbox-mcp-server/commit/628dd4aec141fe2727ca20e045a594c350d6227f))

- **deps**: Update multiple Python dependencies
  ([`1c20ac6`](https://github.com/netboxlabs/netbox-mcp-server/commit/1c20ac60722312e13b7a4c45ca557238d9e7116a))

- **deps**: Update non-major github actions
  ([#109](https://github.com/netboxlabs/netbox-mcp-server/pull/109),
  [`480795f`](https://github.com/netboxlabs/netbox-mcp-server/commit/480795fc89a3d8b2edebff69a9a5999cd20ecd3c))

- **deps**: Update non-major github actions
  ([`d40d861`](https://github.com/netboxlabs/netbox-mcp-server/commit/d40d86102a4de56f38b0d8ab00c4824923b3a666))

- **deps**: Update ruff-pre-commit to v0.15.2
  ([`308f9a0`](https://github.com/netboxlabs/netbox-mcp-server/commit/308f9a0ab8cbddf6f7cf633aeb58f9d246e562ed))

- **deps**: Upgrade FastMCP 3
  ([`ece2bef`](https://github.com/netboxlabs/netbox-mcp-server/commit/ece2bef0565cd300d07e1873160b86193c5593c6))

- **docker**: Update Python base image and enhance metadata
  ([#64](https://github.com/netboxlabs/netbox-mcp-server/pull/64),
  [`a29f43b`](https://github.com/netboxlabs/netbox-mcp-server/commit/a29f43b335b7504009fe6b75d9ccc96db59e1748))

### Continuous Integration

- Add workflow for multi-arch Docker build and publish
  ([#64](https://github.com/netboxlabs/netbox-mcp-server/pull/64),
  [`a29f43b`](https://github.com/netboxlabs/netbox-mcp-server/commit/a29f43b335b7504009fe6b75d9ccc96db59e1748))

- Simplify release workflows ([#114](https://github.com/netboxlabs/netbox-mcp-server/pull/114),
  [`f805f72`](https://github.com/netboxlabs/netbox-mcp-server/commit/f805f72f3ab5296053d56b266d39b60467339e71))

- Switch release workflow to PR-based flow
  ([#114](https://github.com/netboxlabs/netbox-mcp-server/pull/114),
  [`f805f72`](https://github.com/netboxlabs/netbox-mcp-server/commit/f805f72f3ab5296053d56b266d39b60467339e71))

### Documentation

- **server**: Explain n8n float-type workaround and add MCP-boundary tests
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

### Features

- Add container scanning and daily rescan workflows
  ([`478a52f`](https://github.com/netboxlabs/netbox-mcp-server/commit/478a52f5d372bc7c1ee6a4b50c6823436d713b21))

- Add NetBox v4.2-v4.5+ compatibility
  ([#69](https://github.com/netboxlabs/netbox-mcp-server/pull/69),
  [`c2538cc`](https://github.com/netboxlabs/netbox-mcp-server/commit/c2538cc9579a76e31a5fd87a472194207fbcdea4))

- Add Source column to vulnerability scan tables
  ([`7f51672`](https://github.com/netboxlabs/netbox-mcp-server/commit/7f516724ce1d96d262dca55000f85dc120ec7fa2))

### Refactoring

- Remove requests dependency and migrate to httpx
  ([`895a477`](https://github.com/netboxlabs/netbox-mcp-server/commit/895a47707a1bcacc41341e966a68db3c078eaf31))

- Simplify parameter parsing with shared helper and add tests
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))

### Testing

- Add comprehensive tests for endpoint fallback mechanism
  ([#69](https://github.com/netboxlabs/netbox-mcp-server/pull/69),
  [`c2538cc`](https://github.com/netboxlabs/netbox-mcp-server/commit/c2538cc9579a76e31a5fd87a472194207fbcdea4))

- Update ordering tests for simplified string-only parameter
  ([#61](https://github.com/netboxlabs/netbox-mcp-server/pull/61),
  [`d6f4c12`](https://github.com/netboxlabs/netbox-mcp-server/commit/d6f4c12aa111a1f36cc5dfd718e100f6439d6b58))


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
