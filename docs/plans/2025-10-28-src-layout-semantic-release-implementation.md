# src/ Layout + Semantic Release Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure NetBox MCP server to use Python src/ layout, add python-semantic-release automation, and establish CI/CD pipelines for v1.0.0 release.

**Architecture:** Standard Python src/ layout with console script entry point. python-semantic-release for automated versioning and CHANGELOG generation. GitHub Actions for CI testing and release automation.

**Tech Stack:** Python 3.13, uv, python-semantic-release, GitHub Actions, pytest

---

## Phase 1: Structure Setup

### Task 1: Create Package Directory Structure

**Files:**
- Create: `src/netbox_mcp_server/` (directory)

**Step 1: Create the src/ and package directories**

```bash
mkdir -p src/netbox_mcp_server
```

**Step 2: Verify directory structure**

```bash
ls -la src/netbox_mcp_server/
```

Expected: Empty directory

**Step 3: Commit**

```bash
git add src/
git commit -m "chore: create src/netbox_mcp_server directory structure"
```

---

### Task 2: Create Package __init__.py

**Files:**
- Create: `src/netbox_mcp_server/__init__.py`

**Step 1: Write the package initialization file**

```python
"""NetBox MCP Server - Read-only MCP server for NetBox infrastructure data."""

__version__ = "1.0.0"  # Auto-managed by semantic-release

__all__ = ["NetBoxRestClient", "NETBOX_OBJECT_TYPES", "Settings"]

from netbox_mcp_server.netbox_client import NetBoxRestClient
from netbox_mcp_server.netbox_types import NETBOX_OBJECT_TYPES
from netbox_mcp_server.config import Settings
```

**Step 2: Save to file**

```bash
cat > src/netbox_mcp_server/__init__.py << 'EOF'
[paste content above]
EOF
```

**Step 3: Verify file created**

```bash
cat src/netbox_mcp_server/__init__.py
```

**Step 4: Commit**

```bash
git add src/netbox_mcp_server/__init__.py
git commit -m "feat: add package __init__.py with version and exports"
```

---

### Task 3: Create __main__.py Entry Point

**Files:**
- Create: `src/netbox_mcp_server/__main__.py`

**Step 1: Write the module execution entry point**

```python
"""Entry point for python -m netbox_mcp_server execution."""

from netbox_mcp_server.server import main

if __name__ == "__main__":
    main()
```

**Step 2: Save to file**

```bash
cat > src/netbox_mcp_server/__main__.py << 'EOF'
[paste content above]
EOF
```

**Step 3: Commit**

```bash
git add src/netbox_mcp_server/__main__.py
git commit -m "feat: add __main__.py for module execution support"
```

---

### Task 4: Move config.py to Package

**Files:**
- Move: `config.py` → `src/netbox_mcp_server/config.py`
- Modify: `src/netbox_mcp_server/config.py` (imports)

**Step 1: Move the file**

```bash
git mv config.py src/netbox_mcp_server/config.py
```

**Step 2: Verify no import changes needed**

Since config.py doesn't import other local modules, no changes needed.

**Step 3: Commit**

```bash
git commit -m "refactor: move config.py to src/netbox_mcp_server/"
```

---

### Task 5: Move netbox_types.py to Package

**Files:**
- Move: `netbox_types.py` → `src/netbox_mcp_server/netbox_types.py`

**Step 1: Move the file**

```bash
git mv netbox_types.py src/netbox_mcp_server/netbox_types.py
```

**Step 2: Verify no import changes needed**

Since netbox_types.py has no local imports, no changes needed.

**Step 3: Commit**

```bash
git commit -m "refactor: move netbox_types.py to src/netbox_mcp_server/"
```

---

### Task 6: Move netbox_client.py to Package

**Files:**
- Move: `netbox_client.py` → `src/netbox_mcp_server/netbox_client.py`
- Modify: `src/netbox_mcp_server/netbox_client.py` (imports)

**Step 1: Move the file**

```bash
git mv netbox_client.py src/netbox_mcp_server/netbox_client.py
```

**Step 2: Update imports in netbox_client.py**

Read the file and update any local imports:

```python
# Change from:
from netbox_types import NETBOX_OBJECT_TYPES

# To:
from netbox_mcp_server.netbox_types import NETBOX_OBJECT_TYPES
```

