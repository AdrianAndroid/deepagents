# dcode Session-End Summary 内置

### 轮次 1 - 需求

用户要求 session 结束时（正常/异常/中断）在末尾追加：
1. 结束原因（区分完成/中断/异常）
2. 本次 session 总时长

因为是 fork 后分发给终端用户，必须**代码内置**（不能靠 hooks.json）；同时要**尽量少影响上游 deepagents 合并**。

### 轮次 2 - 方案

采用 **atexit + sys.excepthook + signal handler mark_reason** 组合，把所有逻辑收在**单个新模块** `deepagents_code/session_end_summary.py`。

**分类**：
- `completed` — 正常退出 / `/exit` / Ctrl-D / `sys.exit(0)`
- `interrupted` — Ctrl-C（KeyboardInterrupt）/ SIGTERM / SIGHUP / SIGQUIT
- `error` — 任何未捕获异常（附 `ExcType: msg`，截断 500 字符）

**三个输出 sink**：
1. **stderr 面板** — atexit 后打印，textual/rich teardown 完毕不会被吞
2. **`~/.deepagents/.state/session_end/<thread_id>.txt`** — 每 session 一个文件，覆盖式
3. **`~/.deepagents/session_end_log.jsonl`** — 追加式审计日志（一行 JSON）

**优先级**：`error > interrupted > completed`，后来的低优先级不会覆盖已记录的高优先级（例如异常已抛后 atexit 仍报 error 而非 completed）。

### 轮次 3 - 改动清单

| 文件 | 改动 | 目的 |
|---|---|---|
| `deepagents_code/session_end_summary.py` | **新增** | 全部逻辑：install / mark_reason / mark_signal / set_thread_id / _finalize / _reset_for_tests |
| `deepagents_code/main.py` | +3 处 | (a) `cli_main` 顶部（fast path 之后）`install()`；(b) `_handle_termination_signal` 在 `raise SystemExit` 前 `mark_signal(signum)`；(c) `KeyboardInterrupt` 分支 `mark_reason(REASON_INTERRUPTED, "KeyboardInterrupt")` |
| `deepagents_code/app.py` | +1 处 | 现有 `session.end` 派发块内 `set_thread_id(self._lc_thread_id)` |
| `deepagents_code/client/non_interactive.py` | +1 处 | 现有 `dispatch_hook("session.end", ...)` 之后 `set_thread_id(thread_id)` |
| `tests/unit_tests/test_session_end_summary.py` | **新增** | 7 个单测覆盖三条路径 + 幂等 + 优先级 + 文件名 sanitize |

**上游合并友好性**：
- 所有新代码在独立文件，不改公共 API
- 4 个 hook 点都是**块内追加行**（不是修改现有行），且都用 `try/except` 包住失败自愈
- 主线代码里的 4 个 hook 点分别是"cli_main 顶部"、"signal handler"、"KeyboardInterrupt 分支"、"session.end 派发块"，这几处在上游是极稳定区域

### 轮次 4 - 验证

```bash
# 单元测试
uv run --group test pytest tests/unit_tests/test_session_end_summary.py -q
# 7 passed

# 相邻区域回归
uv run --group test pytest tests/unit_tests/test_main.py \
  tests/unit_tests/test_non_interactive.py tests/unit_tests/test_hooks.py \
  tests/unit_tests/test_session_stats.py tests/unit_tests/test_sessions.py -q
# 463 passed

# 手动 smoke
uv run dcode --version       # 不打印面板（fast path 早于 install）
uv run dcode doctor          # 打印 completed 面板
python -c "...RuntimeError..."  # 打印 error 面板 + 异常信息
```

### 关键设计决策记录

1. **install() 放在 `--version` fast path 之后**：避免 `dcode --version` 输出被 session-end 面板污染
2. **`_reset_for_tests` 必须 `atexit.unregister`**：否则每次测试 install 都会累积到 pytest 进程退出打印面板
3. **excepthook 特判 KeyboardInterrupt/SystemExit**：`SystemExit` 不算 error；`KeyboardInterrupt` 从 error 降级为 interrupted
4. **stderr 而不是 stdout**：面板是元信息，headless 模式下用户可能重定向 stdout 到管道
5. **`format_duration` 懒加载 + 本地兜底**：避免测试 mock 或 fast path 强依赖 `deepagents_code.formatting`

### 后续 TODO

- 考虑加个 config 开关（`[session_end].disable_panel = true`）让用户可关面板
- JSONL 文件轮转（当前无上限，长期用户会累积）
- Windows 上信号语义验证（`_install_termination_signal_handlers` 在 win32 上跳过，signal path 只能靠 excepthook）
- （可选）终端交互模式下，在 stderr 面板之前额外用 rich 渲染一次带颜色版本
