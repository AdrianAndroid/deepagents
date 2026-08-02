# Deep Agents 工具列表

## 概述

Deep Agents 提供了一组内置工具，用于文件操作、命令执行、网络请求、对话管理等场景。所有工具通过 Agent 中间件暴露给大语言模型使用。

## 分类

### 1. 文件系统工具 (Filesystem Tools)

| 工具名 | 描述 |
|--------|------|
| `ls` | 列出目录中的所有文件 |
| `read_file` | 从文件系统读取文件内容，支持分页读取大文件 |
| `write_file` | 写入内容到文件，文件不存在则创建，存在则完全覆盖 |
| `edit_file` | 在文件中执行精确的字符串替换 |
| `delete` | 从文件系统删除文件或目录 |
| `glob` | 使用 glob 模式查找文件，返回绝对路径 |
| `grep` | 在文件中搜索字面文本模式（非正则表达式） |

### 2. 命令执行工具

| 工具名 | 描述 |
|--------|------|
| `execute` | 在隔离的沙箱中执行 shell 命令，返回合并的 stdout/stderr 和退出码（内容过大时会截断） |

### 3. 子代理与任务管理

| 工具名 | 描述 |
|--------|------|
| `task` | 启动临时子代理，在隔离的上下文窗口中处理复杂的多步骤任务 |
| `compact_conversation` | 压缩对话，将旧消息总结为简洁摘要。当对话过长时主动使用以释放上下文空间 |

### 4. 目标与评分管理

| 工具名 | 描述 |
|--------|------|
| `get_rubric` | 当最新状态通知表明评分规则处于活动状态时，读取评分标准 |
| `get_goal` | 当最新状态通知表明目标可执行时，读取目标详情 |
| `update_goal` | 仅当最新状态通知表明目标可执行时更新目标 |

### 5. 用户交互

| 工具名 | 描述 |
|--------|------|
| `ask_user` | 需要澄清或输入时向用户提问，支持单选和文本输入 |

### 6. 网络工具

| 工具名 | 描述 |
|--------|------|
| `fetch_url` | 获取 URL 并将页面内容转换为 Markdown 格式 |
| `web_search` | 使用 Tavily 搜索网络获取最新信息（需要配置 API 密钥） |

### 7. 调试与追踪

| 工具名 | 描述 |
|--------|------|
| `get_current_thread_id` | 获取当前 zjcode 线程 ID，用于 LangSmith 追踪或 MCP 工具 |

## 工具来源说明

- **Built-in**: 以上所有工具均为 zjcode 内置工具，在 Agent 编译时绑定
- **MCP Tools**: 通过 MCP（Model Context Protocol）配置的第三方服务器提供额外工具，工具集取决于具体的 MCP 服务器配置

## 相关源码文件

| 文件 | 功能 |
|------|------|
| `libs/deepagents/deepagents/middleware/filesystem.py` | 文件系统工具定义与实现 |
| `libs/code/deepagents_code/tools.py` | 自定义工具（web_search, fetch_url, get_current_thread_id） |
| `libs/code/deepagents_code/tool_catalog.py` | 工具枚举与目录构建 |

## 工具配置限制

- `web_search` 需要配置 `TAVILY_API_KEY` 环境变量才能使用
- 文件系统工具可以通过 `fs_tools` 参数进行白名单配置
- `execute` 工具的沙箱行为受后端配置影响

---

## Skill 调用机制（重要！）

**Skill 没有专用的调用工具。** Skill 系统采用**渐进式披露（Progressive Disclosure）**设计模式：

### 调用流程

1. **发现阶段** - Skill 元数据（name, description, path）被注入到系统提示中
2. **按需读取** - Agent 决定使用某个 Skill 时，使用标准的 `read_file` 工具读取该 Skill 的 `SKILL.md` 文件
3. **执行指令** - Agent 按照 SKILL.md 中的步骤说明完成任务
4. **辅助资源** - Skill 目录中的脚本、配置等文件也通过标准文件工具（`read_file`, `execute` 等）访问

### 为什么没有 `invoke_skill` 工具？

- **轻量设计**：Skill 本质是 Markdown 指令文档，不需要特殊执行引擎
- **透明可控**：Agent 全程可见 Skill 的完整内容，用户也能看到调用过程
- **复用现有工具**：直接使用 `read_file`、`execute` 等已有工具，无需额外的 API 表面
- **Progressive Disclosure**：Skill 内容只在需要时才加载到上下文中，节省 token

### 示例：Skill 调用序列

```
1. 系统提示告知有 "remember" skill，路径为 /path/remember/SKILL.md
2. Agent 决定使用 remember skill
3. Agent 调用: read_file(file_path="/path/remember/SKILL.md", limit=1000)
4. Agent 根据 SKILL.md 的指令执行后续操作（可能包括调用其他工具）
```

### 相关源码

- `libs/deepagents/deepagents/middleware/skills.py` - SkillsMiddleware 实现与系统提示模板
- `libs/code/deepagents_code/skills/invocation.py` - Skill 调用信封构建（`build_skill_invocation_envelope`）
- `SKILLS_SYSTEM_PROMPT` - 包含完整的 Skill 使用说明
