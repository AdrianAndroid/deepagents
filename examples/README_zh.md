<div align="center">
  <a href="https://docs.langchain.com/oss/python/deepagents/overview#deep-agents-overview">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="../.github/images/logo-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="../.github/images/logo-light.svg">
      <img alt="Deep Agents Logo" src="../.github/images/logo-dark.svg" width="50%">
    </picture>
  </a>
</div>

<h3 align="center">示例</h3>

<p align="center"><em>基于 Deep Agents 构建的真实代理与模式。</em></p>

## 精选

<table>
<tr>
<td width="50%" valign="top">

### Deep Agents Code

一个可在终端中使用的预构建编码 Deep Agent，类似 Claude Code 或 Codex，可由任意 LLM 驱动。它包含交互式 TUI、网页搜索、远程沙箱、持久化记忆、自定义技能以及人机协同审批。

```bash
curl -LsSf https://langch.in/dcode | bash
```

<sub>[源码](../libs/code/) · [文档](https://docs.langchain.com/oss/python/deepagents/cli/overview)</sub>

</td>
<td width="50%" valign="top">

### Open SWE

一个面向组织内部工作流的开源异步编码代理。每个任务都在隔离的云沙箱中运行，集成 Slack、Linear 和 GitHub，并能端到端提交 PR。

```text
@open-swe fix this user-reported bug plz!
```

<sub>[仓库](https://github.com/langchain-ai/open-swe) · [博客文章](https://blog.langchain.com/open-swe-an-open-source-framework-for-internal-coding-agents/)</sub>

</td>
</tr>
</table>

## 真实案例

由 LangChain 技术栈驱动的生产级代理：

| 项目 | 描述 |
|---|---|
| [**LangSmith Fleet**](https://www.langchain.com/langsmith/fleet) | 用于从模板构建 AI 代理的无代码平台；连接你的账号后，代理即可处理日常工作 |
| [**Chat LangChain**](https://chat.langchain.com/) | 可回答 LangChain、LangGraph 和 LangSmith 相关问题的文档助手（[源码](https://github.com/langchain-ai/chat-langchain)） |

## 所有示例

`examples/` 目录包含基于 `create_deep_agent()` 构建的面向用户的代理和架构模式。它们不是核心库包；每个文件夹都演示一到两个 Deep Agents 能力，例如 `AGENTS.md` 记忆、技能、子代理、工具集成、自定义后端、MCP、托管部署或外部渠道集成。

### 速查表

| 示例 | 类型 | 作用 | 主要 Deep Agents 概念 |
|---|---|---|---|
| [**Async Subagent Server**](async-subagent-server/) | 架构模式 | 自托管一个 Agent Protocol 服务器，并把研究代理作为异步子代理暴露给 supervisor 代理。 | `AsyncSubAgent`、Agent Protocol、FastAPI、后台任务轮询 |
| [**Better Harness**](better-harness/) | 研究工具 | 使用外层 Deep Agent 迭代改进另一个代理的 harness，并只保留能提升 eval 的改动。 | Harness 工程、eval 驱动优化、可编辑 prompt/tools/skills/middleware |
| [**Content Builder**](content-builder-agent/) | 本地脚本 | 根据品牌记忆和可复用写作工作流创建博客、LinkedIn 帖子、推文和图片。 | `AGENTS.md` 记忆、技能、文件系统后端、子代理、图片工具 |
| [**Deep Research**](deep_research/) | 本地脚本 / LangGraph 服务器 | 通过规划、并行研究子代理和反思执行多步骤网页研究。 | 自定义 prompt、Tavily 搜索、`think_tool`、子代理委派、LangGraph Studio |
| [**Coding Agent**](deploy-coding-agent/) | 托管部署 | 部署一个能在沙箱中规划、编辑、测试、审查并交付代码的自主编码代理。 | `deepagents deploy`、沙箱执行、技能、编码工作流 |
| [**Content Writer**](deploy-content-writer/) | 托管部署 | 部署一个带按用户持久记忆和 Supabase 认证的内容写作代理。 | 托管部署、认证、用户级记忆、技能 |
| [**GTM Strategist**](deploy-gtm-agent/) | 托管部署 | 将市场研究和异步内容生成协调为 go-to-market 策略。 | 同步子代理、异步子代理、子代理自动发现、技能 |
| [**MCP Docs Agent**](deploy-mcp-docs-agent/) | 托管部署 | 部署一个文档优先的研究代理，使用 LangChain docs MCP 工具验证答案。 | MCP 工具、基于文档的回答、托管部署 |
| [**Agents as Folders**](downloading_agents/) | 打包模式 | 展示代理可以作为包含指令和技能的文件夹或 zip 分发。 | `AGENTS.md`、技能、基于文件夹的代理打包 |
| [**LLM Wiki**](llm-wiki/) | 本地脚本 / Context Hub | 构建和维护一个持久化 wiki，并通过 LangSmith Context Hub 同步修订版。 | Context Hub、长期文件系统记忆、脚本化工作流 |
| [**Nemotron Research Agent**](nvidia_deep_agent/) | 本地脚本 / LangGraph 服务器 | 结合前沿模型编排、NVIDIA Nemotron 研究和 GPU 加速 RAPIDS 执行。 | Modal 沙箱、GPU/CPU 后端、多模型子代理、自改进技能 |
| [**Ralph Loop**](ralph_mode/) | 自主循环 | 重复运行一个全新上下文代理，使用文件系统和 git 作为跨迭代记忆。 | 无状态迭代、文件系统持久化、非交互执行、远程沙箱 |
| [**Talon WhatsApp**](talon-whatsapp/) | 渠道集成 | 通过实验性的 Talon 运行时把 Deep Agent 接入 WhatsApp。 | Talon host、WhatsApp bridge、Docker 部署、语音转录 |
| [**Text-to-SQL**](text-to-sql-agent/) | 本地脚本 | 使用 SQL 工具和技能回答 Chinook SQLite 数据库上的自然语言问题。 | LangChain SQL toolkit、规划、技能、只读数据库规则 |

### 详细示例指南

#### [Async Subagent Server](async-subagent-server/)

这是自托管异步子代理的最小端到端模式。`server.py` 暴露 Agent Protocol 端点，用于创建线程、启动运行、轮询状态、读取线程状态、取消运行和健康检查。被托管的 worker 是一个带网页搜索工具的 Deep Agent 研究代理，而 `supervisor.py` 是一个交互式客户端，通过异步子代理接口委派工作。

当你希望主代理启动长时间运行的任务、继续处理其他工作，并在之后检查或更新后台任务时，可以参考此示例。该示例为方便起见使用内存 SQLite，因此更适合作为协议和架构演示，而不是生产服务。

#### [Better Harness](better-harness/)

Better Harness 是一个用于改进另一个代理 harness 的实验性优化循环。TOML 配置定义目标工作区、可编辑表面和 eval cases。系统先运行 baseline，将可见的训练失败案例和 harness 表面复制到 proposer workspace，让外层 Deep Agent 修改 harness，然后只在 train 和 holdout 结果提升时接受候选改动。

它展示了如何把 prompts、tools、skills、middleware 实现和 middleware 注册视为可编辑的优化表面。它最适合研究人员和代理工程师探索 eval 驱动的 harness 工程。

#### [Content Builder](content-builder-agent/)

Content Builder 是一个围绕文件系统配置构建的本地内容创作代理。`AGENTS.md` 定义品牌声音和写作标准，`skills/` 定义博客和社交媒体写作工作流，`subagents.yaml` 定义由主脚本加载的研究子代理。该代理可以研究主题、起草内容、保存输出，并生成封面图或社交图片。

这是理解 `AGENTS.md` + skills + subagents 模式的良好起点。它还展示了 `FilesystemBackend(root_dir=...)` 如何让代理受控访问项目目录。

#### [Deep Research](deep_research/)

Deep Research 是一个重 prompt 的研究代理，能够规划研究任务、将聚焦工作委派给研究子代理、反思进展并综合最终答案。它添加了 Tavily 驱动的搜索和用于在搜索之间进行战略暂停的 `think_tool`。prompt 文件定义研究工作流、委派限制和研究员行为。

它可以通过 notebook 使用，也可以通过 LangGraph 提供服务。可用它学习复杂多步骤研究行为、并行子代理委派和结构化 system prompt。

#### [Coding Agent](deploy-coding-agent/)

这个可部署示例为 LangSmith Managed Deep Agents 定义了一个编码代理。它的 `AGENTS.md` 描述 Plan -> Implement -> Review -> Deliver 工作流，技能则编码规划、代码审查和编码偏好。部署后，代理在沙箱中运行，可以检查仓库、编辑文件、运行测试并交付代码改动。

这是构建带明确工程工作流和可复用技能的托管编码助手的最清晰示例。

#### [Content Writer](deploy-content-writer/)

这个托管内容写作代理展示了用户级持久记忆。每个认证用户都有独立的偏好和上下文记忆文件，因此一个部署可以服务多个用户且不会混淆状态。该示例包含写作技能，以及展示如何带用户认证调用部署的测试脚本。

它是组合托管部署、认证、内容生成和按用户隔离记忆的主要参考。

#### [GTM Strategist](deploy-gtm-agent/)

GTM Strategist 为 go-to-market 规划协调多个子代理。同步市场研究员负责竞品分析和受众研究，异步内容写作代理可以在后台生成耗时更长的素材。主代理将研究、定位、渠道、定价和内容输出整合成最终 GTM 计划。

这是最直接展示混合同步和异步子代理的可部署示例，同时也展示了部署期间的子代理文件夹自动发现。

#### [MCP Docs Agent](deploy-mcp-docs-agent/)

MCP Docs Agent 是一个基于文档的研究助手。它被指示在回答事实性问题之前，通过 MCP 工具搜索和阅读官方 LangChain 文档，并清楚区分经文档验证的内容与推断内容。这可以减少幻觉，使代理适合开发者支持工作流。

这是将 workspace 级 MCP 工具接入已部署 Deep Agent 的最小模式。

#### [Agents as Folders](downloading_agents/)

此示例说明代理可以作为文件夹分发。一个打包好的 content writer 可以作为 zip 下载、解压到项目中，并仅依靠其中的 `AGENTS.md` 和 `skills/` 运行，无需编写 Python 代码。

它适合展示代理的可移植性：指令、记忆和技能可以像普通项目文件一样被版本化、共享和安装。

#### [LLM Wiki](llm-wiki/)

LLM Wiki 是一个脚本优先的工作流，用于创建和维护持久化 wiki。它包含初始化、摄取、问答和 lint 模式。源材料组织在 `raw/` 中，规范化页面位于 `wiki/` 中，`log.md` 记录追加式生命周期事件。该工作流可以通过 LangSmith Context Hub 同步修订版。

可用它学习长期知识库、基于文件系统的记忆、可审阅摄取流程和 Context Hub 集成。

#### [Nemotron Research Agent](nvidia_deep_agent/)

此示例结合了多模型和 GPU 执行。前沿模型负责编排工作流，NVIDIA Nemotron 负责研究，数据处理器则可以在 Modal 沙箱中执行 RAPIDS/cuDF/cuML 工作负载。后端可以在运行时选择 GPU 或 CPU 沙箱，沙箱会预先注入技能和记忆文件。

这是自定义执行后端、GPU 工作负载、多模型子代理和自改进技能文件方面最高级的示例。

#### [Ralph Loop](ralph_mode/)

Ralph Loop 实现了一种自主迭代模式：每次循环都启动一个没有对话历史的新代理运行，而文件系统和 git 保留进展。prompt 会要求代理检查当前状态并继续构建。迭代次数可以有限，也可以无限，并支持远程沙箱。

当你探索长时间自主工作，并且希望用持久文件而不是不断增长的聊天上下文来保存状态时，可以参考此示例。

#### [Talon WhatsApp](talon-whatsapp/)

此示例通过实验性的 Talon 运行时将 Deep Agent 接入 WhatsApp。Docker 容器运行 Talon host 和 WhatsApp bridge，将会话状态和媒体持久化到工作区，并可选择用本地语音模型转录语音消息。

这是外部渠道集成和终端或 Web UI 之外的事件驱动代理运行的主要示例。

#### [Text-to-SQL](text-to-sql-agent/)

Text-to-SQL 将 LangChain SQL toolkit 与 Deep Agents 规划和技能工作流结合起来。代理可以检查 Chinook 数据库 schema、编写 SQL、检查查询并执行只读 `SELECT` 语句。`AGENTS.md` 提供安全规则，例如避免写操作、限制结果数量以及执行前检查语法。

这是将现有 LangChain toolkit 与 Deep Agents 记忆、技能和文件系统持久化结合的紧凑示例。

### 按主题分类

| 主题 | 示例 |
|---|---|
| 托管部署 | [Coding Agent](deploy-coding-agent/), [Content Writer](deploy-content-writer/), [GTM Strategist](deploy-gtm-agent/), [MCP Docs Agent](deploy-mcp-docs-agent/) |
| 子代理 | [Async Subagent Server](async-subagent-server/), [GTM Strategist](deploy-gtm-agent/), [Deep Research](deep_research/), [Content Builder](content-builder-agent/) |
| 记忆和技能 | [Content Builder](content-builder-agent/), [Text-to-SQL](text-to-sql-agent/), [Nemotron Research Agent](nvidia_deep_agent/), [Agents as Folders](downloading_agents/) |
| 沙箱和执行 | [Coding Agent](deploy-coding-agent/), [Nemotron Research Agent](nvidia_deep_agent/), [Ralph Loop](ralph_mode/), [LLM Wiki](llm-wiki/) |
| 研究和知识 | [Deep Research](deep_research/), [MCP Docs Agent](deploy-mcp-docs-agent/), [LLM Wiki](llm-wiki/) |
| Harness 和 evals | [Better Harness](better-harness/) |
| 外部渠道 | [Talon WhatsApp](talon-whatsapp/) |
| 自主循环 | [Ralph Loop](ralph_mode/) |

每个示例都有自己的 `README`，其中包含安装和使用说明。

<details>
<summary><h2>贡献示例</h2></summary>

请参阅[贡献指南](https://docs.langchain.com/oss/python/contributing/overview)了解通用贡献规范。

添加新示例时：

- **使用 uv** 管理依赖，并包含 `pyproject.toml` 和 `uv.lock`（提交 lock 文件）
- **固定 deepagents 版本** —— 在 dependencies 中使用版本范围（例如 `>=0.3.5,<0.4.0`）
- **包含 `README`**，提供清晰的安装和使用说明
- **为可复用工具或非平凡辅助逻辑添加测试**
- **保持聚焦** —— 每个示例应展示一个用例或工作流
- **遵循现有示例结构**（参考 `deep_research/` 或 `text-to-sql-agent/`）

</details>

## 资源

- [LangChain Academy](https://academy.langchain.com/) —— 由 LangChain 团队制作的全面免费课程，覆盖 LangChain 库和产品。
- [行为准则](https://github.com/langchain-ai/langchain/?tab=coc-ov-file) —— 社区准则和标准
