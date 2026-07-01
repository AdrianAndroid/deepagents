# Explain Global Terminal Dcode Dev Path

- Time: 2026-07-01T14:54:17+08:00
- Project: deepagents

## Prompt

想在终端任何地方都可以使用, 是不是需要加一个环境变量?<environment_details>
Current time: 2026-07-01T14:54:17+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/dcode-dev.sh
Visible files:
  libs/code/dcode-dev.sh
Open tabs:
  libs/code/dcode-dev.sh
</environment_details>

## AI Response

是，需要配置 `PATH`，让终端能找到命令。

推荐做法：

```bash
mkdir -p ~/.local/bin
ln -sf "$HOME/.local/share/dcode-dev/bin/dcode" "$HOME/.local/bin/dcode-dev"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

之后任何目录都可以运行：

```bash
dcode-dev
```

这里需要的是 `PATH` 环境变量，不是 `DCODE_DEV_VENV`；后者只是用来自定义虚拟环境位置。
