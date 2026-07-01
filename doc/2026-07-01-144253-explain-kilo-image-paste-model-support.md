# Explain Kilo Image Paste Model Support

- Time: 2026-07-01T14:42:53+08:00
- Project: deepagents

## Prompt

ERROR: Cannot read "image.png" (this model does not support image input). Inform the user.kilo code插件, 为什么我能粘贴图片,但不支持处理图片呢?
我用的火山引擎codingplan, 接入codex是可以解释图片的<environment_details>
Current time: 2026-07-01T14:42:53+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
</environment_details>

## AI Response

能粘贴图片 ≠ 当前模型能读图。Kilo Code 的前端支持图片附件，但是否能处理取决于当前模型/Provider 在 Kilo 中是否声明支持 image input。

你现在用的是火山引擎 `codingplan` / 当前模型链路，Kilo 判断它不支持图片，所以报：`this model does not support image input`。
Codex 能解释图片，是因为你接入 Codex 时用的是支持视觉的模型/通道，不代表火山这个 coding 模型也支持。

解决：在 Kilo 里切换到明确支持视觉输入的模型；或用火山的视觉模型 ID，而不是 coding-only 模型。
