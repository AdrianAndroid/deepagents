# Global development guidelines for the Deep Agents monorepo

This document provides context to understand the Deep Agents Python project and assist with development.

For environment setup, pre-commit installation, and the standard edit-test-lint loop, see [`libs/DEVELOPMENT.md`](libs/DEVELOPMENT.md). The rest of this document covers conventions and architecture reference.

## Project architecture and context

### Monorepo structure

This is a Python monorepo with multiple independently versioned packages:

```txt
deepagents/
├── libs/
│   ├── deepagents/  # Core SDK
│   ├── code/        # Terminal coding agent (`dcode`)
│   ├── cli/         # Managed deployment CLI
│   ├── acp/         # Agent Client Protocol support
│   ├── evals/       # Evaluation suite and Harbor integration
│   ├── talon/       # Experimental local runtime host
│   └── partners/    # Integration packages
│       ├── daytona/
│       ├── modal/
│       ├── quickjs/
│       ├── runloop/
│       └── vercel/
├── examples/        # User-facing example agents and patterns
├── .github/         # CI/CD workflows, issue templates, helper scripts
├── action.yml       # Composite GitHub Action wrapping `deepagents-code`
└── README.md        # Product overview
```

### Repository analysis for future AI agents

This repository is not a single Python package. Treat it as a collection of independently versioned, independently released packages that share source-control, CI, release tooling, examples, and contributor policy.

#### High-level product model

Deep Agents is an opinionated harness on top of the LangChain/LangGraph stack:

```txt
Deep Agents      opinionated agent harness: defaults, middleware, backends, profiles
LangChain        agent abstraction: model + tools + middleware -> agent loop
LangGraph        runtime: state, checkpoints, streaming, interrupts
```

The central public API is `deepagents.create_deep_agent()`. It assembles:

- a chat model, resolved from a LangChain `provider:model` string or a supplied `BaseChatModel`;
- the default Deep Agents middleware stack;
- filesystem, execution, memory, skills, and context backends;
- sync subagents, compiled subagents, and async/remote subagents;
- optional human-in-the-loop interrupts;
- provider and harness profiles; and
- a LangGraph compiled agent graph with Deep Agents metadata.

Runtime behavior is mostly owned by middleware and backends, not by a custom runtime. LangGraph provides execution, streaming, checkpointing, state, and interrupts.

#### Package inventory

Current package directories and their roles:

| Path | Distribution | Role |
| --- | --- | --- |
| `libs/deepagents` | `deepagents` | Core SDK. Exports `create_deep_agent`, `DeepAgentState`, middleware classes, provider/harness profile registration, and backend integration points. |
| `libs/code` | `deepagents-code` | Prebuilt terminal coding agent (`dcode` / `deepagents-code`) with Textual TUI, headless mode, MCP support, skills, provider auth, sandboxes, sessions, and GitHub Action support. |
| `libs/cli` | `deepagents-cli` | Managed Deep Agents deployment CLI. Scaffolds project folders, deploys to LangSmith Managed Deep Agents, manages remote agents, and manages MCP server registrations. |
| `libs/acp` | `deepagents-acp` | Agent Client Protocol adapter for exposing a Python Deep Agent to ACP-capable editors such as Zed. |
| `libs/evals` | `deepagents-evals` | Behavioral eval suite, trial aggregation CLI, model/catalog generation, Harbor integration, and Terminal Bench / CLBench support. |
| `libs/talon` | `deepagents-talon` | Experimental local runtime host for long-running agents, channels, cron, WhatsApp bridge, Fleet exports, MCP loading, and tracing. |
| `libs/partners/daytona` | `langchain-daytona` | Daytona sandbox backend integration. |
| `libs/partners/modal` | `langchain-modal` | Modal sandbox backend integration. |
| `libs/partners/runloop` | `langchain-runloop` | Runloop sandbox provider/backend integration. |
| `libs/partners/vercel` | `langchain-vercel-sandbox` | Vercel Sandbox backend integration. |
| `libs/partners/quickjs` | `langchain-quickjs` | Persistent sandboxed JavaScript REPL middleware backed by QuickJS, including programmatic tool calling and subagent dispatch support. |

`release-please-config.json` currently manages release automation for all packages above except `libs/evals`. Version baselines live in `.release-please-manifest.json`.

#### Source-code map

Use this map before changing code:

