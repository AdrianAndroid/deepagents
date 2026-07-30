#!/usr/bin/env python3
"""
zjcode 品牌隔离层迁移工具

一键解决合并 main 分支的品牌冲突问题。
核心原理：物理隔离 + 动态注入

使用方法:
    python scripts/zjcode-brand-migration.py setup    # 执行迁移
    python scripts/zjcode-brand-migration.py verify   # 验证效果
    python scripts/zjcode-brand-migration.py check   # 合并后完整性检查
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "libs" / "code"
ZJCODE_DIR = CODE_DIR / "zjcode"


def print_header(title: str) -> None:
    print(f"\n{YELLOW}🚀 {title}{NC}\n")


def print_success(msg: str) -> None:
    print(f"{GREEN}✅ {msg}{NC}")


def print_error(msg: str) -> None:
    print(f"{RED}❌ {msg}{NC}")


def print_warning(msg: str) -> None:
    print(f"{YELLOW}⚠️  {msg}{NC}")


def run_cmd(cmd: str, cwd: Path = PROJECT_ROOT) -> tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def create_brand_py() -> None:
    """创建 brand.py - 所有品牌常量定义"""
    content = '''"""
zjcode 品牌专属配置

⚠️  重要：
1. 这个文件是 zjcode 专属的，上游 main 分支永远不会有
2. 所有品牌定制必须放在这里，不要散落在其他文件
3. 每次合并 main 分支后，检查这个文件是否还在（应该永远在）
"""

# ═══════════════════════════════════════════════════════════
# 核心品牌标识
# ═══════════════════════════════════════════════════════════
DISTRIBUTION_NAME = "zjcode"
BRAND_NAME = "zjcode"
CONFIG_DIR_NAME = ".zjcode"
PYPI_PACKAGE_NAME = "zjcode"

# ═══════════════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════════════
CONFIG_DOTDIR = ".zjcode"
PROJECT_DOTDIR = ".zjcode"

# ═══════════════════════════════════════════════════════════
# PyPI URLs
# ═══════════════════════════════════════════════════════════
PYPI_URL = f"https://pypi.org/pypi/{DISTRIBUTION_NAME}/json"
SDK_PYPI_URL = "https://pypi.org/pypi/deepagents/json"

# ═══════════════════════════════════════════════════════════
# 环境变量
# ═══════════════════════════════════════════════════════════
ENV_NO_MOUSE = f"{DISTRIBUTION_NAME.upper()}_NO_MOUSE"
ENV_PYPI_URL = f"{DISTRIBUTION_NAME.upper()}_PYPI_URL"
ENV_SDK_PYPI_URL = f"{DISTRIBUTION_NAME.upper()}_SDK_PYPI_URL"

# ═══════════════════════════════════════════════════════════
# 功能开关
# ═══════════════════════════════════════════════════════════
FEATURE_MCP_TRUST = True
FEATURE_TODO_PROMPT = True
FEATURE_NO_MOUSE = True

# ═══════════════════════════════════════════════════════════
# 补丁映射表
# ═══════════════════════════════════════════════════════════
# 格式: {"模块路径": {"常量名": 我们的值}}
# ═══════════════════════════════════════════════════════════
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
'''
    with open(ZJCODE_DIR / "brand.py", "w") as f:
        f.write(content)
    print_success("创建 brand.py")


def create_patches_py() -> None:
    """创建 patches.py - 运行时补丁逻辑"""
    content = '''"""
运行时品牌补丁应用器

