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
