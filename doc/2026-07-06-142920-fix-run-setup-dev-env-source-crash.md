# Fix run-setup-dev-env.sh crash when sourced

- Time: 2026-07-06T14:29:20+08:00
- Project: deepagents

## Prompt

run-setup-dev-env.sh 这个脚本通过source 运行vscode命令就崩溃了, 修改脚本

## AI Response

已在 `libs/code/run-setup-dev-env.sh` 顶部添加 source 执行防护（`libs/code/run-setup-dev-env.sh:19-24`）。

问题原因：该脚本包含 `set -e`、`cd`、`conda activate`、`exit` 等命令，通过 `source` 执行时会污染当前 shell；一旦出错或执行到 `exit`，会直接关闭 VS Code 等集成终端。

修改内容：

```bash
# 禁止通过 source 执行：source 会污染当前 shell，且脚本中的 exit 会关闭 VS Code 等终端
if [[ -n "${BASH_SOURCE[0]}" ]] && [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "❌ 请直接运行本脚本，不要通过 source 执行: ./$(basename "${BASH_SOURCE[0]}")" >&2
    return 1
fi
```

现在若误用 `source libs/code/run-setup-dev-env.sh`，会立即提示并返回错误，不会崩溃终端。正确用法仍是直接执行：

```bash
./libs/code/run-setup-dev-env.sh
```
