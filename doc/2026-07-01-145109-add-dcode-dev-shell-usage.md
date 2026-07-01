# Add Dcode Dev Shell Usage

- Time: 2026-07-01T14:51:09+08:00
- Project: deepagents

## Prompt

Called the Read tool with the following input: {"filePath":"/Users/zhaojian/Desktop/deepagents/libs/code/dcode-dev.sh"}<path>/Users/zhaojian/Desktop/deepagents/libs/code/dcode-dev.sh</path>
<type>file</type>
<content>
1: #!/usr/bin/env bash
2: set -euo pipefail
3: 
4: SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
5: VENV_DIR="${DCODE_DEV_VENV:-$HOME/.local/share/dcode-dev}"
6: 
7: if ! command -v uv >/dev/null 2>&1; then
8:   printf 'uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/\n' >&2
9:   exit 1
10: fi
11: 
12: if [ ! -x "$VENV_DIR/bin/python" ]; then
13:   uv venv "$VENV_DIR"
14: fi
15: 
16: uv pip install --python "$VENV_DIR/bin/python" -e "$SCRIPT_DIR" --upgrade
17: exec "$VENV_DIR/bin/dcode" "$@"

(End of file - total 17 lines)
</content>

<system-reminder>
Instructions from: /Users/zhaojian/Desktop/deepagents/libs/code/AGENTS.md
# `libs/code` agent guide

`deepagents-code` is the interactive coding agent — the Textual REPL, headless `-x` mode, MCP integration, skills, sandbox bootstrap, and slash-command surface. Forked from `deepagents-cli` at the 0.1.0 split.

For monorepo-wide conventions (commit titles, lint, testing, docs, CI, benchmarks), see the root `AGENTS.md`. For a high-level map of the package (client/server processes, request lifecycle, module map), see `ARCHITECTURE.md`.

[...system reminder truncated in saved prompt...]

</system-reminder>@libs/code/dcode-dev.sh 添加如何在终端使用的命令<environment_details>
Current time: 2026-07-01T14:51:09+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/dcode-dev.sh
Visible files:
  libs/code/dcode-dev.sh
Open tabs:
  libs/code/dcode-dev.sh
</environment_details>

## AI Response

已添加到 `libs/code/dcode-dev.sh` 顶部：

```bash
# Terminal usage:
#   /Users/zhaojian/Desktop/deepagents/libs/code/dcode-dev.sh
#   /Users/zhaojian/Desktop/deepagents/libs/code/dcode-dev.sh --help
#   DCODE_DEV_VENV="$HOME/.local/share/dcode-dev" /Users/zhaojian/Desktop/deepagents/libs/code/dcode-dev.sh
```
