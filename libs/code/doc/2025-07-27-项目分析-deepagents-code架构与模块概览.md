# deepagents-code 项目架构与模块分析

### 轮次 1 - 项目整体分析

#### 用户提问要点
分析 `/home/zhaojian/deepagents/libs/code` 项目（`deepagents-code`）。

#### 结论/方案

## 项目定位

`deepagents-code`（发布名 `deepagents-code`，CLI 命令 `dcode`）是 Deep Agents 生态系统中的**预构建终端编码 Agent**，类似 Claude Code / Cursor 的开源替代品。它构建在 `deepagents` SDK 之上，版本 `0.0.4`，当前处于 Beta 阶段。

- **仓库位置**：`libs/code/`，属于 Deep Agents monorepo 的一个独立发布包
- **Python 版本**：`>=3.11,<4.0`，支持 3.11/3.12/3.13/3.14
- **SDK 依赖**：精确 pin `deepagents==0.7.0a3`
- **构建系统**：hatchling
- **包管理**：uv

## 核心架构：Client/Server 双进程模型

```
┌──────────── Terminal Client ────────────┐
│  Textual TUI / headless mode             │
│  用户输入、审批、流式渲染                  │
└──────────────────┬───────────────────────┘
                   │ streaming protocol (LangGraph SDK)
                   ▼
┌──────────── Agent Server ───────────────┐
│  `langgraph dev` 子进程                   │
│  运行 coding agent graph                  │
│  连接 model, tools, memory, skills, backend │
└──────────────────────────────────────────┘
```

- **Client**（`app.py`, `main.py`, `non_interactive.py`）：负责终端 UI、用户输入收集、审批弹窗、流式事件渲染
- **Server**（`server.py`, `server_graph.py`, `server_manager.py`）：管理 `langgraph dev` 子进程的生命周期，运行 agent graph
- 两者通过 LangGraph SDK 的流式协议通信，Server 绑定到 `127.0.0.1` 的随机端口

## 源码规模

- `deepagents_code/` 下有 **77 个 Python 文件**，总计约 **65,000 行**代码
- `tests/unit_tests/` 下有 **110+ 个测试文件**，测试覆盖面非常广
- `widgets/` 目录有 **38 个 widget 文件**

## 关键模块清单

| 模块 | 职责 |
| --- | --- |
| `main.py` | CLI 入口、参数解析、模式分发（交互/headless/ACP） |
| `app.py` | Textual App 主类、交互命令处理 |
| `agent.py` | Agent 构建与运行时集成（调用 SDK `create_deep_agent`） |
| `server.py` | LangGraph server 子进程生命周期管理 |
| `server_graph.py` | Agent graph 编译与配置 |
| `server_manager.py` | Server 启停与状态管理 |
| `config.py` | 配置 schema、glyphs、console、settings |
| `model_config.py` | 模型 provider 环境变量、认证、端点处理 |
| `command_registry.py` | 32 个 slash 命令注册 |
| `tools.py` / `tools_commands.py` | 工具定义与管理 |
| `mcp_*.py` + `mcp_providers/` | MCP 集成（auth、trust、providers） |
| `skills/` | Skill 加载与调用 |
| `built_in_skills/` | 内置 skill（remember, skill-creator） |
| `integrations/` | 沙箱配置、OpenAI Codex 集成 |
| `widgets/` | 38 个 Textual UI 组件 |
| `system_prompt.md` | Agent system prompt 模板 |
| `goal_rubric.py` / `goal_tools.py` | 目标与评分系统 |

## 32 个 Slash 命令

涵盖：agent 切换、auth 管理、自动更新、changelog、清屏、复制、文档、编辑器、reasoning effort、反馈、goal、help、install、MCP、model 切换、通知、offload（上下文压缩）、退出、reload、remember、restart、rubric、滚动条、skill-creator、主题、threads、时间戳、token 统计、trace、更新、version 等。

## 扩展点

1. **Skills & Subagents**：可复用的 agent 工作流
2. **Tools & MCP Servers**：外部能力集成
3. **Sandboxes**：隔离执行环境（LangSmith、Daytona、Modal、Runloop、Vercel 等）
4. **Hooks & Commands**：本地工作流集成

## 核心依赖

- **框架**：deepagents SDK, langchain, langgraph（checkpoint-sqlite, sdk, cli, runtime-inmem）
- **模型 Provider**：langchain-anthropic, langchain-google-genai, langchain-openai（默认包含）；可选支持 Bedrock, Cohere, DeepSeek, Fireworks, Groq, HuggingFace, IBM, LiteLLM, Mistral, NVIDIA, Ollama, Watsonx, Baseten 等
- **终端 UI**：textual, textual-autocomplete, textual-speedups, prompt-toolkit, rich, markdownify
- **工具**：tavily-python（web search）, langchain-quickjs（JS sandbox）, langchain-mcp-adapters
- **其他**：pyperclip, pillow, pyyaml, aiosqlite, deepagents-acp

## 设计特点

1. **启动性能优先**：禁止在模块级别导入重依赖（deepagents, langchain, langgraph），必须延迟到实际使用时
2. **安全模型**：默认信任运行目录，HITL 审批门控工具调用；不信任的目录应使用远程沙箱
3. **持久会话**：基于 SQLite checkpoint，支持跨会话恢复
4. **可组合配置**：用户/项目/会话/运行时多层配置叠加
5. **Textual 渲染规范**：优先使用 `Content` 而非 Rich `Text`，严格区分 markup 安全性

#### 后续 TODO
- 如需深入某个子系统（如 MCP 集成、沙箱架构、agent graph 编译流程等），可进一步分析

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

### 轮次 1 - 再次请求项目分析（快速概览）

