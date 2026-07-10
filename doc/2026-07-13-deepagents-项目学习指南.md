# Deep Agents 项目学习指南

> **日期**: 2026-07-13
> **定位**: 一份面向开发者的 Deep Agents 项目全景学习指南，帮助你从零开始理解并掌握这个项目。

---

## 一、项目概述

### 1.1 什么是 Deep Agents？

Deep Agents 是一个基于 LangChain/LangGraph 的**开源 Agent Harness（代理框架）**。它的核心价值是：

- **开箱即用** — 一套经过调优的默认配置，适合长时序、多步骤的工作
- **可扩展** — 可以覆盖或替换任何组件，无需 Fork
- **模型无关** — 支持任何支持 tool calling 的 LLM
- **生产就绪** — 基于 LangGraph，拥有 streaming、持久化、checkpointing 等能力

### 1.2 核心三层架构

```
Deep Agents (上层 Harness)  ←  你在这里
    ↓
LangChain (Agent 抽象)      ←  model + tools + middleware → agent loop
    ↓
LangGraph (运行时)          ←  state、checkpointing、streaming、interrupts
```

### 1.3 核心特性一览

| 特性 | 说明 |
|------|------|
| **Sub-agents** | 委派任务给具有隔离上下文窗口的 agent |
| **Filesystem** | 读写编辑搜索，支持可插拔的 local/sandboxed/remote 后端 |
| **Context management** | 压缩长对话、将工具输出卸载到磁盘 |
| **Shell access** | 在选定的沙箱中运行命令 |
| **Persistent memory** | 可插拔的 state/store 后端，跨会话记忆 |
| **Human-in-the-loop** | 在工具执行前批准/编辑/拒绝 |
| **Skills** | 可复用的按需加载行为 |
| **Tools** | 自带工具或 MCP server |

---

## 二、代码仓库结构

这是一个 Python monorepo，包含多个独立版本管理的包：

```
deepagents/
├── libs/
│   ├── deepagents/    ← 核心 SDK（重点关注）
│   ├── code/          ← 终端编码 agent (dcode)
│   ├── cli/           ← 部署 CLI
│   ├── acp/           ← Agent Client Protocol
│   ├── evals/         ← 评估套件
│   ├── talon/         ← 实验性本地运行时
│   └── partners/      ← 合作伙伴集成（Daytona、Modal、Runloop、Vercel 等）
├── examples/          ← 面向用户的示例
└── .github/           ← CI/CD 工作流
```

### 2.1 各包职责

| 包 | 发行名 | 角色 |
|------|--------|------|
| `libs/deepagents` | `deepagents` | 核心 SDK，导出 `create_deep_agent`、`DeepAgentState`、middleware 等 |
| `libs/code` | `deepagents-code` | 预构建终端编码 agent（`dcode` / `deepagents-code`） |
| `libs/cli` | `deepagents-cli` | 部署和管理 CLI |
| `libs/acp` | `deepagents-acp` | ACP 协议适配器 |
| `libs/evals` | `deepagents-evals` | 行为评估套件 |

---

## 三、核心 SDK 深入解析

### 3.1 入口：`create_deep_agent()`

文件位置：`libs/deepagents/deepagents/graph.py`

这是整个项目的核心入口函数。调用链如下：

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-5.5",
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
)
result = agent.invoke({"messages": "Research LangGraph and write a summary"})
```

**`create_deep_agent()` 内部做了什么：**

1. **解析模型** — 通过 `resolve_model()` 将 `provider:model` 字符串解析为 `BaseChatModel` 实例
2. **应用 Harness Profile** — 根据模型匹配对应的 profile（如 Anthropic/OpenAI 等）
3. **验证 profile 排除规则** — 确保必需的 middleware 不能被移除
4. **工具描述覆盖** — 应用 `HarnessProfile` 的工具描述改写
5. **解析后端** — 默认使用 `StateBackend`
6. **处理子代理** — 解析 `SubAgent`、`CompiledSubAgent`、`AsyncSubAgent` 声明
7. **自动添加 general-purpose 子代理** — 除非禁用或覆盖
8. **组装 base middleware** — 核心中间件栈
9. **组合最终 system prompt** — USER → BASE/CUSTOM → SUFFIX 的顺序
10. **调用 `create_agent()`** — 交给 LangChain 创建 agent

**Default 工具集：**

- `write_todos` — 管理待办列表
- `ls`、`read_file`、`write_file`、`edit_file`、`glob`、`grep` — 文件操作
- `execute` — 运行 shell 命令（需要 SandboxBackend）
- `task` — 调用子代理

### 3.2 State：`DeepAgentState`

```python
class DeepAgentState(AgentState):
    messages: Required[Annotated[list[AnyMessage], DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)]]
