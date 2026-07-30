"""
zjcode 品牌专属配置

⚠️ 重要：
1. 这个文件是 zjcode 专属的，上游 main 分支永远不会有
2. 所有品牌定制必须放在这里，不要散落在其他文件
3. 每次合并 main 分支后，检查这个文件是否还在（应该永远在）
"""

# ═══════════════════════════════════════════════════════════════
# 核心品牌标识
# ═══════════════════════════════════════════════════════════════
DISTRIBUTION_NAME = "zjcode"
BRAND_NAME = "zjcode"
CONFIG_DIR_NAME = ".zjcode"
PYPI_PACKAGE_NAME = "zjcode"

# ═══════════════════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════════════════
CONFIG_DOTDIR = ".zjcode"
PROJECT_DOTDIR = ".zjcode"

# ═══════════════════════════════════════════════════════════════
# PyPI URLs
# ═══════════════════════════════════════════════════════════════
PYPI_URL = f"https://pypi.org/pypi/{DISTRIBUTION_NAME}/json"
SDK_PYPI_URL = "https://pypi.org/pypi/deepagents/json"

# ═══════════════════════════════════════════════════════════════
# 环境变量
# ═══════════════════════════════════════════════════════════════
ENV_NO_MOUSE = f"{DISTRIBUTION_NAME.upper()}_NO_MOUSE"
ENV_PYPI_URL = f"{DISTRIBUTION_NAME.upper()}_PYPI_URL"
ENV_SDK_PYPI_URL = f"{DISTRIBUTION_NAME.upper()}_SDK_PYPI_URL"

# ═══════════════════════════════════════════════════════════════
# 功能开关
# ═══════════════════════════════════════════════════════════════
FEATURE_MCP_TRUST = True
FEATURE_TODO_PROMPT = True
FEATURE_NO_MOUSE = True

# ═══════════════════════════════════════════════════════════════
# 补丁映射表
# ═══════════════════════════════════════════════════════════════
# 格式: {"模块路径": {"常量名": 我们的值}}
# ═══════════════════════════════════════════════════════════════
PATCH_MAP = {
    "deepagents_code._constants": {
        "CONFIG_DOTDIR": CONFIG_DOTDIR,
        "PROJECT_DOTDIR": PROJECT_DOTDIR,
    },
    "deepagents_code._version": {
        "DISTRIBUTION_NAME": DISTRIBUTION_NAME,
        "BRAND_NAME": BRAND_NAME,
        "PYPI_URL": PYPI_URL,
        "SDK_PYPI_URL": SDK_PYPI_URL,
    },
    "deepagents_code._env_vars": {
        "NO_MOUSE": ENV_NO_MOUSE,
        "PYPI_URL": PYPI_URL,
        "SDK_PYPI_URL": SDK_PYPI_URL,
    },
}

# 需要保留的专属文件（合并后自动检查）
BRAND_FILES = [
    "zjcode/mcp_trust.py",
    "zjcode/todo_list_prompt.md",
]