**Step 3: Commit**

```bash
git add src/netbox_mcp_server/netbox_client.py
git commit -m "refactor: move netbox_client.py to src/ and update imports"
```

---

### Task 7: Move server.py to Package

**Files:**
- Move: `server.py` → `src/netbox_mcp_server/server.py`
- Modify: `src/netbox_mcp_server/server.py` (imports and main function)

**Step 1: Move the file**

```bash
git mv server.py src/netbox_mcp_server/server.py
```

**Step 2: Update imports in server.py**

```python
# Change from:
from config import Settings, configure_logging
from netbox_client import NetBoxRestClient
from netbox_types import NETBOX_OBJECT_TYPES

# To:
from netbox_mcp_server.config import Settings, configure_logging
from netbox_mcp_server.netbox_client import NetBoxRestClient
from netbox_mcp_server.netbox_types import NETBOX_OBJECT_TYPES
```

**Step 3: Add main() function wrapper**

At the end of the file, wrap the current execution logic:

```python
def main():
    """Main entry point for the MCP server."""
    args = parse_cli_args()
    settings = Settings()
    configure_logging(settings.log_level)

    # Initialize NetBox client
    netbox = NetBoxRestClient(
        base_url=settings.netbox_url,
        token=settings.netbox_token
    )

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(settings.model_dump())
    logger.info(f"Starting NetBox MCP server on {settings.netbox_url}")

    # Run the server
    mcp.run()

if __name__ == "__main__":
    main()
```

**Step 4: Commit**

```bash
git add src/netbox_mcp_server/server.py
git commit -m "refactor: move server.py to src/, update imports, add main() function"
```

---

## Phase 2: Configuration Updates

### Task 8: Add Console Script Entry Point

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add [project.scripts] section**

Add after the `[project]` section:

```toml
[project.scripts]
netbox-mcp-server = "netbox_mcp_server.server:main"
```

**Step 2: Verify toml syntax**

```bash
uv sync --no-install-project
```

Expected: No errors

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add console script entry point netbox-mcp-server"
```

---

### Task 9: Add python-semantic-release Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add dependency using uv**

```bash
uv add --dev python-semantic-release
```

**Step 2: Verify installation**

```bash
uv run semantic-release --version
```

Expected: Version output (e.g., "9.x.x")

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add python-semantic-release dev dependency"
```

---

### Task 10: Configure python-semantic-release

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add [tool.semantic_release] configuration**

Add to the end of pyproject.toml:

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/netbox_mcp_server/__init__.py:__version__"]
branch = "main"
upload_to_vcs_release = true
build_command = "uv build"
tag_format = "v{version}"

[tool.semantic_release.commit_parser_options]
allowed_tags = ["feat", "fix", "docs", "chore", "refactor", "test", "ci", "perf"]
minor_tags = ["feat"]
patch_tags = ["fix", "perf"]

[tool.semantic_release.changelog]
changelog_file = "CHANGELOG.md"
```

**Step 2: Test configuration with dry-run**

```bash
uv run semantic-release version --no-push --no-commit --no-tag
```

Expected: Would bump to 1.0.0 (or similar output showing it works)

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: configure python-semantic-release for automated versioning"
```

---

## Phase 3: Test Updates

### Task 11: Update test_config.py Imports

**Files:**
- Modify: `tests/test_config.py`

**Step 1: Update imports**

```python
# Change from:
from config import Settings, configure_logging, parse_cli_args

# To:
from netbox_mcp_server.config import Settings, configure_logging, parse_cli_args
```

**Step 2: Run tests to verify**

```bash
uv run pytest tests/test_config.py -v
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_config.py
git commit -m "test: update test_config.py imports to use package structure"
```

---

### Task 12: Update test_filter_validation.py Imports

**Files:**
- Modify: `tests/test_filter_validation.py`

**Step 1: Update imports**

```python
# Change from:
from server import validate_filters

# To:
from netbox_mcp_server.server import validate_filters
```

**Step 2: Run tests to verify**

```bash
uv run pytest tests/test_filter_validation.py -v
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_filter_validation.py
git commit -m "test: update test_filter_validation.py imports to use package structure"
```

---