```txt
libs/deepagents/deepagents/
├── graph.py                 # create_deep_agent, DeepAgentState, prompt + middleware assembly
├── _models.py               # model resolution helpers
├── _messages_reducer.py     # DeltaChannel reducer support for messages
├── _tools.py                # built-in tool description override helpers
├── backends/                # state/store/filesystem/context-hub/langsmith/sandbox/local shell backends
├── middleware/              # filesystem, skills, memory, subagents, async subagents, summarization, permissions
└── profiles/                # provider and harness profiles for model/provider-specific behavior

libs/code/deepagents_code/
├── main.py                  # dcode CLI argument parsing and dispatch
├── app.py                   # Textual app and interactive command handling
├── agent.py                 # coding-agent construction/runtime integration
├── server*.py               # local server graph/runtime support
├── command_registry.py      # slash command registry; COMMANDS.md is generated from this
├── model_config.py          # provider env vars, auth, endpoint handling
├── config*.py               # configuration schema, commands, manifests
├── mcp_*.py, mcp_providers/ # MCP integration, auth, trust, provider-specific handling
├── skills/                  # skill management commands and logic
├── built_in_skills/         # packaged skills
├── widgets/                 # Textual UI widgets
└── system_prompt.md         # coding-agent prompt content

libs/cli/deepagents_cli/
├── main.py                  # argparse entrypoint and top-level dispatch
├── deploy/commands.py       # init, deploy, agents, and mcp-servers commands
├── deploy/project.py        # managed-agent project loading and validation
├── deploy/payload.py        # API payload and directory delta construction
├── deploy/api_client.py     # LangSmith Managed Deep Agents API client
├── deploy/mcp_resolver.py   # MCP server lookup and validation
└── deploy/state.py          # local deploy state

libs/evals/
├── deepagents_evals/        # eval CLI, catalog/model-group helpers, reporting utilities
├── deepagents_harbor/       # Harbor/LangSmith integration helpers
├── deepagents_clbench/      # CLBench sync/system files
├── tests/evals/             # behavioral eval cases and vendored data
└── tests/unit_tests/        # CLI/reporting/helper tests
```

#### Core SDK execution model

`create_deep_agent()` in `libs/deepagents/deepagents/graph.py` is the assembly point. Its default visible tools include todo management, filesystem operations, shell execution when supported by the backend, and subagent delegation. The function:

1. resolves the model and active harness profile;
2. validates profile exclusions so required scaffolding middleware cannot be removed;
3. applies tool description overrides;
4. resolves the backend, defaulting to `StateBackend`;
5. processes declarative `SubAgent`, `CompiledSubAgent`, and `AsyncSubAgent` specs;
6. auto-adds the default `general-purpose` subagent unless disabled or overridden;
7. assembles base middleware, user middleware, profile middleware, prompt caching, memory, and HITL middleware;
8. composes the final system prompt with user prompt first, SDK/profile content after it; and
9. delegates to LangChain `create_agent()` with `DeepAgentState` by default.

Important exported SDK symbols are listed in `libs/deepagents/deepagents/__init__.py`; changing these is a public API change. `DeepAgentState.messages` uses a `DeltaChannel` reducer to avoid quadratic checkpoint growth during long runs.

#### Backend and middleware responsibilities

When debugging SDK behavior, distinguish these layers:

- **Tool visibility**: controlled by middleware assembly, caller tools, and harness profile `excluded_tools`.
- **Tool execution capability**: controlled by the backend. The `execute` tool needs a backend implementing the sandbox protocol.
- **Filesystem policy**: `FilesystemMiddleware` enforces `FilesystemPermission` rules for built-in filesystem tools; direct backend calls are separate.
- **Prompt and request shaping**: handled by middleware and provider/harness profiles.
- **Persistence**: graph state/checkpoints come from LangGraph; filesystem and memory persistence come from Deep Agents backends.

Do not solve backend capability problems by hiding tools unless the user explicitly needs the model request surface changed.

#### Dependency relationships

Local development uses editable sources via `[tool.uv.sources]` in each package:

- `deepagents-code` depends on the SDK and local partner packages for optional sandbox/QuickJS integrations.
- `deepagents-cli`, `deepagents-acp`, partner packages, and `deepagents-talon` depend on the SDK.
- `deepagents-evals` depends on the SDK, `deepagents-code`, and `langchain-quickjs`.
- Partner packages should be thin integration layers and should not introduce SDK-breaking assumptions.

Because packages are independently versioned, do not assume all package versions move together. When a change crosses package boundaries, update version pins/ranges and tests deliberately.

#### Examples map

