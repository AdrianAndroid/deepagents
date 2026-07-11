# 图片粘贴触发 BadRequestError 且 Agent 后续失效 - 问题诊断与修复

## 问题现象

用户在 TUI 中粘贴图片后:
1. 出现错误: `Agent error: BadRequestError: An internal error occurred`
2. 之后 Agent **再也不工作了** - 后续每次发送消息都会失败

## 根因分析

### Bug 1: BadRequestError 的根源

在 `deepagents_code/media_utils.py` 中,剪贴板图片的读取路径 **完全没有做大小验证**:

- `get_image_from_path()` (拖放文件路径) 有 `MAX_MEDIA_BYTES` (20MB) 检查 (line 312)
- **但是** `_get_macos_clipboard_image()`、`_get_windows_clipboard_image()`、`_get_linux_clipboard_image()`、`_get_clipboard_via_osascript()` 都没有这个检查

当用户粘贴大图(如高分辨率截图),base64 编码后的 payload 超过 provider API 的请求大小限制,provider 返回 `BadRequestError`,LangGraph 服务端将其序列化为 `{"error": "BadRequestError", "message": "An internal error occurred"}`(通用兜底消息)。

### Bug 2: Agent 再也不工作 - Thread Checkpoint 中毒

关键路径分析 (`textual_adapter.py:700-706`):
```python
async for chunk in agent.astream(
    stream_input,
    stream_mode=["messages", "updates", "custom"],
    subgraphs=True,
    config=config,
    context=context,
    durability="exit",  # <<< 这里
):
```

`durability="exit"` 语义是: **LangGraph 在 stream 开始前就把 user message 持久化到 checkpoint**。所以当 `agent.astream()` 抛出 `BadRequestError` 时:
- 包含损坏多模态内容的 user message **已经被写入 checkpoint**
- 之后每次新对话都会从这个 checkpoint 继续,messages 列表始终包含那条坏消息
- 每次调用模型都会带上这条坏消息,永远失败

原代码在 `app.py:10377` 的 `except Exception as e` 里 **只是展示错误消息,没有清理 checkpoint**。用户必须手动执行 `/clear` 才能继续。

### Bug 3: Linux 剪贴板死代码

`media_utils.py:279` 有段死代码:
```python
if sys.platform == "linux":   # 匹配 Linux
    logger.warning(...)
    return None
if sys.platform.startswith("linux"):   # 永远不会执行!
    return _get_linux_clipboard_image()
```

Linux 上 `sys.platform` 就是 `"linux"`,导致第一个 `if` 命中,直接返回 `None`。`_get_linux_clipboard_image()` 永远不被调用,Linux 剪贴板粘贴图片功能实际是被静默禁用的。

## 修复方案

### 修复 1: 为所有剪贴板路径添加 MAX_MEDIA_BYTES 检查

在 `_get_macos_clipboard_image` (pngpaste 分支)、`_get_clipboard_via_osascript`、`_get_windows_clipboard_image`、`_get_linux_clipboard_image` (wl-paste 和 xclip 分支) 中,在 base64 编码之前都加入:

```python
if len(image_bytes) > MAX_MEDIA_BYTES:
    logger.warning("Clipboard image is too large (%d MB, max %d MB)", ...)
    return None
```

### 修复 2: 添加 checkpoint 回滚机制

在 `app.py` 中新增 `_rollback_last_user_message()` 方法:

- 通过 `agent.aget_state(config)` 拿到当前 thread state
- 从末尾反向遍历,找到最近的 `HumanMessage` (skip 掉包含 `SYSTEM_MESSAGE_PREFIX` 的注入消息)
- 用 `agent.aupdate_state(config, {"messages": [RemoveMessage(id=...)]})` 将其移除
- 所有异常都被 catch 并 log 到 debug (回滚只是尽力而为,失败也不能覆盖原始错误)

在 `_run_agent_task` 的 `except Exception as e:` 分支中,展示错误消息之前调用 `await self._rollback_last_user_message()`,让下一轮对话不再带上这条坏消息。

### 修复 3: 增强错误提示

在 `_build_agent_error_body()` 中为 `BadRequestError` 添加可操作的指引:

```
The request was rejected by the model provider. If you pasted an image,
it may be too large or in an unsupported format. The failed message has
been removed from the conversation so you can continue. Try a smaller
image or use `/clear` to start fresh.
```

### 修复 4: 移除 Linux 死代码

统一使用 `sys.platform.startswith("linux")`,让 Linux 用户实际能用剪贴板粘贴图片。

## 涉及文件

| 文件 | 改动 |
|---|---|
| `deepagents_code/media_utils.py` | 5 处剪贴板路径添加大小验证 + 修复 Linux 死代码 |
| `deepagents_code/app.py` | 新增 `_rollback_last_user_message` + 在错误处理中调用 + `_build_agent_error_body` 增加 BadRequestError 分支 |
| `tests/unit_tests/test_media_utils.py` | 新增 `test_pngpaste_oversized_image_returns_none` + 修正 unsupported_platform 测试 (Linux 现在支持了,改用 freebsd) + import `MAX_MEDIA_BYTES` |
| `tests/unit_tests/test_error_handling.py` | 新建,测试 `_build_agent_error_body` 的 BadRequestError/PermissionDeniedError/其他错误 3 种分支 |

## 测试结果

```
260 passed in 50.05s (test_media_utils.py + test_error_handling.py + test_chat_input.py)
```

- `TestGetClipboardImage::test_pngpaste_oversized_image_returns_none` 通过
- `TestBuildAgentErrorBody` 3 个测试全部通过
- 无回归

## 关键设计决策

1. **回滚只是尽力而为**: `_rollback_last_user_message` 中所有异常都被吞掉并 log 到 debug,绝不能让回滚失败掩盖原始错误(用户必须看到 `error_text`)。

2. **通过 message id 定位**: LangGraph 的 `RemoveMessage(id=msg_id)` 是标准做法,基于 `DeltaChannel` reducer 自动处理。不需要重写整个 messages 列表。

3. **跳过系统注入消息**: 反向扫描时跳过 `SYSTEM_MESSAGE_PREFIX` 开头的消息(比如 skill 注入的),只回滚真正的用户消息。

4. **大小检查在编码之前**: 在 base64 编码之前拒绝大图,避免浪费 CPU 做无谓的编码。20MB 原始字节 -> 约 27MB base64,超出多数 provider 的限制。

## 后续 TODO

- 考虑给 `[image N]` placeholder 加大小提示,让用户在粘贴时就能看到会不会超限
- 考虑自动缩放超限图片(用 PIL resize 到合适尺寸)而非直接拒绝
- 可考虑在 chat_input 的 `_on_paste` 里加 try/except 兜底,防止未预期的异常导致粘贴处理器崩溃