### Task 13: Update test_ordering.py Imports

**Files:**
- Modify: `tests/test_ordering.py`

**Step 1: Update imports**

```python
# Change from:
from server import netbox_get_objects

# To:
from netbox_mcp_server.server import netbox_get_objects
```

**Step 2: Run tests to verify**

```bash
uv run pytest tests/test_ordering.py -v
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_ordering.py
git commit -m "test: update test_ordering.py imports to use package structure"
```

---

### Task 14: Update test_pagination.py Imports

**Files:**
- Modify: `tests/test_pagination.py`

**Step 1: Update imports**

```python
# Change from:
from server import netbox_get_objects

# To:
from netbox_mcp_server.server import netbox_get_objects
```

**Step 2: Run tests to verify**

```bash
uv run pytest tests/test_pagination.py -v
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_pagination.py
git commit -m "test: update test_pagination.py imports to use package structure"
```

---

### Task 15: Update test_search.py Imports

**Files:**
- Modify: `tests/test_search.py`

**Step 1: Update imports**

```python
# Change from:
from server import netbox_search_objects
from netbox_types import NETBOX_OBJECT_TYPES

# To:
from netbox_mcp_server.server import netbox_search_objects
from netbox_mcp_server.netbox_types import NETBOX_OBJECT_TYPES
```

**Step 2: Run tests to verify**

```bash
uv run pytest tests/test_search.py -v
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_search.py
git commit -m "test: update test_search.py imports to use package structure"
```

---

### Task 16: Update test_brief.py Imports

**Files:**
- Modify: `tests/test_brief.py`

**Step 1: Update imports**

```python
# Change from:
from server import netbox_get_objects, netbox_get_object_by_id

# To:
from netbox_mcp_server.server import netbox_get_objects, netbox_get_object_by_id
```

**Step 2: Run tests to verify**

```bash
uv run pytest tests/test_brief.py -v
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_brief.py
git commit -m "test: update test_brief.py imports to use package structure"
```

---

### Task 17: Run Full Test Suite

**Files:**
- None (verification step)

**Step 1: Run all tests**

```bash
uv run pytest -v
```

Expected: All 43 tests pass

**Step 2: Verify no import errors**

Check output for any import-related failures.

**Step 3: If all pass, ready for next phase**

No commit needed - this is verification only.

---

## Phase 4: CI/CD Workflows

### Task 18: Create GitHub Workflows Directory

**Files:**
- Create: `.github/workflows/` (directory)

**Step 1: Create directory**

```bash
mkdir -p .github/workflows
```

**Step 2: Commit**

```bash
git add .github/
git commit -m "chore: create .github/workflows directory for CI/CD"
```

---

### Task 19: Create Test Workflow

**Files:**
- Create: `.github/workflows/test.yml`

**Step 1: Write test workflow**

```yaml
name: Test

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      netbox:
        image: netboxcommunity/netbox:latest
        env:
          SKIP_SUPERUSER: true
        ports:
          - 8000:8080

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest -v
        env:
          NETBOX_URL: http://localhost:8000
          NETBOX_TOKEN: ${{ secrets.NETBOX_TOKEN }}
```

**Step 2: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"
```

Expected: No errors (silent success)

**Step 3: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add test workflow for automated testing"
```

---

### Task 20: Create Release Workflow

**Files:**
- Create: `.github/workflows/release.yml`

**Step 1: Write release workflow**

```yaml
name: Release

permissions:
  contents: write
  issues: write
  pull-requests: write

on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: uv sync

      - name: Python Semantic Release
        uses: python-semantic-release/python-semantic-release@v9
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

**Step 2: Validate YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```

Expected: No errors

**Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: add release workflow for automated semantic releases"
```

---

## Phase 5: Documentation Updates

### Task 21: Update README.md - Breaking Change Notice

**Files:**
- Modify: `README.md`

**Step 1: Add breaking change notice after title**

Find the title (line 1-2) and add immediately after:

```markdown
> **⚠️ Breaking Change in v1.0.0**: The project structure has changed.
> If upgrading from v0.1.0, update your configuration:
> - Change `uv run server.py` to `uv run netbox-mcp-server`
> - Update Claude Desktop/Code configs to use `netbox-mcp-server` instead of `server.py`
> - Docker users: rebuild images with updated CMD
> - See [CHANGELOG.md](CHANGELOG.md) for full details
```

**Step 2: Verify formatting**

```bash
head -20 README.md
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add breaking change notice to README for v1.0.0"
```

---

### Task 22: Update README.md - Running Locally Section

**Files:**
- Modify: `README.md`

**Step 1: Find and update "Running Locally" or similar section**

Change all instances of:

```bash
# Before
uv run server.py

