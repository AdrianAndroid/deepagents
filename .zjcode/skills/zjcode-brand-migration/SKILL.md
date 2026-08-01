---
name: zjcode-brand-migration
description: "zjcode 品牌隔离层迁移工具，一键解决合并 main 分支的品牌冲突问题。Use this skill when the user says: (1) 品牌迁移, (2) brand migration, (3) 合并 main 后品牌冲突, (4) check brand after merge, (5) 品牌常量被覆盖."
license: MIT
compatibility: designed for zjcode
---

# zjcode Brand Migration Skill

## 描述

zjcode 品牌隔离层迁移工具，一键解决合并 main 分支的品牌冲突问题。

**核心原理**：物理隔离 + 动态注入，让品牌定制与上游代码在文件系统层面完全分离。

## 使用场景

- ✅ 每次合并 main 分支都有品牌相关冲突
- ✅ DISTRIBUTION_NAME, CONFIG_DOTDIR 等品牌常量经常被覆盖
- ✅ mcp_trust.py, todo_list_prompt.md 等专属文件经常被上游删除
- ✅ 想要集中管理所有品牌定制

## 快速开始

```bash
# 一键执行迁移
uv run -- zjcode-brand-migration
```

或者分步执行：

```bash
# Step 1: 创建品牌隔离层结构
python scripts/zjcode-brand-migration.py setup

# Step 2: 验证品牌常量是否生效
python scripts/zjcode-brand-migration.py verify

# Step 3: 合并后完整性检查
./scripts/check-brand-after-merge.sh
```

## 迁移效果

| 指标 | 迁移前 | 迁移后 |
|------|--------|--------|
| 品牌相关冲突 | 15+ 个文件 | 0 个核心文件冲突 |
| 解决冲突时间 | 30-60 分钟 | < 1 分钟 |
| 品牌定制位置 | 散落在 20+ 文件 | 集中在 zjcode/ 一个目录 |
| 上游代码污染 | 大量品牌硬编码 | 100% 纯净上游代码 |

## 文件结构

```
libs/code/zjcode/
├── __init__.py              # 导出品牌功能
├── brand.py                 # 所有品牌常量定义
├── patches.py               # 运行时补丁逻辑
├── mcp_trust.py             # MCP 信任模块（从 deepagents_code 移动）
├── todo_list_prompt.md      # Todo 提示词（从 deepagents_code 移动）
└── scripts/
    └── zjcode-brand-migration.sh  # 一键迁移脚本
```

## 合并操作指南

迁移后，每次合并 main 分支：

```bash
# 1. 开始合并
git fetch origin main
git merge origin/main

# 2. 解决品牌相关冲突（只有 2 个！10 秒搞定）
git add libs/code/zjcode/mcp_trust.py
git add libs/code/zjcode/todo_list_prompt.md

# 3. 解决其他非品牌相关冲突...

# 4. 验证品牌完整性
./scripts/check-brand-after-merge.sh

# 5. 提交合并
git commit
```

## 验证命令

```bash
# 验证品牌常量生效
python3 -c "
import sys
sys.path.insert(0, 'libs/code')
from deepagents_code._version import DISTRIBUTION_NAME, BRAND_NAME, PYPI_URL
from deepagents_code._constants import CONFIG_DOTDIR, PROJECT_DOTDIR

print('DISTRIBUTION_NAME:', DISTRIBUTION_NAME)
print('BRAND_NAME:', BRAND_NAME)
print('CONFIG_DOTDIR:', CONFIG_DOTDIR)
print('PROJECT_DOTDIR:', PROJECT_DOTDIR)
print('PYPI_URL:', PYPI_URL)
"
```

## 技术原理

### 第 1 层：物理文件隔离

```
libs/code/
├── deepagents_code/     ← 100% 上游代码，一行不改！
│   ├── _version.py      ← DISTRIBUTION_NAME = "deepagents-code"
│   ├── _constants.py    ← CONFIG_DOTDIR = ".deepagents"
│   └── __init__.py      ← 只加 3 行钩子
│
└── zjcode/              ← 100% 我们的代码，上游永远没有！
```

### 第 2 层：运行时动态补丁

```python
# zjcode/patches.py 启动时自动执行
def apply_brand_patches():
    # 找到目标模块
    import deepagents_code._version as version_module
    
    # 动态修改内存中的属性！不碰源码文件
    setattr(version_module, "DISTRIBUTION_NAME", "zjcode")
```

### 第 3 层：try/except 兼容包装

```python
# 优雅降级，上游删除也不崩溃
try:
    from zjcode import mcp_trust
except ImportError:
    mcp_trust = None
```

## 新增品牌定制

所有新的品牌定制都应该放在 `libs/code/zjcode/brand.py`：

```python
# 在 brand.py 中添加新的常量
MY_NEW_BRAND_CONSTANT = "zjcode-value"

# 在 PATCH_MAP 中添加补丁目标
PATCH_MAP = {
    "deepagents_code.some_module": {
        "MY_NEW_CONSTANT": "zjcode-value",
    },
}
```

## 常见问题

### Q: 补丁什么时候运行？

A: 在 `deepagents_code/__init__.py` 导入时立即运行，比任何业务代码都早。

### Q: 会影响上游代码吗？

A: 完全不会！所有修改都只在内存中，源码文件保持上游原样。

### Q: 如何回滚？

A: 删除 `libs/code/zjcode/` 目录，删除 `__init__.py` 中的 3 行钩子即可。

## 作者

zjcode Team

## 许可证

MIT