原理：在 Python 模块导入后，动态修改模块的属性
优点：
1. 完全不修改上游源码
2. 100% 接收上游的 bug 修复和新功能
3. 我们的定制永远生效
"""

import importlib
import logging
from typing import Any

from zjcode.brand import PATCH_MAP

logger = logging.getLogger(__name__)


def apply_brand_patches() -> None:
    """应用所有品牌定制补丁

    在应用启动早期调用，确保所有品牌定制在使用前生效。
    对于 main 分支没有的常量，直接注入到模块中。
    """
    applied_count = 0
    failed_count = 0

    for module_path, patches in PATCH_MAP.items():
        try:
            module = importlib.import_module(module_path)

            for name, value in patches.items():
                old_value = getattr(module, name, None)
                if old_value != value:
                    setattr(module, name, value)
                    applied_count += 1
                    logger.debug(
                        f"[zjcode] Patched {module_path}.{name}: "
                        f"{old_value!r} → {value!r}"
                    )

        except ImportError:
            logger.warning(f"[zjcode] Module {module_path} not found, skipping patches")
            failed_count += len(patches)

    if applied_count > 0:
        logger.info(f"[zjcode] Applied {applied_count} brand patches")
    if failed_count > 0:
        logger.warning(f"[zjcode] Failed to apply {failed_count} brand patches")


def patch_path_constants() -> None:
    """修补硬编码的路径常量

    对那些在模块级别就计算好的路径，需要在使用前重新计算。
    """
    from pathlib import Path

    try:
        patched = 0

        # 修补 config.py 中的路径常量
        from deepagents_code import config

        if hasattr(config, "_GLOBAL_DOTENV_PATH"):
            old = config._GLOBAL_DOTENV_PATH
            config._GLOBAL_DOTENV_PATH = Path.home() / ".zjcode" / ".env"
            if old != config._GLOBAL_DOTENV_PATH:
                patched += 1

        # 修补 DEFAULT_CONFIG_DIR
        from deepagents_code import model_config

        if hasattr(model_config, "DEFAULT_CONFIG_DIR"):
            old = model_config.DEFAULT_CONFIG_DIR
            model_config.DEFAULT_CONFIG_DIR = Path.home() / ".zjcode"
            if old != model_config.DEFAULT_CONFIG_DIR:
                patched += 1

        # 修补 media_utils.py 中的 PASTED_MEDIA_DIR
        try:
            from deepagents_code import media_utils

            if hasattr(media_utils, "PASTED_MEDIA_DIR"):
                old = media_utils.PASTED_MEDIA_DIR
                media_utils.PASTED_MEDIA_DIR = Path.home() / ".zjcode" / "pasted"
                if old != media_utils.PASTED_MEDIA_DIR:
                    patched += 1
        except ImportError:
            pass

        if patched > 0:
            logger.info(f"[zjcode] Patched {patched} path constants")
    except Exception as e:
        logger.warning(f"[zjcode] Failed to patch path constants: {e}")


def apply_all_patches() -> None:
    """应用所有补丁的入口函数"""
    apply_brand_patches()
    try:
        patch_path_constants()
    except Exception:
        # 路径补丁失败不影响核心功能
        pass
'''
    with open(ZJCODE_DIR / "patches.py", "w") as f:
        f.write(content)
    print_success("创建 patches.py")


def create_init_py() -> None:
    """创建 __init__.py - 导出所有品牌功能"""
    content = '''"""
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
from zjcode.patches import apply_all_patches, apply_brand_patches

try:
    from zjcode.mcp_trust import (
        compute_config_fingerprint,
        is_project_mcp_trusted,
        revoke_project_mcp_trust,
        trust_project_mcp,
    )

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
except ImportError:
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
    ]
'''
    with open(ZJCODE_DIR / "__init__.py", "w") as f:
        f.write(content)
    print_success("创建 __init__.py")


def add_init_hook() -> None:
    """在 deepagents_code/__init__.py 顶部添加补丁钩子"""
    init_path = CODE_DIR / "deepagents_code" / "__init__.py"
    backup_path = CODE_DIR / "deepagents_code" / "__init__.py.bak"

    # 备份
    shutil.copy(init_path, backup_path)

    # 读取原有内容
    with open(init_path, "r") as f:
        lines = f.readlines()

    # 找到 from __future__ import annotations 之后插入钩子
    hook_code = '''