# After
uv run netbox-mcp-server
```

**Step 2: Verify all occurrences updated**

```bash
grep "uv run server.py" README.md
```

Expected: No results (empty)

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README commands to use netbox-mcp-server"
```

---

### Task 23: Update README.md - Claude Desktop/Code Config

**Files:**
- Modify: `README.md`

**Step 1: Find Claude Desktop/Code configuration section**

Update the JSON example:

```json
{
  "mcpServers": {
    "netbox": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/netbox-mcp-server",
        "run",
        "netbox-mcp-server"
      ],
      "env": {
        "NETBOX_URL": "https://demo.netbox.dev/",
        "NETBOX_TOKEN": "your-token-here"
      }
    }
  }
}
```

**Step 2: Verify JSON syntax**

```bash
python3 -c "import json; json.load(open('/dev/stdin'))" < README.md || echo "Check JSON manually"
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update Claude Desktop/Code config examples in README"
```

---

### Task 24: Update CLAUDE.md - Project Structure

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Find "Project Structure" section**

Replace with:

```markdown
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
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update project structure in CLAUDE.md"
```

---

### Task 25: Update CLAUDE.md - Common Commands

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Find "Common Commands" section**

Update all command examples:

```markdown
## Common Commands

```bash
# Install dependencies (ONLY use uv, NEVER pip)
uv sync

# Run the server locally (requires env vars)
NETBOX_URL=https://netbox.example.com/ NETBOX_TOKEN=<token> uv run netbox-mcp-server

# Alternative: module execution
uv run -m netbox_mcp_server

# Add to Claude Code (for development/testing)
claude mcp add --transport stdio netbox \
  --env NETBOX_URL=https://netbox.example.com/ \
  --env NETBOX_TOKEN=<token> \
  -- uv --directory /path/to/netbox-mcp-server run netbox-mcp-server
```
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update common commands in CLAUDE.md"
```

---

### Task 26: Update CLAUDE.md - Add Version Management Section

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add new section after "Development Philosophy"**

```markdown
## Version Management

This project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) for automated version management. Versions are automatically determined from commit messages following [Conventional Commits](https://www.conventionalcommits.org/).

**Release triggers:**
- `feat:` commits trigger minor version bumps (1.0.0 → 1.1.0)
- `fix:` and `perf:` commits trigger patch version bumps (1.0.0 → 1.0.1)
- Commits with `BREAKING CHANGE:` in the body trigger major version bumps (1.0.0 → 2.0.0)
- `docs:`, `test:`, `chore:`, `ci:`, `refactor:` commits are logged but don't trigger releases

**Workflow:**
- Merge to `main` automatically triggers release analysis
- If commits warrant a release, version is bumped and CHANGELOG updated
- GitHub Release is created with auto-generated release notes
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add version management section to CLAUDE.md"
```

---

### Task 27: Update Dockerfile

**Files:**
- Modify: `Dockerfile`

**Step 1: Find CMD line and update**

Change from:

```dockerfile
CMD ["python", "-u", "server.py"]
```

To:

```dockerfile
CMD ["netbox-mcp-server"]
```

**Step 2: Verify Docker syntax**

```bash
docker build -t netbox-mcp-test . --dry-run 2>/dev/null || echo "Build check (ignore if Docker not running)"
```

**Step 3: Commit**

```bash
git add Dockerfile
git commit -m "chore: update Dockerfile to use netbox-mcp-server command"
```

---

## Phase 6: Testing & Verification

### Task 28: Verify Console Script Works

**Files:**
- None (verification)

**Step 1: Sync dependencies to ensure script installed**

```bash
uv sync
```

**Step 2: Test console script execution (will fail without env vars - expected)**

```bash
uv run netbox-mcp-server --help 2>&1 || echo "Expected: Shows help or env var error"
```

