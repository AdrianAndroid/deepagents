# zjcode Skill 加载原理与链路分析

## 问题背景

用户发现：
1. zjcode 如何读取项目级目录的 skill？
2. 如何使用 skill？
3. 为什么在使用时没有发现 `skill(xxx)` 出现在 system prompt 中？

## 核心结论（先说结论）

存在 **两个独立问题** 导致 skill 不可见：

### 问题 1：路径分裂（Split-Brain）Bug

zjcode 品牌迁移后，项目级 skill 目录存在两条不同的解析路径，指向不同的目录：

| 代码路径 | 使用的函数 | 解析结果 | 用途 |
|---|---|---|---|
| **中间件**（agent.py -> PluginSkillsMiddleware） | `ProjectContext.project_skills_dir()` | `{project_root}/.zjcode/skills/` | 注入 system prompt |
| **CLI/TUI 发现**（invocation.py -> discover_skills_and_roots） | `Settings.get_project_skills_dir()` | `{project_root}/.deepagents/skills/` | `/skill:` 命令、自动补全 |

**根因**：`config.py:2829` 硬编码了 `".deepagents"`，而 `project_utils.py:87` 使用被品牌补丁修改后的 `PROJECT_DOTDIR = ".zjcode"`。

### 问题 2：缺少 YAML Frontmatter

`.zjcode/skills/zjcode-brand-migration/SKILL.md` 文件 **没有 YAML frontmatter**（以 `# zjcode Brand Migration Skill` 开头），导致 SDK 的 `_parse_skill_metadata()` 解析失败、返回 `None`，skill 被静默丢弃。

---

## 详细链路分析

### 一、Skill 源目录体系（8 层优先级，从低到高）

```
0. Built-in:        <package>/built_in_skills/
1. Plugin:          命名空间（plugin_id:skill_name）
2. User Deepagents: ~/.deepagents/{agent_name}/skills/
3. User Agents:     ~/.agents/skills/
4. Project Deepagents: {project_root}/.deepagents/skills/  ← config.py 硬编码
   OR               {project_root}/.zjcode/skills/          ← project_utils.py（品牌补丁后）
5. Project Agents:  {project_root}/.agents/skills/
6. User Claude:     ~/.claude/skills/（实验性）
7. Project Claude:  {project_root}/.claude/skills/（实验性）
```

同名 skill：高优先级覆盖低优先级（last-one-wins）。

### 二、两条加载链路

#### 链路 A：中间件路径（Runtime Middleware -> System Prompt）

```
agent.py (enable_skills=True)
  │
  ├─ 获取 project_skills_dir:
  │   project_context.project_skills_dir()  ->  {project_root}/.zjcode/skills/
  │   （当 project_context 不为 None 时）
  │
  ├─ 构建 sources 列表:
  │   [(built_in, "Built-in"),
  │    (plugin_sources...),
  │    (user_skills_dir, "User Deepagents"),
  │    (user_agent_skills_dir, "User Agents"),
  │    (project_skills_dir, "Project Deepagents"),   ← .zjcode/skills/
  │    (project_agent_skills_dir, "Project Agents"),
  │    (user_claude, "User Claude"),
  │    (project_claude, "Project Claude")]
  │
  └─ PluginSkillsMiddleware(sources=sources)
        │
        ├─ before_agent() / abefore_agent()
        │     │
        │     ├─ 遍历每个 source
        │     │   ├─ 无 namespace: sdk_skills._list_skills_with_errors(backend, path)
        │     │   │     ├─ backend.ls(source_path)          ← 列出子目录
        │     │   │     ├─ 对每个子目录 download SKILL.md
        │     │   │     └─ _parse_skill_metadata(content)   ← 解析 YAML frontmatter
        │     │   │         ├─ 无 frontmatter -> 返回 None -> 静默丢弃
        │     │   │         ├─ name 不匹配目录名 -> 警告但仍加载
        │     │   │         └─ 成功 -> SkillMetadata
        │     │   └─ 有 namespace: load_namespaced_skills() -> 递归发现
        │     │
        │     ├─ merge_skill()  ← 按名字合并，last-one-wins
        │     └─ 返回 SkillsStateUpdate(skills_metadata=[...])
        │
        └─ modify_request()
              │
              ├─ _format_skills_list(skills_metadata)
              │     -> "- **{name}**: {description}..."
              │     -> "  -> Read `{path}` for full instructions"
              │
              └─ append_to_system_message(skills_section)
                    -> 注入到 system prompt 的 "## Skills System" 部分
```

