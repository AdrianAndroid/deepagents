<div align="center">
  <a href="https://docs.langchain.com/oss/python/deepagents/overview#deep-agents-overview">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="../.github/images/logo-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="../.github/images/logo-light.svg">
      <img alt="Deep Agents Logo" src="../.github/images/logo-dark.svg" width="50%">
    </picture>
  </a>
</div>

<h3 align="center">Examples</h3>

<p align="center"><em>Real agents and patterns built on Deep Agents.</em></p>

## Featured

<table>
<tr>
<td width="50%" valign="top">

### Deep Agents Code

A pre-built coding Deep Agent in your terminal — similar to Claude Code or Codex — powered by any LLM. Includes an interactive TUI, web search, remote sandboxes, persistent memory, custom skills, and human-in-the-loop approval.

```bash
curl -LsSf https://langch.in/dcode | bash
```

<sub>[Source](../libs/code/) · [Docs](https://docs.langchain.com/oss/python/deepagents/cli/overview)</sub>

</td>
<td width="50%" valign="top">

### Open SWE

An open-source, async coding agent for your org's internal workflows. Runs each task in an isolated cloud sandbox, integrates with Slack, Linear, and GitHub, and ships PRs end-to-end.

```text
@open-swe fix this user-reported bug plz!
```

<sub>[Repository](https://github.com/langchain-ai/open-swe) · [Blog post](https://blog.langchain.com/open-swe-an-open-source-framework-for-internal-coding-agents/)</sub>

</td>
</tr>
</table>

## In the wild

Production agents powered by the LangChain stack:

| Project | Description |
|---|---|
| [**LangSmith Fleet**](https://www.langchain.com/langsmith/fleet) | No-code platform for building AI agents from templates; connect your accounts and let the agent handle routine work |
| [**Chat LangChain**](https://chat.langchain.com/) | Documentation assistant that answers questions about LangChain, LangGraph, and LangSmith ([source](https://github.com/langchain-ai/chat-langchain)) |

## All examples

The `examples/` directory contains user-facing agents and architectural patterns built on `create_deep_agent()`. They are not core library packages; each folder demonstrates one or two Deep Agents capabilities such as `AGENTS.md` memory, skills, subagents, tool integration, custom backends, MCP, managed deployment, or external channel integration.

### Quick reference

| Example | Type | Purpose | Main Deep Agents concepts |
|---|---|---|---|
| [**Async Subagent Server**](async-subagent-server/) | Architecture pattern | Self-host an Agent Protocol server and expose a researcher as an async subagent to a supervisor agent. | `AsyncSubAgent`, Agent Protocol, FastAPI, background task polling |
| [**Better Harness**](better-harness/) | Research tooling | Use an outer Deep Agent to iteratively improve another agent's harness, then keep only changes that improve evals. | Harness engineering, eval-driven optimization, editable prompts/tools/skills/middleware |
| [**Content Builder**](content-builder-agent/) | Local script | Create blog posts, LinkedIn posts, tweets, and images from brand memory and reusable writing workflows. | `AGENTS.md` memory, skills, filesystem backend, subagents, image tools |
| [**Deep Research**](deep_research/) | Local script / LangGraph server | Run multi-step web research with planning, parallel researcher subagents, and reflection. | Custom prompts, Tavily search, `think_tool`, subagent delegation, LangGraph Studio |
| [**Coding Agent**](deploy-coding-agent/) | Managed deployment | Deploy an autonomous coding agent that plans, edits, tests, reviews, and delivers code in a sandbox. | `deepagents deploy`, sandbox execution, skills, coding workflow |
| [**Content Writer**](deploy-content-writer/) | Managed deployment | Deploy a content writer with per-user persistent memory and Supabase-backed authentication. | Managed deployment, auth, user-scoped memory, skills |
| [**GTM Strategist**](deploy-gtm-agent/) | Managed deployment | Coordinate market research and asynchronous content generation into a go-to-market strategy. | Sync subagents, async subagents, subagent auto-discovery, skills |
| [**MCP Docs Agent**](deploy-mcp-docs-agent/) | Managed deployment | Deploy a documentation-first research agent that verifies answers with LangChain docs MCP tools. | MCP tools, docs-grounded responses, managed deployment |
| [**Agents as Folders**](downloading_agents/) | Packaging pattern | Show that an agent can be distributed as a folder or zip containing instructions and skills. | `AGENTS.md`, skills, folder-based agent packaging |
| [**LLM Wiki**](llm-wiki/) | Local script / Context Hub | Build and maintain a persistent wiki, then sync revisions through LangSmith Context Hub. | Context Hub, long-term filesystem memory, scripted workflows |
| [**Nemotron Research Agent**](nvidia_deep_agent/) | Local script / LangGraph server | Combine frontier orchestration, NVIDIA Nemotron research, and GPU-accelerated RAPIDS execution. | Modal sandbox, GPU/CPU backends, multi-model subagents, self-improving skills |
| [**Ralph Loop**](ralph_mode/) | Autonomous loop | Repeatedly run a fresh-context agent that uses the filesystem and git as cross-iteration memory. | Stateless iterations, filesystem persistence, non-interactive execution, remote sandboxes |
| [**Talon WhatsApp**](talon-whatsapp/) | Channel integration | Connect a Deep Agent to WhatsApp through the experimental Talon runtime. | Talon host, WhatsApp bridge, Docker deployment, voice transcription |
| [**Text-to-SQL**](text-to-sql-agent/) | Local script | Answer natural-language questions over the Chinook SQLite database using SQL tools and skills. | LangChain SQL toolkit, planning, skills, read-only database rules |

### Detailed example guide

#### [Async Subagent Server](async-subagent-server/)

This example is the minimal end-to-end pattern for hosting your own async subagent. `server.py` exposes Agent Protocol endpoints for creating threads, starting runs, polling status, reading thread state, canceling runs, and health checks. The hosted worker is a Deep Agent researcher with a web search tool, while `supervisor.py` is an interactive client that delegates work through the async subagent interface.

Use it when you want the main agent to start long-running work, continue doing other tasks, and later check or update the background task. The example uses in-memory SQLite for convenience, so it is intended as a protocol and architecture demo rather than a production service.

#### [Better Harness](better-harness/)

Better Harness is an experimental optimization loop for improving another agent's harness. A TOML config defines the target workspace, editable surfaces, and eval cases. The system runs a baseline, copies visible train failures and harness surfaces into a proposer workspace, asks an outer Deep Agent to modify the harness, then accepts the candidate only if train and holdout results improve.

It demonstrates how prompts, tools, skills, middleware implementations, and middleware registration can be treated as editable optimization surfaces. It is most useful for researchers and agent engineers exploring eval-driven harness engineering.

#### [Content Builder](content-builder-agent/)

Content Builder is a local content creation agent built around filesystem configuration. `AGENTS.md` defines brand voice and writing standards, `skills/` defines workflows for blog and social media writing, and `subagents.yaml` defines a researcher subagent loaded by the main script. The agent can research topics, draft content, save outputs, and generate cover or social images.

This is a strong starting point for understanding the `AGENTS.md` + skills + subagents pattern. It also shows how `FilesystemBackend(root_dir=...)` gives the agent controlled access to a project directory.

#### [Deep Research](deep_research/)

Deep Research is a prompt-heavy research agent that plans a research task, delegates focused work to researcher subagents, reflects on progress, and synthesizes a final answer. It adds Tavily-powered search and a `think_tool` for strategic pauses between searches. The prompt files define research workflow, delegation limits, and researcher behavior.

It can be used from a notebook or served with LangGraph. Use it to study complex multi-step research behavior, parallel subagent delegation, and structured system prompts.

#### [Coding Agent](deploy-coding-agent/)

This deployable example defines a coding agent for LangSmith Managed Deep Agents. Its `AGENTS.md` describes a Plan -> Implement -> Review -> Deliver workflow, and its skills encode planning, code-review, and coding preferences. After deployment, the agent runs in a sandbox where it can inspect repositories, edit files, run tests, and deliver code changes.

It is the clearest example for building a managed coding assistant with explicit engineering workflow and reusable skills.

#### [Content Writer](deploy-content-writer/)

This managed content writer demonstrates user-specific persistent memory. Each authenticated user has separate memory files for preferences and context, allowing one deployed agent to serve multiple users without mixing their state. The example includes writing skills and a test script showing how to call the deployment with user authentication.

Use it as the main reference for combining managed deployment, auth, content generation, and per-user memory isolation.

#### [GTM Strategist](deploy-gtm-agent/)

The GTM Strategist coordinates multiple subagents for go-to-market planning. A synchronous market researcher performs competitive analysis and audience research, while an asynchronous content writer can produce longer-running assets in the background. The main agent combines research, positioning, channels, pricing, and content outputs into a final GTM plan.

This is the most direct deployable example of mixing sync and async subagents, and it also shows subagent folder auto-discovery during deployment.

#### [MCP Docs Agent](deploy-mcp-docs-agent/)

The MCP Docs Agent is a documentation-grounded research assistant. It is instructed to search and read official LangChain documentation through MCP tools before answering factual questions, and to clearly distinguish verified documentation from inference. This reduces hallucination and makes the agent suitable for developer support workflows.

Use it as the minimal pattern for attaching workspace-level MCP tools to a deployed Deep Agent.

#### [Agents as Folders](downloading_agents/)

This example illustrates the distribution model that agents can be folders. A packaged content writer can be downloaded as a zip, unpacked into a project, and run from its `AGENTS.md` and `skills/` without writing Python code.

It is useful for demonstrating agent portability: instructions, memory, and skills can be versioned, shared, and installed like ordinary project files.

#### [LLM Wiki](llm-wiki/)

LLM Wiki is a script-first workflow for creating and maintaining a persistent wiki. It has modes for initialization, ingestion, query answering, and linting. Source material is organized into `raw/`, normalized pages live in `wiki/`, and `log.md` records append-only lifecycle events. The workflow can sync revisions through LangSmith Context Hub.

Use it to study long-lived knowledge bases, filesystem-backed memory, reviewable ingestion, and Context Hub integration.

#### [Nemotron Research Agent](nvidia_deep_agent/)

This example combines multiple models and GPU execution. A frontier model orchestrates the workflow, NVIDIA Nemotron handles research, and a data processor can execute RAPIDS/cuDF/cuML workloads inside a Modal sandbox. The backend can choose GPU or CPU sandboxes at runtime, and the sandbox is seeded with skills and memory files.

It is the most advanced example for custom execution backends, GPU workloads, multi-model subagents, and self-improving skill files.

#### [Ralph Loop](ralph_mode/)

Ralph Loop implements an autonomous iteration pattern: each loop starts a new agent run with no conversation history, while the filesystem and git preserve progress. The prompt tells the agent to inspect the current state and continue building. Iterations can be finite or indefinite, and remote sandboxes are supported.

Use it when exploring long-running autonomous work where persistent files are preferred over an ever-growing chat context.

#### [Talon WhatsApp](talon-whatsapp/)

This example connects a Deep Agent to WhatsApp through the experimental Talon runtime. A Docker container runs the Talon host and WhatsApp bridge, persists session state and media under the workspace, and can optionally transcribe voice messages with a local speech model.

It is the primary example for external channel integration and event-driven agent operation outside a terminal or web UI.

#### [Text-to-SQL](text-to-sql-agent/)

Text-to-SQL wraps the LangChain SQL toolkit with Deep Agents planning and skill workflows. The agent can inspect the Chinook database schema, write SQL, check queries, and execute read-only `SELECT` statements. `AGENTS.md` provides safety rules such as avoiding writes, limiting results, and checking syntax before execution.

Use it as a compact example of combining existing LangChain toolkits with Deep Agents memory, skills, and filesystem persistence.

### Examples by theme

| Theme | Examples |
|---|---|
| Managed deployment | [Coding Agent](deploy-coding-agent/), [Content Writer](deploy-content-writer/), [GTM Strategist](deploy-gtm-agent/), [MCP Docs Agent](deploy-mcp-docs-agent/) |
| Subagents | [Async Subagent Server](async-subagent-server/), [GTM Strategist](deploy-gtm-agent/), [Deep Research](deep_research/), [Content Builder](content-builder-agent/) |
| Memory and skills | [Content Builder](content-builder-agent/), [Text-to-SQL](text-to-sql-agent/), [Nemotron Research Agent](nvidia_deep_agent/), [Agents as Folders](downloading_agents/) |
| Sandboxes and execution | [Coding Agent](deploy-coding-agent/), [Nemotron Research Agent](nvidia_deep_agent/), [Ralph Loop](ralph_mode/), [LLM Wiki](llm-wiki/) |
| Research and knowledge | [Deep Research](deep_research/), [MCP Docs Agent](deploy-mcp-docs-agent/), [LLM Wiki](llm-wiki/) |
| Harness and evals | [Better Harness](better-harness/) |
| External channels | [Talon WhatsApp](talon-whatsapp/) |
| Autonomous loops | [Ralph Loop](ralph_mode/) |

Each example has its own `README` with setup instructions.

<details>
<summary><h2>Contributing an example</h2></summary>

See the [Contributing Guide](https://docs.langchain.com/oss/python/contributing/overview) for general contribution guidelines.

When adding a new example:

- **Use uv** for dependency management with a `pyproject.toml` and `uv.lock` (commit the lock file)
- **Pin to deepagents version** — use a version range (e.g., `>=0.3.5,<0.4.0`) in dependencies
- **Include a `README`** with clear setup and usage instructions
- **Add tests** for reusable utilities or non-trivial helper logic
- **Keep it focused** — each example should demonstrate one use-case or workflow
- **Follow the structure** of existing examples (see `deep_research/` or `text-to-sql-agent/` as references)

</details>

## Resources

- [LangChain Academy](https://academy.langchain.com/) — Comprehensive, free courses on LangChain libraries and products, made by the LangChain team.
- [Code of Conduct](https://github.com/langchain-ai/langchain/?tab=coc-ov-file) — community guidelines and standards
