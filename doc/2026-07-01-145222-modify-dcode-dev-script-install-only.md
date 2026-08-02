# Modify Dcode Dev Script Install Only

- Time: 2026-07-01T14:52:22+08:00
- Project: deepagents

## Prompt

修改脚本,只构建和安装脚本, 不启动TUI<environment_details>
Current time: 2026-07-01T14:52:22+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/dcode-dev.sh
Visible files:
  libs/code/dcode-dev.sh
Open tabs:
  libs/code/dcode-dev.sh
</environment_details>

## AI Response

已修改 `libs/code/dcode-dev.sh`：现在只创建/更新虚拟环境并 editable 安装 `libs/code`，不会启动 TUI。

安装后运行：

```bash
$HOME/.local/share/dcode-dev/bin/dcode
```