**关键**：如果 `_parse_skill_metadata()` 返回 `None`（如缺少 frontmatter），该 skill **不会** 出现在 system prompt 中，也不会有任何错误提示给用户——只在日志中有 `WARNING`。

#### 链路 B：CLI/TUI 发现路径（Slash Command -> Invocation）

```
app.py (_discover_skills)
  │
  ├─ _discover_skills_and_roots()
  │     │
  │     ├─ discover_plugin_skill_state()  ← 获取插件 skill 源
  │     │
  │     └─ invocation.discover_skills_and_roots(assistant_id, ...)
  │           │
  │           ├─ settings.get_built_in_skills_dir()    ← <package>/built_in_skills/
  │           ├─ settings.get_user_skills_dir(agent_id) ← ~/.deepagents/{agent}/skills/
  │           ├─ settings.get_project_skills_dir()      ← {project_root}/.deepagents/skills/  硬编码
  │           ├─ settings.get_user_agent_skills_dir()   ← ~/.agents/skills/
  │           ├─ settings.get_project_agent_skills_dir()← {project_root}/.agents/skills/
  │           ├─ settings.get_user_claude_skills_dir()  ← ~/.claude/skills/
  │           └─ settings.get_project_claude_skills_dir()← {project_root}/.claude/skills/
  │
  │     └─ skills/load.py list_skills(sources...)
  │           │
  │           ├─ 对每个 source 目录:
  │           │   ├─ FilesystemBackend(root_dir=skill_dir)
  │           │   ├─ list_skills_from_backend(backend, ".")
  │           │   │     └─ _list_skills_with_errors(backend, ".")
  │           │   │           ├─ ls(".") -> 列出子目录
  │           │   │           ├─ download SKILL.md for each
  │           │   │           └─ _parse_skill_metadata()  ← 同样需要 frontmatter
  │           │   └─ merge_skill()  ← last-one-wins
  │           │
  │           └─ 返回 list[ExtendedSkillMetadata]
  │
  ├─ build_skill_commands(skills)  ← 生成 /skill:<name> 自动补全条目
  │
  └─ _invoke_skill(skill_name, args)  ← 用户执行 /skill:<name> 时
        │
        ├─ 从缓存 _discovered_skills 查找
        │   （缓存未命中时重新 discover_skills_and_roots）
        │
        ├─ load_skill_content(skill_path, allowed_roots)
        │     ├─ Path.resolve() 路径安全检查
        │     ├─ containment check（防止 symlink 逃逸）
        │     └─ 读取 SKILL.md 原文
        │
        └─ build_skill_invocation_envelope(skill, content, args)
              │
              └─ 组装 prompt:
                  "I'm invoking the skill `{name}`.
                   Below are the full instructions from the skill's SKILL.md file.
                   Follow these instructions to complete the task.
                   ---
                   {content}
                   ---
                   **User request:** {args}"
              -> 作为 HumanMessage 发送给 agent
```

### 三、品牌补丁对路径的影响

```
zjcode/brand.py
  PROJECT_DOTDIR = ".zjcode"

zjcode/patches.py
  apply_brand_patches()
    setattr(_constants, "PROJECT_DOTDIR", ".zjcode")
    ← 运行时修改 _constants 模块属性

受影响的代码：
  OK  project_utils.py:87  -> self.project_root / PROJECT_DOTDIR / "skills"  -> .zjcode/skills/
  BUG config.py:2829        -> self.project_root / ".deepagents" / "skills"  -> .deepagents/skills/  ← 硬编码
```

### 四、当前项目的实际状态

