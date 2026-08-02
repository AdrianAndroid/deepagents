# Deep Agents Skill 系统原理与加载机制

## 一、概述

Skill 系统是 Deep Agents 的核心扩展机制，通过**渐进式披露（Progressive Disclosure）**模式为 Agent 提供领域知识和工作流指导。Skill 遵循 [Agent Skills Specification](https://agentskills.io/specification) 规范。

## 二、整体架构

```
                    ┌─────────────────────────────────────────┐
                    │          系统提示 (System Prompt)         │
                    │  ┌─────────────────────────────────────┐ │
                    │  │         Skills 系统说明               │ │
                    │  │  ┌───────────────────────────────┐  │ │
                    │  │  │    可用技能列表（名称+描述）    │  │ │
                    │  │  │    → 按需读取完整 SKILL.md     │  │ │
                    │  │  └───────────────────────────────┘  │ │
                    │  └─────────────────────────────────────┘ │
                    └─────────────────────────────────────────┘
                                      ↓
                          ┌───────────────────┐
                          │  SkillsMiddleware │
                          └─────────┬─────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
┌─────────▼─────────┐   ┌───────────▼───────────┐   ┌─────────▼─────────┐
│   SDK 核心模块    │   │  Code Plugin 适配器   │   │   CLI 命令模块    │
│ deepagents/middle │   │ plugins/adapters/     │   │ skills/commands.py│
│ ware/skills.py    │   │ skills.py             │   │ skills/load.py    │
└───────────────────┘   └───────────────────────┘   └───────────────────┘
```

## 三、Skill 文件结构

### 3.1 目录结构

每个 Skill 是一个独立目录，必须包含 `SKILL.md` 文件：

```
skill-name/
├── SKILL.md          # 必需：YAML frontmatter + Markdown 说明
├── helper.py         # 可选：辅助脚本
├── scripts/          # 可选：子目录
└── examples/         # 可选：示例文件
```

### 3.2 SKILL.md 格式

采用 YAML frontmatter + Markdown 正文格式：

```markdown
---
name: skill-name                      # 技能标识符（1-64字符）
description: 技能描述，说明用途场景    # 1-1024字符
license: MIT                          # 可选：许可证
compatibility: Python 3.10+           # 可选：兼容性要求
metadata:                             # 可选：自定义元数据
  key: value
allowed_tools: [read_file, execute]   # 可选：推荐工具列表
---

# Skill 完整说明文档

## 使用场景
...

## 工作流程
...

## 示例
...
```

### 3.3 命名规范验证

`_validate_skill_name()` 函数执行以下检查：
- 长度：1-64 字符
- 字符：小写字母、数字、连字符（`a-z`, `0-9`, `-`）
- 不能以连字符开头或结尾
- 不能包含连续连字符
- **必须与所在目录名一致**

## 四、Skill 源（Sources）与优先级

Skill 从多个目录分层加载，**后面的源覆盖前面的**（Last One Wins）。

### 4.1 优先级顺序（低 → 高）

| 优先级 | 源路径 | 说明 | 标签 |
|--------|--------|------|------|
| 0 | `<package>/built_in_skills/` | 内置技能 | Built-in |
| 1 | Plugin skill directories | 插件技能 | Plugin: {id} |
| 2 | `~/.zjcode/{agent}/skills/` | 用户技能 | User |
| 3 | `~/.agents/skills/` | 用户共享技能 | User |
| 4 | `.zjcode/skills/` | 项目技能 | Project |
| 5 | `.agents/skills/` | 项目共享技能 | Project |
| 6 | `~/.claude/skills/` | Claude兼容（实验性） | Claude (experimental) |
| 7 | `.claude/skills/` | 项目Claude（实验性） | Claude (experimental) |

### 4.2 源的表示形式

每个源可以是：
- **裸路径**：`"/skills/user/"` → 标签自动从路径推导
- **元组形式**：`(path, label)` → 显式指定标签，用于区分叶子目录名相同的源

## 五、核心模块详解

### 5.1 SDK 核心：`deepagents/middleware/skills.py`

#### 5.1.1 `SkillMetadata` 数据结构

```python
class SkillMetadata(TypedDict):
    path: str                    # SKILL.md 文件路径
    name: str                    # 技能名称
    description: str             # 描述
    license: str | None          # 许可证
    compatibility: str | None    # 兼容性
    metadata: dict[str, str]     # 自定义元数据
    allowed_tools: list[str]     # 推荐使用的工具
```

#### 5.1.2 `SkillsMiddleware` 中间件

**工作流程：**

```
before_agent() / abefore_agent()
        ↓
  检查 state["skills_metadata"] 是否已存在
        ↓ （不存在则加载）
  遍历所有 sources
        ↓
  _list_skills_with_errors() → 扫描子目录
        ↓
  下载所有 SKILL.md → _skill_metadata_from_response()
        ↓
  解析 YAML frontmatter → _parse_skill_metadata()
        ↓
  合并技能（同名后加载的覆盖先加载的）
        ↓
  更新 state["skills_metadata"]


modify_request() / wrap_model_call()
        ↓
  格式化技能列表注入系统提示
```

**关键方法：**

| 方法 | 作用 |
|------|------|
| `before_agent()` | 同步加载技能元数据到 state |
| `abefore_agent()` | 异步版本 |
| `modify_request()` | 将技能说明注入系统提示 |
| `_format_skills_list()` | 格式化技能列表展示 |

#### 5.1.3 解析流程

```
_skill_metadata_from_response()
        ↓
  检查响应错误 → 非 file_not_found 警告
        ↓
  UTF-8 解码内容
        ↓
_parse_skill_metadata()
        ↓
  ├─ 匹配 YAML frontmatter (--- 分隔)
  ├─ yaml.safe_load() 解析
  ├─ 提取 name, description, license, compatibility
  ├─ 解析 allowed_tools（支持逗号/空格分隔或列表）
  └─ 验证 name 格式与目录名一致
```

### 5.2 Plugin 适配器：`plugins/adapters/skills.py`

扩展 SDK 的单级扫描为**递归多级扫描**，支持嵌套技能目录：

```
source/
├── foo/
│   └── bar/
│       └── skill1/        → 命名: plugin_id:foo:bar:skill1
│           └── SKILL.md
└── baz/
    └── skill2/            → 命名: plugin_id:baz:skill2
        └── SKILL.md
```

#### 5.2.1 `PluginSkillsMiddleware`

继承并扩展 `SkillsMiddleware`：
- 对带 namespace 的源使用递归扫描 (`discover_skill_dirs`)
- 对嵌套目录的技能名称添加 `:` 分隔的命名空间前缀
- 保持与 SDK 相同的合并逻辑

### 5.3 CLI 加载器：`skills/load.py`

为 CLI 命令（`/skills list`, `/skills info`）提供文件系统直接访问能力：
- 使用 `FilesystemBackend` 绕过后端抽象
- 支持实验性 Claude 兼容路径
- 每个源独立 try/except，单个源失败不影响整体

## 六、渐进式披露（Progressive Disclosure）

### 6.1 设计理念

为了避免在系统提示中塞入大量技能全文，采用"元数据先行，按需读取"模式：

1. **初始加载**：仅读取 SKILL.md 的 YAML frontmatter（名称、描述）
2. **系统提示注入**：列出所有可用技能的名称和描述，并给出路径
3. **按需读取**：Agent 判断需要使用某技能时，主动调用 `read_file` 读取完整内容

### 6.2 系统提示模板

```markdown
## Skills System

You have access to a skills library that provides specialized capabilities...

**Built-in Skills**: `/path/to/built_in_skills/` (higher priority)
**User Skills**: `~/.zjcode/deepagents-code/skills/`

**Available Skills:**

- **web-research**: 结构化的网络研究方法 (License: MIT)
  -> Read `/path/to/built_in_skills/web-research/SKILL.md` for full instructions

**How to Use Skills:**
1. Recognize when a skill applies
2. Read the skill's full instructions with read_file
3. Follow the skill's instructions
4. Access supporting files
```

## 七、错误处理与安全边界

### 7.1 加载错误处理

- **源级别错误**：如目录不存在、权限不足 → 记录警告并继续
- **单个技能错误**：YAML 解析失败、命名违规 → 跳过该技能并警告
- **展示限制**：系统提示中最多显示 20 条警告，每条截断为 1000 字符

### 7.2 安全防护

1. **路径包含检查**：`load_skill_content()` 验证路径在 `allowed_roots` 内
2. **最大文件大小**：SKILL.md 最大 10MB，防止 DoS
3. **.env 注入防护**：项目 `.env` 不能注入危险环境变量（`PATH`, `PYTHONPATH`, `LD_PRELOAD` 等）
4. **HTML 转义**：警告信息经过 `html.escape()` 和 `json.dumps()` 双重转义

## 八、关键源码位置

| 模块 | 文件路径 | 核心功能 |
|------|----------|----------|
| SDK 中间件 | `libs/deepagents/deepagents/middleware/skills.py` | 核心加载逻辑、系统提示注入 |
| Plugin 适配器 | `libs/code/deepagents_code/plugins/adapters/skills.py` | 插件技能源提取 |
| Plugin 中间件 | `libs/code/deepagents_code/plugins/adapters/skills_middleware.py` | 递归扫描、命名空间 |
| CLI 加载器 | `libs/code/deepagents_code/skills/load.py` | CLI 命令用文件系统加载 |
| 配置 | `libs/code/deepagents_code/config.py` | 技能目录路径解析 |
| 合并逻辑 | `libs/code/deepagents_code/skills/merge.py` | 技能冲突合并 |

## 九、初始化流程（以 agent.py 为例）

```python
# 1. 构建 sources 列表
sources = [
    (str(settings.get_built_in_skills_dir()), "Built-in"),
    (str(user_skills_dir), "User"),
    (str(project_skills_dir), "Project"),
]

# 2. 添加插件技能源
sources.extend(plugin_skill_sources(plugin_result.plugins))

# 3. 创建 PluginSkillsMiddleware
middleware = PluginSkillsMiddleware(
    backend=filesystem_backend,
    sources=sources,
)

# 4. 添加到中间件栈
middleware_stack.append(middleware)
```

## 十、总结

Skill 系统的设计要点：

1. **分层加载**：多源按优先级叠加，后加载覆盖先加载
2. **渐进披露**：元数据先行，按需读取全文，节省 token
3. **插件扩展**：支持递归扫描和命名空间，适配插件生态
4. **容错设计**：单个技能/源失败不影响整体，优雅降级
5. **安全边界**：路径包含检查、大小限制、转义防护