# =============================================================================
# zjcode 品牌定制钩子
# 这是我们唯一修改的上游文件，只有 3 行，冲突概率极低
# =============================================================================
try:
    from zjcode import apply_all_patches

    apply_all_patches()
except ImportError:
    pass  # 上游构建时没有 zjcode 目录，正常运行
# =============================================================================
'''

    # 查找插入位置（在 docstring 和 from __future__ 之后
    new_lines = []
    i = 0
    n = len(lines)

    # 跳过空行和 docstring
    while i < n and (lines[i].strip() == "" or lines[i].startswith('"""') or lines[i].startswith("'''"):
        new_lines.append(lines[i])
        if lines[i].strip() in ('"""', "'''"):
            # 找到 docstring 结束
            i += 1
            while i < n and not lines[i].strip() not in ('"""', "'''"):
                new_lines.append(lines[i])
                i += 1
            if i < n:
                new_lines.append(lines[i])
                i += 1
        else:
            i += 1

    # 现在插入钩子
    new_lines.append("\n")
    new_lines.append(hook_code)
    new_lines.append("\n")

    # 添加剩余的行
    while i < n:
        new_lines.append(lines[i])
        i += 1

    # 写入新文件
    with open(init_path, "w") as f:
        f.writelines(new_lines)

    print_success("添加 __init__.py 补丁钩子")


def move_brand_files() -> None:
    """移动品牌专属文件"""
    files_to_move = [
        ("mcp_trust.py", "移动 mcp_trust.py"),
        ("todo_list_prompt.md", "移动 todo_list_prompt.md"),
    ]

    for filename, desc in files_to_move:
        src = CODE_DIR / "deepagents_code" / filename
        dst = ZJCODE_DIR / filename
        if src.exists():
            shutil.move(src, dst)
            print_success(desc)


def update_import_references() -> None:
    """更新导入引用为 try/except 包装"""
    # 这部分需要手动处理，因为每个文件的导入方式不同
    print_warning("请手动更新以下文件的 mcp_trust 导入引用：")
    print("  - main.py")
    print("  - mcp_login_service.py")
    print("  - mcp_tools.py")
    print("  - agent.py 中的 todo_list_prompt.md 路径")


def create_check_script() -> None:
    """创建品牌完整性检查脚本"""
    script_path = PROJECT_ROOT / "scripts" / "check-brand-after-merge.sh"
    content = '''#!/bin/bash
# zjcode 品牌完整性检查脚本
# 每次合并 main 分支后运行

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 检查 zjcode 品牌定制完整性...${NC}"
echo ""

ERRORS=0
WARNINGS=0

# 检查 1: zjcode 目录存在
if [ ! -d "libs/code/zjcode" ]; then
    echo -e "${RED}❌ 严重: zjcode 目录不存在！${NC}"
    echo "   恢复命令: git checkout HEAD -- libs/code/zjcode/"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ zjcode 目录存在${NC}"
fi

# 检查 2: __init__.py 钩子
grep -q "zjcode" libs/code/deepagents_code/__init__.py
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  警告: __init__.py 中可能缺少 zjcode 钩子${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ __init__.py 钩子存在${NC}"
fi

# 检查 3: brand.py 中的 DISTRIBUTION_NAME
grep -q 'DISTRIBUTION_NAME.*zjcode' libs/code/zjcode/brand.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ brand.py 中 DISTRIBUTION_NAME 不是 zjcode${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ brand.py 中 DISTRIBUTION_NAME = zjcode${NC}"
fi

# 检查 4: _constants.py 是否已恢复上游默认值（不应该有 CONFIG_DOTDIR）
grep -q 'CONFIG_DOTDIR.*zjcode' libs/code/deepagents_code/_constants.py
if [ $? -eq 0 ]; then
    echo -e "${YELLOW}⚠️  警告: _constants.py 中 CONFIG_DOTDIR 可能未恢复为上游默认值${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ _constants.py 已恢复上游默认值${NC}"
fi

# 检查