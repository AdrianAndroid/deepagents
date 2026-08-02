# Dcode Image Input Model Error

- Time: 2026-07-01T14:10:24+08:00
- Project: deepagents

## Prompt

ERROR: Cannot read "image.png" (this model does not support image input). Inform the user.打开之后显示这个<environment_details>
Current time: 2026-07-01T14:10:24+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Open tabs:
  doc/2026-07-01-135504-run-deepagents-code-cli.md
</environment_details>

## AI Response

这个错误表示：当前选择的模型不支持图片输入，但启动/对话里传入了 `image.png`。

处理方式：

1. 不需要图片时，删除输入里的图片引用，只发文字任务。
2. 需要看图时，切换到支持 vision/image input 的模型。
3. 如果你用的是自定义 OpenAI 兼容 API，确认该模型是否真的支持图片；很多兼容模型只支持文本。

可以启动后执行：

```txt
/model
```

选择支持图片的模型；或者启动时指定：

```bash
uv run dcode --model openai:你的视觉模型名
```

如果只是想跑代码助手，推荐先用纯文本模型，不要附带 `image.png`。