```

这里使用 `DeltaChannel` 是关键优化 — 避免对话历史增长时的 O(N²) checkpoint 膨胀问题，将其降低到 O(N)。`snapshot_frequency=50` 表示每 50 次更新做一次快照。

### 3.3 Middleware 体系

Middleware 是 Deep Agents 的核心扩展机制，文件位于 `libs/deepagents/deepagents/middleware/`：

| Middleware | 文件 | 职责 |
|------|------|------|
| `FilesystemMiddleware` | `filesystem.py` | 文件系统工具 + 权限控制（**不可移除**） |
| `SubAgentMiddleware` | `subagents.py` | 子代理调度（**不可移除**） |
| `SkillsMiddleware` | `skills.py` | 技能加载 |
| `MemoryMiddleware` | `memory.py` | 记忆系统 |
| `AsyncSubAgentMiddleware` | `async_subagents.py` | 异步子代理 |
| `PatchToolCallsMiddleware` | `patch_tool_calls.py` | 工具调用修补 |
| `RubricMiddleware` | `rubric.py` | 评分标准 |

**Middleware 组装顺序：**

```
Base stack:
  1. TodoListMiddleware
  2. SkillsMiddleware (如果有 skills)
  3. FilesystemMiddleware
  4. SubAgentMiddleware (如果有子代理)
  5. SummarizationMiddleware
  6. MemoryMiddleware
  7. HumanInTheLoopMiddleware
  8. [用户自定义 middleware]
  9. Profile middleware
  10. Prompt caching middleware
```

**关键约束：** `FilesystemMiddleware` 和 `SubAgentMiddleware` 是**必需的**，`HarnessProfile.excluded_middleware` 不能移除它们。

### 3.4 Backend 体系

Backend 决定 agent 的执行能力，文件位于 `libs/deepagents/deepagents/backends/`：

| Backend | 文件 | 职责 |
|------|------|------|
| `StateBackend` | `state.py` | 默认后端，纯状态管理 |
| `LocalShellBackend` | `local_shell.py` | 本地 shell 执行 |
| `SandboxBackend` | `sandbox.py` | 沙箱执行（Remote） |
| `FilesystemBackend` | `filesystem.py` | 文件系统操作 |
| `StoreBackend` | `store.py` | 持久化存储 |
| `ContextHubBackend` | `context_hub.py` | LangSmith Context Hub |
| `LangsmithBackend` | `langsmith.py` | LangSmith 集成 |
| `CompositeBackend` | `composite.py` | 组合多个后端 |

Backend 协议定义在 `protocol.py` 中，包括 `SandboxBackendProtocol` 等接口。

### 3.5 Profiles 体系

Profiles 分为两大类，位于 `libs/deepagents/deepagents/profiles/`：

- **Provider Profiles** (`provider/`) — 按模型提供商定制行为
- **Harness Profiles** (`harness/`) — 整个 harness 级别的配置

功能包括：自定义 system prompt、排除工具、排除 middleware、改写工具描述等。

### 3.6 子代理系统

子代理是 Deep Agents 的核心能力之一，支持三种形式：

1. **`SubAgent`** — 声明式子代理，创建新的 `create_agent`
2. **`CompiledSubAgent`** — 传入已编译的 LangGraph 图
3. **`AsyncSubAgent`** — 异步子代理，支持后台轮询

自动发现机制：默认会添加 `general-purpose` 子代理，也可以自动发现项目中的子代理。

---

## 四、Code 包（终端编码 Agent）

### 4.1 架构概览

Code 包（`libs/code/`）是一个客户端-服务器架构：

```
┌──────────────────── Terminal client ─────────────────────┐
│  展示交互式或 headless 输出                               │
│  收集用户输入和审批                                       │
└──────────────────────────┬───────────────────────────────┘
                           │ streaming protocol
                           ▼
