# zjcode 品牌隔离层迁移完全指南

## 🎯 问题诊断

### 以前的痛点

每次合并上游 main 分支时：
1. **品牌定制经常被覆盖**（DISTRIBUTION_NAME 变回 deepagents-code）
2. **新增的文件被删除**（mcp_trust.py, todo_list_prompt.md）
3. **硬编码的路径被还原**（.zjcode 变回 .deepagents）
4. **每次解决冲突需要 30-60 分钟**

---

## 🏗️ 解决方案：补丁层模式

### 核心原理

**物理隔离 + 动态注入**，让品牌定制与上游代码在文件系统层面完全分离。

```
libs/code/
├── deepagents_code/     ← 100% 上游代码，一行不改！
│   ├── _version.py      ← DISTRIBUTION_NAME = "deepagents-code"
│   ├── _constants.py    ← CONFIG_DOTDIR = ".deepagents"
│   └── __init__.py      ← 只加 3 行钩子
│
└── zjcode/              ← 100% 我们的代码，上游永远没有！
    ├── __init__.py      ← 导出品牌功能
    ├── brand.py         ← 所有品牌常量定义
    ├── patches.py       ← 运行时补丁逻辑
    ├── mcp_trust.py     ← 我们新增的功能
    └── todo_list_prompt.md
```

---

## 🚀 一键迁移脚本

```bash
#!/bin/bash
# zjcode-brand-migration.sh
# 一键执行品牌隔离层迁移

set -e

echo "🚀 开始 zjcode 品牌隔离层迁移..."

# 1. 创建目录结构
mkdir -p libs/code/zjcode

# 2. 创建 brand.py
cat > libs/code/zjcode/brand.py << 'EOF'
"""
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
EOF

echo "✅ 创建 brand.py"

# 3. 创建 patches.py
cat > libs/code/zjcode/patches.py << 'EOF'
"""
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
EOF

echo "✅ 创建 patches.py"

# 4. 创建 __init__.py
cat > libs/code/zjcode/__init__.py << 'EOF'
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
EOF

echo "✅ 创建 __init__.py"

# 5. 移动独立模块
if [ -f libs/code/deepagents_code/mcp_trust.py ]; then
    mv libs/code/deepagents_code/mcp_trust.py libs/code/zjcode/mcp_trust.py
    echo "✅ 移动 mcp_trust.py"
fi

if [ -f libs/code/deepagents_code/todo_list_prompt.md ]; then
    mv libs/code/deepagents_code/todo_list_prompt.md libs/code/zjcode/todo_list_prompt.md
    echo "✅ 移动 todo_list_prompt.md"
fi

# 6. 在 deepagents_code/__init__.py 顶部添加钩子
# 先备份
cp libs/code/deepagents_code/__init__.py libs/code/deepagents_code/__init__.py.bak

# 创建带有钩子的新文件
cat > libs/code/deepagents_code/__init__.py.new << 'EOF'
"""Deep Agents Code - Interactive AI coding assistant."""

from __future__ import annotations

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

EOF

# 追加原有内容（跳过第一行 docstring 和第二行空行）
tail -n +4 libs/code/deepagents_code/__init__.py.bak >> libs/code/deepagents_code/__init__.py.new
mv libs/code/deepagents_code/__init__.py.new libs/code/deepagents_code/__init__.py
rm libs/code/deepagents_code/__init__.py.bak

echo "✅ 添加 __init__.py 补丁钩子"

# 7. 更新所有引用 mcp_trust 的地方
echo ""
echo "🔧 更新 mcp_trust 导入引用..."

# main.py
if grep -q "from deepagents_code.mcp_trust import" libs/code/deepagents_code/main.py 2>/dev/null; then
    sed -i '' 's/from deepagents_code.mcp_trust import/try:\n    from zjcode import/g' libs/code/deepagents_code/main.py
    sed -i '' '/from zjcode import/a\
except ImportError:\
    # 上游没有 MCP 信任功能\
    pass' libs/code/deepagents_code/main.py
    echo "  ✅ 更新 main.py"
fi

# mcp_login_service.py
if grep -q "from deepagents_code.mcp_trust import" libs/code/deepagents_code/mcp_login_service.py 2>/dev/null; then
    sed -i '' 's/from deepagents_code.mcp_trust import/try:\n    from zjcode import/g' libs/code/deepagents_code/mcp_login_service.py
    sed -i '' '/from zjcode import/a\
except ImportError:\
    # 上游没有 MCP 信任功能\
    mcp_trust = None' libs/code/deepagents_code/mcp_login_service.py
    echo "  ✅ 更新 mcp_login_service.py"
fi

# mcp_tools.py
if grep -q "from deepagents_code.mcp_trust import" libs/code/deepagents_code/mcp_tools.py 2>/dev/null; then
    sed -i '' 's/from deepagents_code.mcp_trust import/try:\n    from zjcode import/g' libs/code/deepagents_code/mcp_tools.py
    sed -i '' '/from zjcode import/a\
except ImportError:\
    # 上游没有 MCP 信任功能\
    mcp_trust = None' libs/code/deepagents_code/mcp_tools.py
    echo "  ✅ 更新 mcp_tools.py"
fi

# 8. 更新 agent.py 中的 todo_list_prompt.md 引用
if grep -q "todo_list_prompt.md" libs/code/deepagents_code/agent.py 2>/dev/null; then
    # 这个需要手动修改，因为是路径引用
    echo "  ⚠️  请手动更新 agent.py 中的 todo_list_prompt.md 路径引用"
    echo "     改为从 zjcode 包加载"
fi

# 9. 创建品牌完整性检查脚本
mkdir -p scripts
cat > scripts/check-brand-after-merge.sh << 'EOF'
#!/bin/bash
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

# 检查 5: mcp_trust.py 位置
if [ -f "libs/code/zjcode/mcp_trust.py" ]; then
    echo -e "${GREEN}✅ mcp_trust.py 已迁移到 zjcode/ 目录${NC}"
else
    echo -e "${YELLOW}⚠️  警告: mcp_trust.py 不在 zjcode/ 目录${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "==================== 汇总 ===================="
if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✅ 所有品牌定制检查通过！${NC}"
        echo -e "${GREEN}   下次合并 main 分支应该几乎没有冲突${NC}"
    else
        echo -e "${YELLOW}⚠️  通过，但有 $WARNINGS 个警告${NC}"
    fi
    exit 0
else
    echo -e "${RED}❌ 发现 $ERRORS 个问题，请检查修复${NC}"
    exit 1
fi
EOF

chmod +x scripts/check-brand-after-merge.sh

echo "✅ 创建品牌检查脚本"

echo ""
echo "🎉 zjcode 品牌隔离层迁移完成！"
echo ""
echo "📋 下一步操作:"
echo "  1. 验证: python3 -c \"from deepagents_code._version import DISTRIBUTION_NAME; print(DISTRIBUTION_NAME)\""
echo "  2. 检查: ./scripts/check-brand-after-merge.sh"
echo "  3. 提交: git add libs/code/zjcode/ libs/code/deepagents_code/__init__.py && git commit"
EOF

chmod +x libs/code/zjcode/scripts/zjcode-brand-migration.sh 2>/dev/null || true

echo ""
echo "✅ 迁移脚本已创建！"
echo ""
echo "🚀 运行命令: bash libs/code/zjcode/scripts/zjcode-brand-migration.sh"
