### 轮次 - LangGraph server readiness BlockingError 修复

**用户提问要点：** 启动 server 时报错：
```
Server failed to start: RuntimeError: Server graph 'agent' failed readiness check (status: 500): BlockingError: Blocking call to os.getcwd()
```

**问题分析：**
- LangGraph dev server 在事件循环上运行 graph factory `deepagents_code.server_graph.make_graph()`。
- 当应用未通过环境变量传入项目上下文（`DEEPAGENTS_CODE_SERVER_CWD` 缺失）时，`deepagents_code.config._ensure_bootstrap()` 在懒加载 `settings` 时会调用 `_load_dotenv(start_path=None)`，内部回退到 `Path.cwd()`，即同步调用 `os.getcwd()`。
- LangGraph dev server 集成了 `blockbuster`，会拒绝事件循环上的同步 I/O 调用，因此触发 `BlockingError: Blocking call to os.getcwd()`，readiness 返回 500。

**关键操作或文件改动：**
- `libs/code/deepagents_code/server_graph.py`
  - 在 `_make_graph()` 中，若 `get_server_project_context()` 返回 `None`，改用 `asyncio.to_thread(os.getcwd)` 在 worker 线程计算 cwd。
  - 将 cwd 写回 `DEEPAGENTS_CODE_SERVER_CWD` 环境变量，确保懒加载的 `settings` 不会回退到 `Path.cwd()`。
  - 同时在线程中计算 `project_root`，构造 `ProjectContext` 并传给下游的 MCP 发现和 `create_cli_agent`，避免 `mcp_tools._resolve_project_config_base` 回退到 `Path.cwd()`。
  - 新增导入：`pathlib.Path`、`os`、`SERVER_ENV_PREFIX`、`find_project_root`。
- `libs/code/tests/unit_tests/test_server_graph.py`
  - `test_auto_discovery_loads_mcp_without_explicit_config`：更新断言，验证无 env 上下文时 `make_graph()` 会自动计算并传递 `project_context`。
  - `test_interpreter_settings_apply_before_agent_construction`：在 mock settings 上补充 `reload_from_environment`，因为修复后 `project_context` 非空会调用该方法。

**验证结果：**
- 独立验证脚本复现了无 env 上下文场景，`make_graph()` 成功构造 `ProjectContext(user_cwd=..., project_root=...)` 并调用下游，输出 `OK`。
- `ruff check deepagents_code/server_graph.py tests/unit_tests/test_server_graph.py` 通过。
- `ty check deepagents_code/server_graph.py tests/unit_tests/test_server_graph.py` 通过。
- 直接运行 `pytest` 受当前 Windows 环境限制：pytest 的 `tmp_path` fixture 在创建 `current` 符号链接时挂起（`os.symlink` 阻塞），导致测试套件无法在该环境中执行。已通过独立脚本完成核心逻辑验证。

**后续 TODO：**
- 在支持符号链接的 Windows 环境（开启 Developer Mode 或具备相应权限）中补跑 `pytest tests/unit_tests/test_server_graph.py`，确认官方测试全部通过。
- 观察是否还有其他在 server 事件循环上的同步 I/O 调用被 `blockbuster` 拦截（例如 `os.stat`），必要时继续 offload 到线程。

#### 复盘更正：真正的根因与最终修复

上一次的 `server_graph.py` 改动只覆盖了「缺失项目上下文」这一种情况，用户重启后仍报同样的 `os.getcwd` BlockingError。通过在事件循环线程上给 `os.getcwd` 打桩打印调用栈（临时脚本）复现，定位到真正根因：

- 即使 `DEEPAGENTS_CODE_SERVER_CWD` 已设置，graph factory 在事件循环上仍会触发大量同步文件 I/O：
  - 懒加载 `settings` 时 `_ensure_bootstrap()` → `dotenv.find_dotenv(usecwd=True)`（直接 `os.getcwd()`）、`Settings.from_environment()` → `find_project_root()` → `Path.resolve()`。
  - `settings.reload_from_environment()` → `_load_dotenv` / `find_project_root` / `_git._normalize_lookup_path` → `Path.resolve()`。
  - **关键：Windows 上 `Path.resolve()` 内部会调用 `os.getcwd()`**，因此这些看似与 cwd 无关的路径解析都会被 `blockbuster` 拦截。