Examples under `examples/` are user-facing patterns, not core library code. They are useful for compatibility checks and public API usage searches.

| Path | Purpose |
| --- | --- |
| `examples/deep_research` | Multi-step research with Tavily, subagents, reflection, notebook/server options. |
| `examples/content-builder-agent` | File-configured content agent using `AGENTS.md`, skills, memory, and subagents. |
| `examples/text-to-sql-agent` | Natural-language-to-SQL agent on Chinook with skill-oriented workflows. |
| `examples/async-subagent-server` | FastAPI server exposing a researcher as an async subagent. |
| `examples/deploy-*` | Managed deployment examples with `agent.json`, `AGENTS.md`, tools, skills, and subagents. |
| `examples/llm-wiki` | Script-first wiki/Context Hub workflow. |
| `examples/nvidia_deep_agent` | Nemotron/GPU-oriented research and execution example. |
| `examples/better-harness` | Eval-driven outer-loop harness optimization. |
| `examples/ralph_mode` | Autonomous looping with filesystem persistence and optional sandboxes. |
| `examples/talon-whatsapp` | Docker/local topology for Talon WhatsApp channel. |
| `examples/downloading_agents` | "Agents as folders" packaging pattern. |

When changing a public interface, search examples as well as tests.

#### CI and automation map

Important automation files:

- `.github/workflows/ci.yml` detects changed package paths and fans out lint/test jobs.
- `.github/workflows/_lint.yml` and `_test.yml` are reusable package lint/test workflows.
- `.github/workflows/_benchmark.yml` and `_benchmark_nightly.yml` run CodSpeed benchmarks.
- `.github/workflows/release-please.yml` creates release PRs.
- `.github/workflows/release.yml` builds, tests, publishes to Test PyPI/PyPI, and creates GitHub releases.
- `.github/workflows/pr_lint.yml`, `pr_scope_file_check.yml`, `release_please_parse_check.yml`, and related workflows enforce PR title/body/release-please correctness.
- `.github/workflows/check_*` workflows validate lockfiles, versions, extras, dependency bounds, SDK pins, and release dependencies.
- `.github/workflows/evals*.yml`, `harbor.yml`, and `clbench.yml` run eval workflows.
- `action.yml` defines the composite GitHub Action for running `deepagents-code` in workflows.

All GitHub Actions used in workflows must be pinned to full-length commit SHAs, not tags.

#### Pre-commit and generated artifacts

`.pre-commit-config.yaml` runs Conventional Commit validation, syntax checks, whitespace/smart-quote hooks, package-specific format/lint hooks, lockfile checks, extras sync, version equality checks, eval catalog generation, and `deepagents-code` command catalog generation.

Generated or drift-checked artifacts include:

- `libs/code/COMMANDS.md`, generated from `deepagents_code/command_registry.py`;
- `libs/evals/EVAL_CATALOG.md`, generated from eval tests;
- `libs/evals/MODEL_GROUPS.md`, generated from the eval model registry;
- `uv.lock` files for every package and example with a `pyproject.toml`;
- `_version.py`, `pyproject.toml`, changelogs, and release manifest entries managed by release-please.

Do not hand-edit generated catalogs unless the generator expects that file as input.

### Development tools & commands

- `uv` – Package installer and resolver (replaces pip/poetry)
- `make` – Task runner. Look at the `Makefile` for available commands and usage patterns.
- `ruff` – Linter and formatter
- `ty` – Static type checking

Local development uses editable installs: `[tool.uv.sources]`

```bash
# Run unit tests (no network)
make test

# Run specific test file
uv run --group test pytest tests/unit_tests/test_specific.py
```

```bash
# Lint code
make lint

# Format code
make format
```

#### Environment and dependency management

Use `uv` for all environment and dependency operations in this monorepo. Do not invoke `pip`, `poetry`, or `conda` directly.

- Let `uv` manage the interpreter and virtual environments — `uv sync` and `uv run` operate without manual `source .venv/bin/activate`. Do not create ad-hoc virtual environments outside the package directory.
- Each package targets its own supported Python range via its `pyproject.toml`; do not pin a global Python version. If you need an interpreter explicitly, defer to the package's `requires-python` rather than assuming system Python.
- Install dependencies explicitly through `uv sync` (optionally `--group <name>` / `--all-groups`); never let them install implicitly.
- Don't mix environments within a session, and don't add new dependencies unless strictly required — when you do, justify them (recent releases/commits, adoption).

#### Suppressing ruff lint rules

