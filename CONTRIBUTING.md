# Contributing to NetBox MCP Server

Thanks for your interest in contributing! This guide covers what kinds of contributions we're looking for, how to propose them, and where the project's boundaries are.

Questions that don't need a code change are best asked in the `#ai` channel on [NetDev Community Slack](https://netdev.chat/) - this project doesn't have dedicated community channels yet.

## Project scope

The NetBox MCP Server is a **simple, read-only MCP server for core NetBox objects**. It uses the NetBox REST API with static token authentication. The priorities are:

- **Easy to get started.** Minimal configuration, minimal dependencies, runs locally in under a minute.
- **Hard to misuse.** Read-only by design, no plugin surface, small attack surface.
- **Easy to fork.** Apache 2.0 licensed, small codebase, designed to be adapted.

This project is maintained by a small team - scope is deliberately limited so it stays that way. We may decline feature proposals that fall outside the areas listed below, even if they're well-executed.

### Forking is a first-class option

If your use case needs features outside this scope, forking is actively encouraged. The project is small and focused by design - your fork can diverge without losing the core. We welcome issues or discussions that share interesting forks back with the community.

## Reporting bugs

Bug reports should describe unintended or unexpected behaviour - not requests for new functionality (see "Feature requests" below for that).

1. Check you're running the [latest release](https://github.com/netboxlabs/netbox-mcp-server/releases) - your bug may already be fixed.
2. Search [existing issues](https://github.com/netboxlabs/netbox-mcp-server/issues) to see if it's been reported. If so, add a 👍 reaction and any extra context as a comment.
3. If it's new, [open an issue](https://github.com/netboxlabs/netbox-mcp-server/issues/new) with clear reproduction steps, error messages, and NetBox/Python versions.

Tips:

- Screenshots and exact error messages are especially helpful.
- Don't prepend your issue title with a label like `[Bug]` - labels are applied by maintainers.

## Feature requests

Before opening a feature request:

1. **Check the scope section above.** If your idea falls outside the project's scope, please consider a fork rather than an FR.
2. **Search existing issues** to avoid duplicates.
3. **Open an issue for discussion first.** Don't start implementation until a maintainer has confirmed scope fit.

In-scope contributions we're especially keen to see:

- Bug fixes in existing tools
- Improvements to error messages and logging
- Documentation, examples, and quickstart improvements
- Adding new core NetBox object types to `src/netbox_mcp_server/netbox_types.py`
- Compatibility fixes for new NetBox versions
- Dependency updates

## Submitting pull requests

For non-trivial changes, please **open an issue first**. This saves you time - if the change isn't a good fit, we can tell you before you write the code. Drive-by bug fixes and small docs improvements don't need an issue first - just send a PR.

Our process for larger changes:

1. Open an issue describing the bug or feature.
2. Wait for maintainer response confirming scope and approach.
3. Submit a PR referencing the issue.
4. Respond to review feedback.
5. Maintainer merges.

PR checklist:

- Base off `main`.
- Conventional commit format (`feat:`, `fix:`, `chore:`, etc. - see [`CLAUDE.md`](CLAUDE.md) for details).
- `ruff check` passes.
- Type hints on all public functions.

Detailed code standards live in [`CLAUDE.md`](CLAUDE.md) - please skim it before your first PR.

## AI-assisted contributions

AI-assisted contributions are welcome. We use AI tools ourselves. That said, you're responsible for what you submit - review it, test it, and take ownership. PRs that appear to be unreviewed AI output will be asked for revision or closed.

## Other ways to contribute

Not every useful contribution is code:

- Answering questions in discussions or issues
- Writing a blog post or video about your use case
- Sharing useful forks back via issues or discussions
- Improving documentation
