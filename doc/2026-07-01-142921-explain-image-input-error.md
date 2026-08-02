# Explain Image Input Error

- Time: 2026-07-01T14:29:21+08:00
- Project: deepagents

## Prompt

ERROR: Cannot read "image.png" (this model does not support image input). Inform the user.这个都是什么意思?<environment_details>
Current time: 2026-07-01T14:29:21+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/dcode-dev.sh
Visible files:
  libs/code/dcode-dev.sh
Open tabs:
  libs/code/dcode-dev.sh
</environment_details>

## AI Response

意思是：程序尝试读取 `image.png`，但你当前选择的 AI 模型不支持图片输入，所以无法分析这张图。

分解：
- `ERROR`：发生错误。
- `Cannot read "image.png"`：无法读取/处理这张图片。
- `this model does not support image input`：当前模型不支持视觉/图片能力。
- `Inform the user`：系统提示助手要把这个原因告诉用户。

解决：换支持图片的模型，或不要上传图片，只发文字。