| 目录 | 存在 | 有 Frontmatter | 中间件能发现 | CLI 能发现 |
|---|---|---|---|---|
| `.zjcode/skills/zjcode-brand-migration/` | YES | NO | 能找到目录但被丢弃 | NO |
| `.deepagents/skills/publish-zjcode-version/` | YES | YES | NO | YES |
| `~/.deepagents/agent/skills/` | YES (空) | - | YES | YES |
| Built-in skills (3个) | YES | YES | YES | YES |

**结果**：
- `zjcode-brand-migration`：中间件找到了目录但 SKILL.md 没有 frontmatter -> 被丢弃 -> 不在 system prompt
- `publish-zjcode-version`：CLI 能发现（`/skill:publish-zjcode-version` 可用），但中间件找不到（去 `.zjcode/skills/` 找了）-> 不在 system prompt

### 五、SKILL.md 规范要求

```markdown
---
name: my-skill-name          # 必填，必须与父目录名一致，小写字母+连字符
description: What it does    # 必填，最长 1024 字符
license: MIT                 # 可选
compatibility: ...           # 可选，最长 500 字符
metadata:                    # 可选，键值对
  key: value
allowed-tools: tool1 tool2   # 可选
---

# Skill Title

正文内容...
```

**没有 YAML frontmatter 的 SKILL.md 会被静默丢弃**，只在日志中留 `WARNING: Skipping ...: no valid YAML frontmatter found`。

### 六、Skill 的两种使用方式

#### 方式 1：模型自主调用（System Prompt 注入）

中间件将 skill 列表注入 system prompt，模型看到后：
1. 识别任务匹配某个 skill 的 description
2. 用 `read_file(skill_path, limit=1000)` 读取完整 SKILL.md
3. 按照 SKILL.md 中的指令执行
4. 使用 skill 目录中的辅助脚本（用绝对路径）

#### 方式 2：用户手动调用（/skill: 命令）

```
/skill:publish-zjcode-version 发布 0.2.5
```

TUI 拦截命令 -> 查找 skill -> 读取 SKILL.md -> 组装 prompt -> 发送给 agent。

静态别名：
- `/remember` = `/skill:remember`
- `/skill-creator` = `/skill:skill-creator`

### 七、修复建议

#### 修复 1：统一 project skills 目录路径

`config.py:2829` 应该使用 `PROJECT_DOTDIR` 而非硬编码 `".deepagents"`：

```python
# config.py - 修复前
def get_project_skills_dir(self) -> Path | None:
    if not self.project_root:
        return None
    return self.project_root / ".deepagents" / "skills"  # ← 硬编码

# config.py - 修复后
def get_project_skills_dir(self) -> Path | None:
    if not self.project_root:
        return None
    from deepagents_code._constants import PROJECT_DOTDIR
    return self.project_root / PROJECT_DOTDIR / "skills"  # ← 动态
```

同样需要修复 `get_project_agents_dir()`（config.py:2864）。

**或者**：统一到只使用一条路径——要么全用 `.zjcode`，要么全用 `.deepagents`。建议统一用 `.zjcode`（品牌迁移后的正确值）。

#### 修复 2：为 zjcode-brand-migration 添加 Frontmatter

```markdown
---
name: zjcode-brand-migration
description: "zjcode 品牌隔离层迁移工具，一键解决合并 main 分支的品牌冲突问题"
license: MIT
compatibility: designed for zjcode
---

# zjcode Brand Migration Skill
...
```

#### 修复 3：统一 skill 目录

将 `.deepagents/skills/publish-zjcode-version/` 移到 `.zjcode/skills/`，或修复路径后两处都能发现。

---

## 完整调用链路图