Expected: Either help output or error about missing NETBOX_URL/NETBOX_TOKEN

**Step 3: Verify script is in uv environment**

```bash
uv run which netbox-mcp-server
```

Expected: Path to script in .venv/bin/

---

### Task 29: Run Full Test Suite Again

**Files:**
- None (verification)

**Step 1: Run all tests**

```bash
uv run pytest -v --tb=short
```

Expected: All 43 tests pass

**Step 2: Check for any warnings**

Review test output for deprecation warnings or issues.

**Step 3: Generate coverage report**

```bash
uv run pytest --cov=netbox_mcp_server --cov-report=term-missing
```

---

### Task 30: Verify Import Structure

**Files:**
- None (verification)

**Step 1: Test package imports in Python**

```bash
uv run python -c "from netbox_mcp_server import NetBoxRestClient, NETBOX_OBJECT_TYPES, Settings; print('Imports successful')"
```

Expected: "Imports successful"

**Step 2: Test version access**

```bash
uv run python -c "from netbox_mcp_server import __version__; print(f'Version: {__version__}')"
```

Expected: "Version: 1.0.0"

**Step 3: Test module execution**

```bash
uv run python -m netbox_mcp_server --help 2>&1 || echo "Expected: help or env error"
```

---

### Task 31: Validate GitHub Actions YAML

**Files:**
- None (verification)

**Step 1: Validate test.yml**

```bash
python3 -c "import yaml; print('test.yml valid') if yaml.safe_load(open('.github/workflows/test.yml')) else print('INVALID')"
```

Expected: "test.yml valid"

**Step 2: Validate release.yml**

```bash
python3 -c "import yaml; print('release.yml valid') if yaml.safe_load(open('.github/workflows/release.yml')) else print('INVALID')"
```

Expected: "release.yml valid"

---

## Phase 7: Final Commit & Push

### Task 32: Create Breaking Change Commit

**Files:**
- All modified files

**Step 1: Check git status**

```bash
git status
```

Expected: Should show "nothing to commit, working tree clean" (all previous commits done)

**Step 2: If any uncommitted files, stage them**

```bash
git add .
```

**Step 3: Verify all changes are in git history**

```bash
git log --oneline -20
```

Expected: See all commits from previous tasks

---

### Task 33: Push Feature Branch

**Files:**
- None (git operation)

**Step 1: Push feature branch to remote**

```bash
git push -u origin feat/src-layout-and-semantic-release
```

Expected: Branch pushed successfully

**Step 2: Note the branch URL**

GitHub will provide a URL to create a pull request.

---

### Task 34: Create Pull Request

**Files:**
- None (GitHub operation)

**Step 1: Open GitHub PR**

Use the URL from previous step or manually create PR with:

**Title:**
```
feat!: restructure to src/ layout and add semantic release
```

**Body:**
```markdown
## Summary

Restructures the project to use standard Python src/ layout and adds automated semantic release capabilities via python-semantic-release.

## Breaking Changes

⚠️ **This is a breaking change for users:**

- **Command change**: `uv run server.py` → `uv run netbox-mcp-server`
- **Claude config change**: Update `args` to use `netbox-mcp-server` instead of `server.py`
- **Docker change**: Rebuild images (CMD updated)
- **Import changes** (contributors): `from server import` → `from netbox_mcp_server.server import`

## Changes

### Structure
- Moved all Python modules to `src/netbox_mcp_server/`
- Added package `__init__.py` with version export
- Added `__main__.py` for module execution support
- Added console script entry point in pyproject.toml

### Automation
- Added python-semantic-release for automated versioning
- Added CI test workflow (pytest on PRs and main)
- Added release workflow (automatic on push to main)
- Configured conventional commits for version bumping

### Code
- Updated all module imports to use package structure
- Added `main()` function to server.py
- Updated all 6 test files with new imports

### Documentation
- Updated README.md with breaking change notice
- Updated all command examples in README.md
- Updated CLAUDE.md project structure
- Updated Dockerfile CMD
- Added version management documentation

## Testing

- ✅ All 43 tests passing
- ✅ Console script `netbox-mcp-server` works
- ✅ Module execution `python -m netbox_mcp_server` works
- ✅ Package imports validated
- ✅ CI workflows validated

## Release Plan

When merged, this will automatically trigger a v1.0.0 release via python-semantic-release due to the breaking change in the commit history.

Closes #[issue number if applicable]
```

