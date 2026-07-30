"""Lightweight shared constants for the app.

This module is intentionally dependency-free (no third-party imports, no
sibling-module imports) so any other module — including the startup-critical
`main.py` and the heavy `agent.py` — can import from it without triggering a
chain of expensive imports.
"""

from __future__ import annotations

from typing import Final

DEFAULT_AGENT_NAME: Final[str] = "agent"
"""Default agent / assistant identifier when no `-a` flag is given."""

FS_TOOL_NAMES: Final[frozenset[str]] = frozenset(
    {"ls", "read_file", "write_file", "edit_file", "delete", "glob", "grep", "execute"}
)
"""Mirror of the SDK's `FsToolName` literal members.

Hardcoded here rather than derived from `deepagents.FsToolName` because
`deepagents` must not be imported on the arg-parsing hot path (see AGENTS.md
"Startup performance"); this module is dependency-free and safe for `main.py` to
import. Consumers (`main._parse_allow_fs_tools_flag`,
`tool_catalog.collect_built_in_tools`) alias this set, and `get_args(FsToolName)`
drift guards in `test_main_args` and `test_tool_catalog` pin it so a new or
renamed SDK filesystem tool fails a test instead of silently diverging.
"""

SDK_DEFAULT_RUBRIC_MAX_ITERATIONS: Final[int] = 3
"""Default `RubricMiddleware.max_iterations`, shown without importing the SDK.

Hardcoded rather than read from `deepagents.middleware.rubric.RubricMiddleware`
because this module is dependency-free and importing the SDK for a display
string would violate the startup-performance rule (see AGENTS.md). This is a
hand-maintained duplicate that can rot if the SDK bumps its default, so
`test_reliable_rubric.py::TestReliableRubricMiddleware::test_displayed_max_iterations_default_matches_sdk`
is the drift guard that fails when the two diverge.
"""

CONFIG_DOTDIR: Final[str] = ".zjcode"
"""User-level config directory name (the `.zjcode` in `~/.zjcode/`).

Single source of truth for the private-brand directory name. `model_config`
builds the absolute `DEFAULT_CONFIG_DIR` from it, and prompt/help text that
needs a portable `~/...` form references the name directly. Keep it in
lock-step with `PROJECT_DOTDIR` (the per-project `.zjcode/`) when rebranding.
"""

PROJECT_DOTDIR: Final[str] = ".zjcode"
"""Per-project config directory name (e.g. `<project-root>/.zjcode/`).

Holds project-scoped skills, agents, `AGENTS.md`, and `.mcp.json`. Named here
so the private-branded `zjcode` build stays consistent with the user-level
`~/.zjcode` directory (see `model_config.DEFAULT_CONFIG_DIR`) — both must move
together when rebranding, otherwise project-level discovery silently points at
the upstream `.deepagents` path and finds nothing.
"""

FIREWORKS_PROVIDER_ID_PREFIX: Final[str] = "accounts/fireworks/"
"""Prefix used to infer Fireworks from fully-qualified IDs."""

FIREWORKS_MODEL_ID_PREFIXES: Final[tuple[str, ...]] = (
    "accounts/fireworks/models/",
    "accounts/fireworks/routers/",
)
"""Model and router ID prefixes used for stripping and classification."""

MCP_REENABLED_PENDING_ERROR: Final[str] = "Re-enabled — press Ctrl+R to load."
"""User-facing reconnect guidance shown for an MCP server that was optimistically
re-enabled but whose agent has not yet reconnected.

Set as `MCPServerInfo.error` by `app._apply_optimistic_disabled_state` (alongside
`pending_reconnect=True`, which is what `/tools` actually keys off). Named here
so the producer and the tests asserting the message share one literal.
"""

SYSTEM_MESSAGE_PREFIX: Final[str] = "[SYSTEM]"
"""Prefix for synthetic human messages (e.g. interrupt cancellation notices).

Such messages are written to the `messages` channel for the agent's benefit on
resume but are not user-authored, so they are filtered out of both the rendered
transcript and a thread's initial prompt. Shared here so the single producer
(`textual_adapter`) and its consumers (`app`, `sessions`) agree on one literal.
"""
