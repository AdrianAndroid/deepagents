# Add Global Path Setup To Dcode Script

- Time: 2026-07-01T14:55:47+08:00
- Project: deepagents

## Prompt

将这个加入脚本<environment_details>
Current time: 2026-07-01T14:55:47+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/dcode-dev.sh
Visible files:
  libs/code/dcode-dev.sh
Open tabs:
  libs/code/dcode-dev.sh
</environment_details>

## AI Response

已加入 `libs/code/dcode-dev.sh`。

现在脚本会：
- 安装/更新开发版 `dcode`
- 创建 `~/.local/bin/dcode-dev` 软链接
- 自动把 `~/.local/bin` 写入 `~/.zshrc`

运行脚本后执行：

```bash
source ~/.zshrc
dcode-dev
```