---

## Post-Merge Verification

### Task 35: Monitor Release Workflow

**After PR is merged to main:**

**Step 1: Watch GitHub Actions**

Navigate to: `https://github.com/netboxlabs/netbox-mcp-server/actions`

**Step 2: Wait for "Release" workflow to complete**

Expected: Green checkmark, workflow completes successfully

**Step 3: Verify outputs**
- Version bumped to 1.0.0 in pyproject.toml
- CHANGELOG.md created and committed
- Git tag `v1.0.0` created
- GitHub Release created

---

### Task 36: Verify GitHub Release

**Files:**
- None (GitHub verification)

**Step 1: Navigate to GitHub Releases page**

`https://github.com/netboxlabs/netbox-mcp-server/releases`

**Step 2: Verify v1.0.0 release exists**

Check:
- Tag is `v1.0.0`
- Release notes include breaking change information
- Release notes auto-generated from commits

---

### Task 37: Test v1.0.0 Locally

**Files:**
- None (verification)

**Step 1: Pull latest main**

```bash
git checkout main
git pull
```

**Step 2: Verify version in files**

```bash
grep "version = " pyproject.toml
grep "__version__ = " src/netbox_mcp_server/__init__.py
```

Expected: Both show "1.0.0"

**Step 3: Verify CHANGELOG exists**

```bash
cat CHANGELOG.md | head -20
```

Expected: Shows v1.0.0 entry with breaking change notice

---

### Task 38: Clean Up Worktree (Optional)

**Files:**
- None (cleanup)

**Step 1: Return to main working directory**

```bash
cd ../..  # Back to main repo root
```

**Step 2: Remove worktree**

```bash
git worktree remove .worktrees/feat-src-layout-and-semantic-release
```

**Step 3: Prune worktree references**

```bash
git worktree prune
```

---

## Success Criteria Checklist

- [ ] All 43 tests passing with new structure
- [ ] Console script `netbox-mcp-server` executes successfully
- [ ] Module execution `python -m netbox_mcp_server` works
- [ ] All imports use `netbox_mcp_server.*` package structure
- [ ] pyproject.toml has console script entry point
- [ ] pyproject.toml has semantic-release configuration
- [ ] python-semantic-release dev dependency added
- [ ] Test workflow `.github/workflows/test.yml` created
- [ ] Release workflow `.github/workflows/release.yml` created
- [ ] README.md updated with breaking change notice
- [ ] README.md commands updated to use `netbox-mcp-server`
- [ ] CLAUDE.md project structure updated
- [ ] CLAUDE.md commands updated
- [ ] CLAUDE.md has version management section
- [ ] Dockerfile CMD updated to use `netbox-mcp-server`
- [ ] Feature branch pushed to GitHub
- [ ] Pull request created with breaking change notice
- [ ] PR merged to main
- [ ] Release workflow executed successfully
- [ ] GitHub Release v1.0.0 created
- [ ] CHANGELOG.md generated and committed
- [ ] Version 1.0.0 in pyproject.toml and __init__.py

---

## Rollback Plan (If Needed)

If issues arise after merge:

1. Create hotfix branch from commit before merge
2. Revert breaking changes
3. Create patch release
4. Fix issues in separate PR

**Prevention:**
- All tasks have verification steps
- Tests run before merge
- Can test PR branch before merging

---

## Notes for Implementer

- **DRY**: Each file is moved/modified once
- **YAGNI**: No extra features, just what's needed for refactoring
- **TDD**: Tests updated immediately after code changes
- **Commits**: Frequent, atomic commits for easy review
- **Verification**: Tests run after each import change

**Estimated total time**: 2-3 hours for careful implementation

**Key risks**:
1. Import errors - mitigated by testing after each change
2. CI workflow misconfiguration - mitigated by YAML validation
3. Semantic release issues - mitigated by dry-run testing

**Support**:
- Design document: `.plans/2025-10-28-src-layout-semantic-release-design.md`
- Python-semantic-release docs: https://python-semantic-release.readthedocs.io/
- Conventional commits: https://www.conventionalcommits.org/
