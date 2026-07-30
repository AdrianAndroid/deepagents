"""
zjcode 品牌定制层

这个包包含所有 zjcode 专属的品牌定制和扩展功能。
上游 main 分支不包含这个目录，因此永远不会产生合并冲突。
"""

from zjcode.brand import (
    BRAND_NAME,
    CONFIG_DIR_NAME,
    DISTRIBUTION_NAME,
    FEATURE_MCP_TRUST,
    FEATURE_NO_MOUSE,
    FEATURE_TODO_PROMPT,
    PYPI_URL,
    SDK_PYPI_URL,
)
from zjcode.mcp_trust import (
    compute_config_fingerprint,
    is_project_mcp_trusted,
    revoke_project_mcp_trust,
    trust_project_mcp,
)
from zjcode.patches import apply_all_patches, apply_brand_patches

__all__ = [
    "BRAND_NAME",
    "CONFIG_DIR_NAME",
    "DISTRIBUTION_NAME",
    "FEATURE_MCP_TRUST",
    "FEATURE_NO_MOUSE",
    "FEATURE_TODO_PROMPT",
    "PYPI_URL",
    "SDK_PYPI_URL",
    "apply_all_patches",
    "apply_brand_patches",
    "compute_config_fingerprint",
    "is_project_mcp_trusted",
    "revoke_project_mcp_trust",
    "trust_project_mcp",
]