- `blockbuster` 是 `langgraph dev`（`langgraph_runtime_inmem/queue.py`）在事件循环上启用的，用于捕获阻塞调用。它提供官方逃生开关：环境变量 `LANGGRAPH_ALLOW_BLOCKING=true`（对应 CLI `--allow-blocking`）。

**最终修复（已回退之前的 server_graph/测试改动，保持聚焦）：**
- `deepagents_code/server.py::_build_server_env()` 增加 `env["LANGGRAPH_ALLOW_BLOCKING"] = "true"`，让 dcode 启动的 `langgraph dev` 子进程不再对 graph 构建期间合法的同步文件 I/O 抛 `BlockingError`。
- `tests/unit_tests/test_server_helpers.py` 新增 `test_allows_blocking_io_on_dev_server` 断言该环境变量被设置。

**验证：**
- 临时打桩脚本确认根因来自 `settings` 引导 / `reload_from_environment` 中的 `Path.resolve()` → `os.getcwd()`。
- 阅读 `langgraph_runtime_inmem/queue.py` 确认 `LANGGRAPH_ALLOW_BLOCKING=true` 会跳过 blockbuster。
- `python -c "from deepagents_code.server import _build_server_env; ..."` 打印 `LANGGRAPH_ALLOW_BLOCKING= true`。
- `ruff`、`ty` 检查通过；pytest 仍因本机 `tmp_path` 符号链接挂起无法运行（环境问题，与本改动无关）。

**遗留 TODO：**
- 若希望彻底避免事件循环阻塞（而非放行），可后续将 `settings` 引导与项目根探测整体 offload 到线程，或改造为异步；当前采用官方 `--allow-blocking` 开关是最小且符合 langgraph dev 设计意图的修复。

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

### 轮次 - 只设 env 变量不生效，补传 `--allow-blocking` flag

**用户提问要点：** 重启后仍报同样的 `BlockingError: Blocking call to os.getcwd`；要求修正 `libs/code` 下的项目。

**问题分析（补充上一会话遗漏的根因）：**
- 上一会话只在 `_build_server_env()` 设置了 `LANGGRAPH_ALLOW_BLOCKING=true`，但**该 env 值会被 `langgraph dev` 覆盖**，所以实际未生效。
- 通过阅读已安装依赖源码（`.venv` 内）定位：
  - `langgraph_api/cli.py:272` 的 `run_server()` 用 `patch_environment(...)` 把 `LANGGRAPH_ALLOW_BLOCKING=str(allow_blocking).lower()` **无条件写入**，`allow_blocking` 默认 `False`，即覆盖成 `"false"`。
  - `langgraph_runtime_inmem/queue.py:98` 读取该 env 决定是否启用 blockbuster。
  - `langgraph_cli/cli.py:715` 的 `dev` 命令支持 `--allow-blocking` flag，其值最终传入上面的 `allow_blocking`。
- 结论：deepagents 的 `_build_server_cmd()` 没有传 `--allow-blocking`，导致 env 被重置为 false，blockbuster 激活，`Path.resolve()` → `os.getcwd()`（Windows）报错。

**关键操作或文件改动：**
- `libs/code/deepagents_code/server.py`
  - `_build_server_cmd()` 在 argv 中新增 `--allow-blocking` flag，并补注释说明 `langgraph dev` 会用该 flag 覆盖 env 变量。
  - `_build_server_env()` 处更新注释：env 变量仅为完整性保留，真正生效靠 `--allow-blocking` flag。
- `libs/code/tests/unit_tests/test_server_helpers.py`
  - 新增 `test_includes_allow_blocking`，断言命令包含 `--allow-blocking`。

**环境说明：**
- 本机 `uv`/`conda`/`rg` 均不在 PATH；conda 位于 `C:\ProgramData\miniconda3`，其 `deepagents` 环境未装 pytest。
- 最终使用项目自带 `D:\deepagents\libs\code\.venv\Scripts\python.exe` 运行验证。

**验证结果：**
- `.venv` python 运行 `pytest tests/unit_tests/test_server_helpers.py`：19 passed。
- `ruff check deepagents_code/server.py tests/unit_tests/test_server_helpers.py`：通过。

**后续 TODO：**
- 无。彻底 offload 阻塞 I/O 的 TODO 仍如上一会话所述，属可选优化。