┌──────────────────── Agent server ────────────────────────┐
│  运行 coding agent graph                                  │
│  连接 model、tools、memory、skills 和 backend              │
└──────────────────────────────────────────────────────────┘
```

### 4.2 核心文件

| 文件 | 职责 |
|------|------|
| `main.py` | CLI 入口 |
| `app.py` | Textual 应用主循环 |
| `agent.py` | Agent 构建和运行时 |
| `server.py` / `server_graph.py` | 服务端运行时 |
| `command_registry.py` | 斜杠命令注册 |
| `model_config.py` | 模型配置（环境变量、认证、端点） |
| `config.py` / `config_manifest.py` | 配置管理和 manifest |
| `sessions.py` | 会话管理 |
| `mcp_*.py` | MCP 集成 |

### 4.3 技能系统

位于 `deepagents_code/skills/` 和 `deepagents_code/built_in_skills/`：

- **内置技能**：`remember`（记忆）、`skill-creator`（创建技能）
- **技能加载路径**（按优先级）：
  1. `~/.deepagents/agent/skills`（Deepagents 技能）
  2. `~/.agents/skills`（Agents 共享技能）
  3. 项目级 `.deepagents/skills` 和 `.agents/skills`
  4. `.claude/skills`（最高优先级）

---

## 五、学习路径

### 第一阶段：理解产品全貌（1-2 天）

1. ✅ 读顶层 README
2. ✅ 跑一个简单示例（如 `content-builder-agent`）
3. ✅ 理解三层架构关系

### 第二阶段：深入核心 SDK（3-5 天）

1. **`graph.py`** — 从 `create_deep_agent()` 入口，理解组装流程
2. **`middleware/`** — 逐个读：filesystem → subagents → skills → memory → permissions → summarization
3. **`backends/`** — 理解各后端的能力差异
4. **`profiles/`** — 了解 provider/harness profile 如何定制行为

> 建议：边读边跑 `libs/deepagents/tests/` 中的单元测试。

### 第三阶段：理解 Code 包（2-3 天）

1. `agent.py` — coding agent 如何构建
2. `app.py` — Textual 应用
3. `command_registry.py` — 命令系统
4. `mcp_*.py` — MCP 集成

### 第四阶段：横向扩展（按需）

| 方向 | 路径 | 适合场景 |
|------|------|----------|
| CLI 部署 | `libs/cli/` | 了解远程 agent 部署 |
| ACP 协议 | `libs/acp/` | 编辑器集成 |
| 评估套件 | `libs/evals/` | 跑 benchmark |
| 合作伙伴 | `libs/partners/` | 沙箱后端集成 |

### 第五阶段：动手实践

1. **改 middleware** — 给 filesystem 加自定义权限规则
2. **写 skill** — 用 `skill-creator` 技能引导创建
3. **跑 eval** — 用 `libs/evals/` 跑评估
4. **贡献代码** — 从 good first issue 开始

---

## 六、示例项目速查

| 示例 | 类型 | 核心概念 |
|------|------|----------|
| **Content Builder** | 本地脚本 | AGENTS.md 记忆、技能、文件系统后端、子代理 |
| **Deep Research** | 本地/服务器 | 子代理委派、Tavily 搜索、LangGraph Studio |
| **Coding Agent** | 托管部署 | 沙箱执行、技能、编码工作流 |
| **Text-to-SQL** | 本地脚本 | SQL 工具、规划、技能 |
| **Ralph Loop** | 自主循环 | 无状态迭代、文件系统持久化 |
| **Better Harness** | 研究工具 | Eval 驱动优化 |

---

## 七、开发工具链

- **`uv`** — 包管理和环境管理
- **`make`** — 任务运行
- **`ruff`** — Lint 和格式化
- **`ty`** — 静态类型检查
- **`pytest`** — 测试框架

### 常用命令

```bash
# 安装依赖
uv sync

# 运行测试
make test

# 运行指定测试
uv run --group test pytest tests/unit_tests/test_specific.py

# Lint
make lint

# 格式化
make format
```

---

## 八、关键设计原则

### 8.1 不要打破公共接口

- 检查函数/类是否在 `__init__.py` 中导出
- 使用 keyword-only 参数添加新参数：`*, new_param: str = "default"`
- 实验性功能需要明确标记

### 8.2 公共 API 清单（`__init__.py`）

```
create_deep_agent, DeepAgentState, AsyncSubAgent, AsyncAgentMiddleware,
FilesystemMiddleware, FilesystemPermission, MemoryMiddleware,
RubricMiddleware, SubAgent, CompiledSubAgent, SubAgentMiddleware,
HarnessProfile, HarnessProfileConfig, register_harness_profile,
ProviderProfile, register_provider_profile, GeneralPurposeSubagentProfile
```

---

## 九、调试入口

当 Deep Agents 行为异常时，排查路径：

1. **工具不可见？** → middleware assembly / profile `excluded_tools`
2. **工具不能执行？** → Backend 是否实现了 `SandboxBackendProtocol`
3. **文件权限问题？** → `FilesystemMiddleware` + `FilesystemPermission`
4. **Prompt 不符合预期？** → Harness Profile 的 system prompt 覆盖
5. **状态不持久？** → 检查 Backend 和 Store 配置

---

## 十、外部资源

- **官方文档**: https://docs.langchain.com/oss/python/deepagents/overview
- **API 参考**: https://reference.langchain.com/python/deepagents/
- **社区论坛**: https://forum.langchain.com/c/oss-product-help-lc-and-lg/deep-agents/18
- **LangChain Academy**: https://academy.langchain.com/
- **LangSmith**: https://docs.langchain.com/langsmith/home