```
                    zjcode 启动
                        |
            +-----------+-----------+
            v                       v
     品牌补丁应用               Settings 初始化
     patches.py                config.py
     PROJECT_DOTDIR            project_root = find_git_root()
       = ".zjcode"             get_project_skills_dir()
                                 -> .deepagents/skills/  [硬编码BUG]
            |                       |
            v                       v
  +-------------------+     +---------------------------+
  | agent.py          |     | app.py / non_interactive  |
  | enable_skills     |     | _discover_skills()        |
  |                   |     |                           |
  | uses ProjectCtx   |     | uses Settings             |
  | .project_skills   |     | .get_project_             |
  | _dir()            |     |  skills_dir()             |
  | -> .zjcode/       |     | -> .deepagents/           |
  |   skills/         |     |   skills/                 |
  +--------+----------+     +------------+--------------+
           |                             |
           v                             v
  PluginSkillsMiddleware        list_skills()
  before_agent()                load.py
           |                             |
           v                             v
  _list_skills_with_           _list_skills_with_
    errors(backend,              errors(backend,
    ".zjcode/skills/")           ".deepagents/skills/")
           |                             |
           v                             v
  _parse_skill_metadata        _parse_skill_metadata
  (需要 YAML frontmatter)      (需要 YAML frontmatter)
           |                             |
           v                             v
  modify_request()             build_skill_commands()
  -> system prompt              -> /skill: autocomplete
  "## Skills System"            -> _invoke_skill()
```

## 关键文件索引

| 文件 | 作用 |
|---|---|
| `libs/code/deepagents_code/agent.py:2613-2660` | 构建 sources 列表，创建 PluginSkillsMiddleware |
| `libs/code/deepagents_code/agent.py:2386-2403` | 获取 project_skills_dir（两条路径分叉点） |
| `libs/code/deepagents_code/config.py:2821-2829` | `get_project_skills_dir()` 硬编码 `.deepagents` |
| `libs/code/deepagents_code/project_utils.py:83-87` | `ProjectContext.project_skills_dir()` 使用 `PROJECT_DOTDIR` |
| `libs/code/deepagents_code/skills/load.py:48-163` | `list_skills()` CLI 发现逻辑 |
| `libs/code/deepagents_code/skills/invocation.py:28-82` | `discover_skills_and_roots()` TUI 发现逻辑 |
| `libs/code/deepagents_code/skills/invocation.py:85-120` | `build_skill_invocation_envelope()` 调用时组装 prompt |
| `libs/code/deepagents_code/skills/trust.py` | Skill 信任存储（symlink 安全） |
| `libs/code/deepagents_code/plugins/adapters/skills_middleware.py` | PluginSkillsMiddleware 实现 |
| `libs/deepagents/deepagents/middleware/skills.py:371-470` | `_parse_skill_metadata()` YAML frontmatter 解析 |
| `libs/deepagents/deepagents/middleware/skills.py:721-761` | `SKILLS_SYSTEM_PROMPT` 模板 |
| `libs/deepagents/deepagents/middleware/skills.py:900-926` | `modify_request()` 注入 system prompt |
| `libs/code/zjcode/brand.py:22` | `PROJECT_DOTDIR = ".zjcode"` |
| `libs/code/zjcode/patches.py:20-57` | `apply_brand_patches()` 运行时补丁 |
| `libs/code/deepagents_code/command_registry.py:431-520` | `/skill:` 命令解析与自动补全生成 |

## 涉及的核心类和函数

### SDK 层（deepagents）

- `SkillsMiddleware` - 基础 skill 中间件，负责 `before_agent` 加载 + `modify_request` 注入
- `SkillMetadata` - TypedDict，包含 name/description/path/license/compatibility/metadata/allowed_tools
- `_parse_skill_metadata()` - 解析 SKILL.md 的 YAML frontmatter，无 frontmatter 返回 None
- `_list_skills_with_errors()` - 列出 source 目录下的所有 skill
- `SKILLS_SYSTEM_PROMPT` - 注入 system prompt 的模板字符串

### zjcode 层（deepagents_code）

- `PluginSkillsMiddleware` - 继承 SkillsMiddleware，增加 plugin namespace 支持
- `Settings.get_project_skills_dir()` - 硬编码 `.deepagents/skills/`（BUG）
- `ProjectContext.project_skills_dir()` - 使用 `PROJECT_DOTDIR`（`.zjcode/skills/`）
- `discover_skills_and_roots()` - TUI 启动时的 skill 发现入口
- `build_skill_invocation_envelope()` - `/skill:xxx` 调用时组装 prompt
- `load_skill_content()` - 读取 SKILL.md 原文，含安全检查
- `apply_brand_patches()` - 运行时修改 `_constants.PROJECT_DOTDIR` 为 `.zjcode`
