# Create Dcode Dev Script

- Time: 2026-07-01T14:25:07+08:00
- Project: deepagents

## Prompt

/libs/code在项目目录下,创建可以直接使用的脚本文件, 确保每次直接运行脚本就可以直接执行<environment_details>
Current time: 2026-07-01T14:25:07+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: doc/2026-07-01-142323-explain-editable-dcode-dev-commands.md
Visible files:
  doc/2026-07-01-142323-explain-editable-dcode-dev-commands.md
Open tabs:
  doc/2026-07-01-142323-explain-editable-dcode-dev-commands.md
</environment_details>

## AI Response

已创建：

`libs/code/dcode-dev.sh`

使用方式：

```bash
/Users/zhaojian/Desktop/deepagents/libs/code/dcode-dev.sh
```

脚本每次运行会确保开发虚拟环境存在、以 editable 模式安装/更新 `libs/code`，然后直接启动 `dcode`。
