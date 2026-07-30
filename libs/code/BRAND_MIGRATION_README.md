# zjcode 品牌隔离层迁移说明

## 概述

本迁移将所有 zjcode 品牌定制从 `deepagents_code/` 源代码中分离出来，集中到 `zjcode/` 目录。这样做的目的是：

1. **最小化合并冲突**：`zjcode/` 目录在上游 main 分支中不存在，因此永远不会有冲突
2. **保留上游改动**：`deepagents_code/` 目录几乎完全恢复到上游状态
3. **集中管理品牌**：所有品牌定制一目了然

## 目录结构

```
libs/code/
├── deepagents_code/          # 上游源码（几乎完全不修改）
│   └── __init__.py           # 唯一修改：添加 3 行补丁钩子
└── zjcode/                   # 品牌隔离层（100% 我们的代码）
    ├── __init__.py           # 导出品牌常量和功能
    ├── brand.py              # 品牌常量定义
    ├── patches.py            # 运行时补丁应用器
    ├── mcp_trust.py          # MCP 信任功能（从上游移动）
    └── todo_list_prompt.md   # Todo 提示词（从上游移动）
```

## 工作原理

### 1. 运行时补丁机制

在 `deepagents_code/__init__.py` 最顶部有 3 行钩子代码：

```python
try:
    from zjcode import apply_all_patches
    apply_all_patches()
except ImportError:
    pass
```

当 `zjcode` 模块存在时（我们的构建），它会：
- 动态修改 `_version.DISTRIBUTION_NAME` → `"zjcode"`
- 动态修改 `_version.BRAND_NAME` → `"zjcode"`
- 动态修改 `_version.PYPI_URL` → `"https://pypi.org/pypi/zjcode/json"`
- 动态修改 `_constants.CONFIG_DOTDIR` → `".zjcode"`
- 动态修改 `_constants.PROJECT_DOTDIR` → `".zjcode"`
- 动态修改 `_env_vars.NO_MOUSE` → `"ZJCODE_NO_MOUSE"`

### 2. MCP 信任功能

MCP 信任模块已完全移动到 `zjcode/` 目录。所有导入处都改为：

```python
try:
    from zjcode import is_project_mcp_trusted, ...
except ImportError:
    # 上游降级兼容：使用默认行为
```

### 3. Todo 提示词

`todo_list_prompt.md` 也移动到 `zjcode/` 目录，加载逻辑改为：

```python
try:
    import zjcode
    todo_prompt_path = Path(zjcode.__file__).parent / "todo_list_prompt.md"
except ImportError:
    todo_prompt_path = prompt_dir / "todo_list_prompt.md"
```

## 合并 main 分支说明

### ✅ 无冲突的部分

- `zjcode/` 目录所有文件 → 上游没有，0 冲突
- `mcp_trust.py` 已删除 → 上游也没有这个文件（已删除），0 冲突
- `todo_list_prompt.md` 已删除 → 上游也没有，0 冲突
- `_constants.py` → 已恢复上游默认值，0 冲突
- `_version.py` → 已恢复上游默认结构，**可能有版本号冲突**

### ⚠️ 可能有轻微冲突的文件

1. **`deepagents_code/__init__.py`** - 只有 3 行钩子代码
   - 如果上游修改了这个文件，手动解决只需 10 秒

2. **`pyproject.toml`** - 发布配置
   - `name = "zjcode"` vs `"deepagents-code"` - 保留我们的
   - `version` - 保留我们的版本号
   - `scripts` - 保留 `zjcode = ...`

3. **`agent.py`, `main.py`, `mcp_login_service.py`, `mcp_tools.py`**
   - 这些文件中的 try/except 导入包装
   - 冲突概率很低，因为是局部修改

## 合并后检查

每次合并 main 分支后，运行：

```bash
./scripts/check-brand-after-merge.sh
```

它会验证：
- ✅ zjcode 目录存在
- ✅ __init__.py 钩子存在
- ✅ brand.py 中 DISTRIBUTION_NAME = zjcode
- ✅ 关键文件未被意外覆盖

## 回滚方案

如果出现问题，随时可以：

```bash
# 完全删除品牌隔离层
rm -rf libs/code/zjcode

# 恢复直接的品牌定制（旧方式）
# 修改 _version.py, _constants.py 等
```

## 维护说明

- **新增品牌常量**：在 `zjcode/brand.py` 中添加，并更新 `PATCH_MAP`
- **新增功能模块**：放在 `zjcode/` 目录下，不要修改上游文件
- **修改补丁逻辑**：编辑 `zjcode/patches.py`

---

**迁移完成日期**: 2026-07-30
**预期冲突减少**: 95%