Prefer inline `# noqa: RULE` over `[tool.ruff.lint.per-file-ignores]` for individual exceptions. `per-file-ignores` silences a rule for the *entire* file — If you add it for one violation, all future violations of that rule in the same file are silently ignored. Inline `# noqa` is precise to the line, self-documenting, and keeps the safety net intact for the rest of the file. Add comments to justify silencing. If you can't make a good justification for the ignore, it is probably code smell and should be re-evaluated.

Reserve `per-file-ignores` for **categorical policy** that applies to a whole class of files (e.g., `"tests/**" = ["D1", "S101"]` — tests don't need docstrings, `assert` is expected). These are not exceptions; they are different rules for a different context.

```toml
# GOOD – categorical policy in pyproject.toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D1", "S101"]

# BAD – single-line exception buried in pyproject.toml
"deepagents_cli/agent.py" = ["PLR2004"]
```

```python
# GOOD – precise, self-documenting inline suppression
timeout = 30  # noqa: PLR2004  # default HTTP timeout, not arbitrary
```

#### PR and commit titles

Follow Conventional Commits. See `.github/workflows/pr_lint.yml` for allowed types and scopes. All titles must include a scope with no exceptions.

- Start the text after `type(scope):` with a lowercase letter, unless the first word is a proper noun (e.g. `Azure`, `GitHub`, `OpenAI`) or a named entity (class, function, method, parameter, or variable name).
- Wrap named entities in backticks so they render as code. Proper nouns are left unadorned.
- Keep titles short and descriptive — save detail for the body.
- For version-branch sync PRs, use a title like `chore(repo): sync main into vX.Y`. Do not use `release` as the scope; PR title lint reserves `release` for the type and disallows it as a scope.

Examples:

```txt
feat(sdk): add new chat completion feature
fix(cli): resolve type hinting issue
chore(evals): update infrastructure dependencies
test(cli): missing unit tests for `_git`
feat(cli): `--startup-cmd` flag
style(cli): strip trailing annotations from `ask_user` questions
```

See [PR labeling and linting](#pr-labeling-and-linting) for more info.

#### Branch naming

Branches should be prefixed `<github-username>/<scope>/<short-description>`:

- `<github-username>` — the author's GitHub login (e.g. `mdrxy`).
- `<scope>` — the same scope used in the Conventional Commit title (`sdk`, `cli`, `code`, `evals`, `acp`, partner name, `infra`, `docs`).
- `<short-description>` — kebab-case, brief, no trailing slash.

Examples:

```txt
mdrxy/sdk/concrete-toolruntime-middleware-tools
mdrxy/code/help-screen-drift-test
mdrxy/cli/startup-cmd-flag
```

#### PR descriptions

The description *is* the summary — do not add a `# Summary` header.

- When the PR closes an issue, lead with the closing keyword on its own line at the very top, followed by a horizontal rule and then the body:

  ```txt
  Closes #123

  ---

  <rest of description>
  ```

  Only `Closes`, `Fixes`, and `Resolves` auto-close the referenced issue on merge. `Related:` or similar labels are informational and do not close anything.

- Explain the *why*: the motivation and why this solution is the right one. Limit prose.
- Write for readers who may be unfamiliar with this area of the codebase. Avoid insider shorthand and prefer language that is friendly to public viewers — this aids interpretability.
- Do **not** cite line numbers; they go stale as soon as the file changes.
- Rarely include full file paths or filenames. Reference the affected symbol, class, or subsystem by name instead.
- Wrap class, function, method, parameter, and variable names in backticks.
- For net new features or behavior-changing bugfixes, PR descriptions should include a `## Release note` section that states the user-visible change in release-note-ready language. Otherwise, omit the header.
- Skip dedicated "Test plan" or "Testing" sections in most cases. Mention tests only when coverage is non-obvious, risky, or otherwise notable.
- Call out areas of the change that require careful review.

## Core development principles

### Maintain stable public interfaces

CRITICAL: Always attempt to preserve function signatures, argument positions, and names for exported/public methods. Do not make breaking changes.

You should warn the developer for any function signature changes, regardless of whether they look breaking or not.

**Before making ANY changes to public APIs:**

- Check if the function/class is exported in `__init__.py`
- Look for existing usage patterns in tests and examples
- Use keyword-only arguments for new parameters: `*, new_param: str = "default"`
- Mark experimental features clearly with docstring warnings (using MkDocs Material admonitions, like `!!! warning`)

Ask: "Would this change break someone's code if they used it last week?"

### Code quality standards

All Python code MUST include type hints and return types.

```python title="Example"
def filter_unknown_users(users: list[str], known_users: set[str]) -> list[str]:
    """Single line description of the function.

    Any additional context about the function can go here.

    Args:
        users: List of user identifiers to filter.
        known_users: Set of known/valid user identifiers.

    Returns:
        List of users that are not in the `known_users` set.
    """
```

- Use descriptive, self-explanatory variable names.
- Follow existing patterns in the codebase you're modifying
- Attempt to break up complex functions (>20 lines) into smaller, focused functions where it makes sense
- Avoid using the `any` type
- Prefer single word variable names where possible

### Testing requirements

Every new feature or bugfix MUST be covered by unit tests.

- Unit tests: `tests/unit_tests/` (no network calls allowed)
- Integration tests: `tests/integration_tests/` (network calls permitted)
- We use `pytest` as the testing framework; if in doubt, check other existing tests for examples.
- Do NOT add `@pytest.mark.asyncio` to async tests — every package sets `asyncio_mode = "auto"` in `pyproject.toml`, so pytest-asyncio discovers them automatically.
- The testing file structure should mirror the source code structure.
- Avoid mocks as much as possible
- Test actual implementation, do not duplicate logic into tests

Ensure the following:

- Does the test suite fail if your new logic is broken?
- Edge cases and error conditions are tested
- Tests are deterministic (no flaky tests)

### Security and risk assessment

- No `eval()`, `exec()`, or `pickle` on user-controlled input
- Proper exception handling (no bare `except:`) and use a `msg` variable for error messages
- Remove unreachable/commented code before committing
- Race conditions or resource leaks (file handles, sockets, threads).
- Ensure proper resource cleanup (file handles, connections)

### Documentation standards

Use Google-style docstrings with Args section for all public functions.

```python title="Example"
def send_email(to: str, msg: str, *, priority: str = "normal") -> bool:
    """Send an email to a recipient with specified priority.

    Any additional context about the function can go here.

    Args:
        to: The email address of the recipient.
        msg: The message body to send.
        priority: Email priority level.

    Returns:
        `True` if email was sent successfully, `False` otherwise.

    Raises:
        InvalidEmailError: If the email address format is invalid.
        SMTPConnectionError: If unable to connect to email server.
    """
```

- Types go in function signatures, NOT in docstrings
  - If a default is present, DO NOT repeat it in the docstring unless there is post-processing or it is set conditionally.
- Focus on "why" rather than "what" in descriptions
- Document all parameters, return values, and exceptions
- Keep descriptions concise but clear
- Ensure American English spelling (e.g., "behavior", not "behaviour")
- Do NOT use Sphinx-style double backtick formatting (` ``code`` `). Use single backticks (`code`) for inline code references in docstrings and comments.

#### Model references in docs and examples

Always use the latest generally available models when referencing LLMs in docstrings, examples, and default values. Outdated model names signal stale code and confuse users. Before writing or updating model references, look up the current model IDs from each provider's official docs (Anthropic, OpenAI, Google). Do not rely on memorized model names — they go stale quickly.

## Package-specific guidance

### Deep Agents SDK (`libs/deepagents/`)

For SDK questions about `create_deep_agent`, middleware, tools, subagents, or agent construction, start in:

- `libs/deepagents/deepagents/graph.py`
  - `create_deep_agent` is the public construction entry point.
  - It builds the Deep Agents middleware stack and delegates to `langchain.agents.create_agent(...)`.
  - The final call currently happens near the end of `create_deep_agent`, followed by `.with_config(...)` for Deep Agents metadata and recursion config.
- `libs/deepagents/deepagents/middleware/`
  - Built-in Deep Agents middleware lives here.
  - `subagents.py` handles subagent middleware and nested `create_agent` use.
  - `filesystem.py`, `skills.py`, `memory.py`, `permissions.py`, and `summarization.py` are feature-specific middleware modules.
- `libs/deepagents/tests/`
  - Unit tests for SDK behavior.

If investigating LangChain `create_agent` internals, Deep Agents usually delegates into LangChain rather than owning the graph node assembly itself. Resolve the installed dependency source directly rather than searching the whole repo.

### Search hygiene

Avoid broad repo-level `glob` / `grep` for normal SDK work. This repo contains package `.venv`s, hidden worktrees, generated metadata, and scratch files that make broad searches noisy.

Prefer targeted paths:

- SDK source: `libs/deepagents/deepagents`
- SDK tests: `libs/deepagents/tests`
- Deep Agents Code/TUI package: `libs/code` (terminal coding agent)
- CLI deploy package: `libs/cli`
- ACP package: `libs/acp`

Avoid searching these unless explicitly needed:

- `.venv/`
- `.worktrees/`
- `.claude/worktrees/`
- `deepagents.egg-info/`
- benchmark result JSONs and scratch scripts at repo root

For dependency internals, first locate the dependency file from the package environment, then read that exact file instead of grepping all `site-packages`.

### Deep Agents Code (`libs/code/`)

The `deepagents-code` package ships the interactive terminal coding agent, launched via the `dcode` console command (`dcode` is the short alias for `deepagents-code`).

See `libs/code/AGENTS.md` for package-specific guidance — Textual, startup performance, slash commands, model providers, SDK pin, help-screen drift.

### Deep Agents CLI (`libs/cli/`)

As of `deepagents-cli==0.1.0` the interactive Textual REPL moved to `libs/code/` (`deepagents-code`). This package contains deployment and managed-agent administration commands only; see [Deep Agents Code](#deep-agents-code-libscode) above for Textual/widget/slash-command guidance.

#### Surface

- Entry points: `deepagents` and `deepagents-cli` console scripts → `deepagents_cli.cli_main`.

- Subcommands: `init` (scaffold a managed-agent project), `deploy` (upsert managed agents), `agents` (list/get/delete remote agents), and `mcp-servers` (register, inspect, connect, update, delete, and list tools for workspace MCP servers).
- Bare `deepagents` invocations print a deprecation notice pointing at `deepagents-code` and exit non-zero.

#### Layout

- `deepagents_cli/main.py` — argparse wiring + `cli_main` dispatch.
- `deepagents_cli/deploy/commands.py` — argparse wiring and handlers for `init`, `deploy`, `agents`, and `mcp-servers`.
- `deepagents_cli/deploy/project.py` — project layout loading and validation for `agent.json`, `AGENTS.md`, tools, skills, and subagents.
- `deepagents_cli/deploy/payload.py` — API payload construction and remote directory delta generation.
- `deepagents_cli/deploy/api_client.py` — LangSmith Managed Deep Agents API client.
- `deepagents_cli/deploy/mcp_resolver.py` — MCP server lookup and validation for deploy payloads.
- `deepagents_cli/deploy/state.py` — local deployment state keyed by endpoint.
- `deepagents_cli/config.py` — slim `_load_dotenv` helper used by deploy/admin commands.
- `deepagents_cli/model_config.py` — slim `resolve_env_var` helper for the `DEEPAGENTS_CLI_` env-var prefix.
- `deepagents_cli/_version.py` — `__version__` (managed by release-please).

Everything else (REPL widgets, Textual app, MCP, skills, sandbox bootstrap, agent picker, slash commands, splash tips, help-screen drift test, model-provider drift test, SDK-pin check) lived under `libs/cli/` before 0.1.0 and now lives under `libs/code/`.

### Evals (`libs/evals/`)

**Vendored data files:**

`libs/evals/tests/evals/tau2_airline/data/` contains vendored data from the upstream [tau-bench](https://github.com/sierra-research/tau-bench) project. These files must stay byte-identical to upstream. Pre-commit hooks (`end-of-file-fixer`, `trailing-whitespace`, `fix-smartquotes`, `fix-spaces`) are excluded from this directory in `.pre-commit-config.yaml`. Do not remove those exclusions or reformat files in this directory.

### Benchmarks

Each package's `Makefile` defines `bench` (walltime) and `bench-memory` (heap) targets that are the **single source of truth for the bench invocation** — both local runs and the reusable CI workflow (`.github/workflows/_benchmark.yml`) call these targets. To change how benchmarks are invoked, edit the Makefile; CI inherits the change automatically.

**Run locally:**

```bash
# Single package (same target CI invokes):
make -C libs/deepagents bench
make -C libs/code bench

# All benched packages in one go:
make -C libs bench-all

# Existing `benchmark` target (no CodSpeed instrumentation, faster, suitable
# for ad-hoc local tuning with pytest-benchmark):
make -C libs/deepagents benchmark
```

The `bench` target adds `--codspeed`; the older `benchmark` target stays around for plain `pytest-benchmark` runs that don't need walltime profiling. `bench-memory` runs the `memory_benchmark`-marked subset and is gated in CI behind `has-memory-benchmarks: true` on the workflow input — currently set by `libs/partners/quickjs`.

**Dashboard:** https://codspeed.io/langchain-ai/deepagents — separate views per package via the upper-left selector. PR comments with performance reports are posted by the CodSpeed GitHub App when it is enabled for the repository (independent of this workflow's configuration).

**Regression thresholds:** currently 10% global, managed in the CodSpeed dashboard. Tighten per-benchmark thresholds for benches whose noise floor is well below 10% (e.g., the `create_deep_agent` construction benches in `libs/deepagents/tests/benchmarks/`) — wide thresholds will mask real regressions in tight code.

**Nightly full sweep:** `.github/workflows/_benchmark_nightly.yml` runs every benched package on a daily cron without path gating, so baselines for unchanged packages don't drift. Use `workflow_dispatch` on that workflow for an ad-hoc full sweep before bumping `pytest-codspeed` or the `CodSpeedHQ/action` SHA.

## CI/CD infrastructure

### Release process

Releases use **release-please** automation. When conventional commits land on `main`, release-please creates/updates a release PR with version bumps and CHANGELOG entries. Merging the release PR triggers `.github/workflows/release.yml` via `.github/workflows/release-please.yml`.

The release pipeline: build → unit tests against built package → publish to Test PyPI → publish to PyPI (trusted publishing/OIDC) → create GitHub release.

See `.github/RELEASING.md` for the full workflow (version bumping, pre-releases, troubleshooting failed releases, and label management).

#### Overriding a merged commit's changelog entry

See [Overriding a Merged Commit's Changelog Entry](.github/RELEASING.md#overriding-a-merged-commits-changelog-entry) in `RELEASING.md` for the workflow (when to use it, the block format, and the squash-merge caveats).

#### Reverting a merged-but-unreleased PR

See [Reverting a Merged-but-Unreleased PR](.github/RELEASING.md#reverting-a-merged-but-unreleased-pr) in `RELEASING.md` when a PR has landed on `main` but its `release(<component>): X.Y.Z` PR has not yet shipped. Covers the quiet path (override to `chore` + `chore` revert, so the entry never appears in the changelog) and the `revert:` audit-trail path.

#### Developing a new version line

See [Developing a new version line](.github/RELEASING.md#developing-a-new-version-line) in `RELEASING.md` before creating a version branch (e.g. staging `0.7` while `main` stays `0.6.x`, or maintaining `0.6.x` after `main` moves on). Branches must be named `vX.Y` to match the protection ruleset (CI-passing PRs required like `main`, but `v[0-9].*` additionally allows merge commits — `main` stays squash-only); release-please only runs on `main`; keep a staging branch current by opening forward-merge PRs from `main` (a merge commit, not squash), reserving cherry-pick for when the branch deliberately diverges; and the cutover is an admin merge-commit to `main` that preserves individual commits (don't squash) so the changelog stays itemized.

### PR labeling and linting

**Title linting** (`.github/workflows/pr_lint.yml`) – Enforces Conventional Commits format with required scope on PR titles

**Release-please parse check** (`.github/workflows/release_please_parse_check.yml`) – Runs `@conventional-commits/parser` on the would-be squash-merge message (`<title> (#<num>)\n\n<body>`) at PR time. Fails the check and posts a sticky comment with a paste-ready `BEGIN_COMMIT_OVERRIDE` block when the parser would reject the body, preventing silent changelog drops. Mirrors release-please's `preprocessCommitMessage` and `splitMessages` so per-sub-message parse failures are caught the same way release-please catches them. The parser is exact-pinned (not a semver range) and must stay in lock-step with `release-please/package.json`.

**Auto-labeling:**

- `.github/workflows/pr_labeler.yml` – Unified PR labeler (size, file, title, external/internal, contributor tier)
- `.github/workflows/pr_labeler_backfill.yml` – Manual backfill of PR labels on open PRs
- `.github/workflows/auto-label-by-package.yml` – Issue labeling by package
- `.github/workflows/tag-external-issues.yml` – Issue external/internal classification and contributor tier labeling

### Adding a new partner to CI

When adding a new partner package, update these files:

- `.github/ISSUE_TEMPLATE/bug-report.yml` – Add to Area checkbox options
- `.github/ISSUE_TEMPLATE/feature-request.yml` – Add to Area checkbox options
- `.github/ISSUE_TEMPLATE/privileged.yml` – Add to Area checkbox options
- `.github/dependabot.yml` – Add dependency update directory
- `.github/scripts/pr-labeler-config.json` – Add scope-to-label mapping and file rule
- `.github/workflows/auto-label-by-package.yml` – Add package label mapping
- `.github/workflows/ci.yml` – Add to change detection and lint/test jobs
- `.github/workflows/pr_lint.yml` – Add to allowed scopes
- `.github/workflows/release.yml` – Add to `package` input options and `setup` job mapping
- `.github/workflows/release-please.yml` – Add release detection output and trigger job
- `release-please-config.json` – Add package entry under `packages`
- `.release-please-manifest.json` – Add the latest-released baseline; for a new package whose first release should be `0.0.1`, use `0.0.0`
- `.github/RELEASING.md` – Add to Managed Packages table
- `.github/workflows/harbor.yml` – Add sandbox option and credential check (sandbox-backed partners only)

### GitHub Actions & Workflows

This repository require actions to be pinned to a full-length commit SHA. Attempting to use a tag will fail. Use the `gh` cli to query. Verify tags are not annotated tag objects (which would need dereferencing).

## Additional resources

- **Documentation:** https://docs.langchain.com/oss/python/deepagents/overview and source at https://github.com/langchain-ai/docs or `../docs/`. Prefer the local install and use file search tools for best results. If needed, use the docs MCP server as defined in `.mcp.json` for programmatic access.
- **Contributing Guide:** [Contributing Guide](https://docs.langchain.com/oss/python/contributing/overview)

## 文档留存规则
1. 每轮问答实时留存要求：每一轮问答（单次 user → assistant 交互）结束后，必须**主动、自动**立即对该轮问答内容进行结构化总结，提取有价值的信息（需求说明、技术方案、问题排查过程、开发指南、架构分析、决策记录、用户反馈等）追加保存为 Markdown 文档，不得等到整个会话结束再一次性总结，避免遗漏细节。**禁止在保存前询问用户是否需要保存**——这是默认行为，无需确认；即使用户没有明确要求也必须保存。
2. 统一存储路径：所有问答/会话总结文档必须保存到项目根目录的 `doc/` 文件夹中。
3. 命名规范：文档统一采用 `YYYY-MM-DD-主题-内容摘要.md` 格式命名，同一天同一主题的多轮问答追加到同一文件中，确保命名清晰可追溯，方便后续检索复用。
4. 单轮追加格式：每一轮问答追加时，先写一个二级或三级标题（如 `### 轮次 N - 简要主题` 或时间戳），然后依次记录：用户提问要点、结论/方案、关键操作或文件改动、后续 TODO（如有）。
5. 内容质量要求：总结内容需要具备可复用性，信息准确完整，避免重复解决相同问题，沉淀为项目知识库的一部分。
6. 会话分隔规范：所有多会话的文档（包括问答记录、知识库文档、AGENTS 规则更新记录等），不同会话产生的内容之间必须添加统一格式的分隔符，明确区分两次会话的边界，避免内容混淆。同一会话内的多轮问答不使用该分隔符，仅使用标题层级区分。
统一分隔符样式如下：
```markdown
---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---
```
分隔符需要独占三行，上下各一条横线，中间是带 emoji 的会话标识，确保视觉上足够明显，长文档中可快速定位不同会话的内容边界。

7. 单轮结束标记：每一轮问答的记录末尾必须追加一行"结束状态标记"，同时标明结束结果与该轮总耗时，用于区分正常结束、异常结束和中断结束，便于事后审计与统计。
   - 格式统一为：`> ⏹ 结束状态：<状态> | ⏱ 总耗时：<HH:MM:SS 或 Xs>  | 🕒 结束时间：<YYYY-MM-DD HH:MM:SS>`
   - `<状态>` 取值：`✅ 正常结束`（任务完整完成）/ `⚠️ 异常结束`（工具报错、需求未达成、被中途打断等）/ `⏸ 用户中断`（用户主动 stop / Ctrl+C）/ `🚫 拒绝执行`（用户拒绝工具调用或本轮无实际操作）。
   - `<总耗时>` 指从本轮 user 消息发出到 assistant 最终回复完成的墙钟时间；若无法精确获知，用估算值并在后面加 `(估算)` 标注。
   - 该标记必须位于本轮所有二级/三级小节内容之后、下一轮标题或分隔符之前，作为单轮记录的最后一行，且使用引用块（`> ` 前缀）以在视觉上与正文区分。
   - 异常/中断情况下需另起一行简要说明失败原因或中断上下文（同样使用 `> ` 引用块），供复盘参考。
