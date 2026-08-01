"""Re-export zjcode MCP trust functions for backward-compatible patching.

Tests patch ``deepagents_code.mcp_trust.is_project_mcp_trusted``; this thin
shim keeps that import path working without duplicating the implementation.
"""

from zjcode.mcp_trust import (  # noqa: F401
    compute_config_fingerprint,
    is_project_mcp_trusted,
    revoke_project_mcp_trust,
    trust_project_mcp,
)