#### 用户提问要点
再次请求：分析 `libs/code` 项目（deepagents-code）。

#### 结论/方案（相对上次的增量与校准）

**版本状态更新**
- `pyproject.toml` 中当前 `version = "0.0.11"`（上次快照为 `0.0.4`）
- SDK pin 已更新为 `deepagents==0.7.0a7`（上次为 `0.7.0a3`）
- 依赖新增/收紧：`langchain>=1.3.13,<2.0.0`、`langgraph-runtime-inmem>=0.31.0`、`textual>=8.2.7,<9.0.0`（含 `_textual_patches.py` 上游 workaround）、`langchain-quickjs>=0.3.2,<0.4.0`、`deepagents-acp>=0.0.8`
- 保持 3.11–3.14 Python 支持、hatchling 构建、uv 管理

**顶层目录（校准后）**
```
libs/code/
├── deepagents_code/          # 主包源码
├── examples/
├── doc/                      # 项目文档（含本文档）
├── images/                   # README 图
├── scripts/
├── pyproject.toml
├── Makefile
├── ARCHITECTURE.md / DEVELOPMENT.md / COMMANDS.md
├── AGENTS.md / CHANGELOG.md
├── bump-version.py / hatch_build.py
├── run-*.sh, run-*.ps1, dcode-dev.ps1
```

**运行时架构（沿用 ARCHITECTURE.md）**
- Terminal Client（Textual TUI 或 headless）↔ Agent Server（LangGraph graph）
- 两进程分离；client 只负责渲染/输入/审批，server 负责模型 + tools + memory + skills + sandbox
- 通过 langgraph-sdk streaming 协议通信，用 LangGraph 的 checkpoint（sqlite）实现 resume

**`deepagents_code/` 关键模块分组（本次汇总）**

| 分组 | 文件 |
|---|---|
| CLI 入口 & 运行 | `main.py`（≈3956 行）、`__main__.py`、`app.py`、`app.tcss` |
| Agent 组装 | `agent.py`、`server_graph.py`、`_server_config.py`、`subagents.py`、`hooks.py` |
| 客户端 | `client/`（含 `launch/`、`commands/`、`non_interactive.py`、`remote_client.py`） |
| 命令 / 提示词 | `command_registry.py`（生成 `COMMANDS.md`）、`system_prompt.md`、`default_agent_prompt.md`、`todo_list_prompt.md` |
| 模型 & 鉴权 | `model_config.py`、`configurable_model.py`、`auth_store.py`、`auth_display.py`、`reasoning_effort.py` |
| Tools & 展示 | `tools.py`、`tool_catalog.py`、`tool_display.py`、`_tool_stream.py`、`managed_tools.py`、`file_ops.py`、`editor.py` |
| MCP 集成 | `mcp_config.py`、`mcp_tools.py`、`mcp_auth.py`、`mcp_login_service.py`、`mcp_oauth_ui.py`、`mcp_trust.py`、`mcp_disabled.py`、`mcp_providers/` |
| Skills | `skills/`、`built_in_skills/`（内置 `remember`、`skill-creator`） |
| Sandbox 集成 | `integrations/`（`sandbox_config.py`、`sandbox_factory.py`、`sandbox_provider.py`、`sandbox_registry.py`、`openai_codex.py`） |
| 会话 & 恢复 | `sessions.py`、`resume_state.py`、`state_migration.py`、`_session_stats.py` |
| 审批 / HITL | `approval_mode.py`、`ask_user.py`、`_ask_user_types.py` |
| 目标 / rubric | `goal_rubric.py`、`goal_tools.py`、`reliable_rubric.py` |
| UI 组件 | `tui/`、`widgets/`、`ui.py`、`output.py`、`input.py`、`paste_collapse.py`、`formatting.py`、`theme.py`、`iterm_cursor_guide.py`、`notifications.py`、`clipboard.py`、`media_utils.py` |
| 终端能力 & 安全 | `terminal_capabilities.py`、`terminal_escape.py`、`unicode_security.py`、`memory_guard.py` |
| 环境 / 配置 | `_env_vars.py`、`_paths.py`、`_constants.py`、`config.py`、`config_manifest.py`、`local_context.py`、`project_utils.py`、`extras_info.py`、`onboarding.py`、`doctor.py`、`update_check.py` |
| 内部工具 | `_git.py`、`_debug.py`、`_debug_buffer.py`、`_startup_error.py`、`_testing_models.py`、`_fake_models.py`、`_textual_patches.py`、`_tool_stream.py`、`offload.py`、`event_bus.py`、`_cli_context.py` |

**特性能力（沿用 README，无变化）**
交互 TUI + streaming、会话 resume、Tavily web search、远程 sandbox（LangSmith / AgentCore / Daytona / Modal / Runloop / Vercel / QuickJS）、持久 memory、自定义 skills（progressive disclosure）、headless 模式、HITL 审批、MCP 集成、ACP 适配。

**安全模型（沿用 THREAT_MODEL.md 与 README）**
默认信任 CWD；HITL 只拦模型请求的 tool call；不信任仓库建议搭配远程 sandbox。

**开发工具链**
- `uv` + `Makefile`：`test / lint / format / bench / commands-catalog / commands-catalog-check` 等
- `pre-commit`：conventional commit、lockfile、SDK-pin、命令目录再生成、Textual patch 测试
- 独立版本，`release-please` 驱动 changelog / release
- 测试：`tests/unit_tests/`（无网络）+ `tests/integration_tests/`

#### 关键操作或文件改动
仅新增本文档追加，未改动源码。

#### 后续 TODO
- 需要时可深入 `main.py` 的启动流程、`server_graph.py` 中间件组装、`integrations/` 沙箱注册机制或 `client/launch/` 客户端拉起流程

