# dcode 服务器启动错误与 /model 命令链路分析

会话日期：2026-07-04
涉及包：`libs/code`（deepagents-code）

---

## 轮次 1 - `Server graph 'agent' did not initialize within 60s` 报错含义

### 用户提问要点
询问 `dcode` 启动时报错：

```
Error: Server failed to start: RuntimeError: Server graph 'agent' did not initialize within 60s
```

### 结论 / 方案

**报错来源**：`libs/code/deepagents_code/server.py:543` 的 `wait_for_graph_ready()` 方法。

**机制**：
- `dcode` 会本地拉起 `langgraph dev` 子进程作为 Server。
- 客户端轮询健康接口 `GET {server_url}/assistants/agent/graph`。
- 超时时间常量：`_HEALTH_TIMEOUT = 60`（`server.py:42`）。
- 60 秒内该 HTTP 请求一直没成功返回 200 就抛出该错误。

### 常见根因

1. **图初始化时的慢/阻塞动作**（最常见）
   - LLM SDK 冷启动
   - `create_deep_agent` 中的中间件加载 skills / MCP servers 太慢
   - MCP server 连接慢/hang（当前 `reference-langchain` 已 URL 不可达；`docs-langchain` 也是 HTTP MCP）
   - 网络代理/DNS 导致首次导入依赖包卡住
2. **依赖/环境问题**：`langgraph-cli` 版本不匹配，缺 `[inmem]` extra，Python 解释器与 `.venv` 不一致
3. **端口/权限**：端口被占、防火墙拦截 localhost（较少见）
4. **子进程已挂但错误未被完全捕获**：一般 message 会附带日志尾部内容

### 排查建议
- 看抛出的完整 message，后面附带 `_extract_startup_error_marker` 提取的启动错误摘要 + 日志尾部（`_LOG_TAIL_CHARS`），那里才是真正原因。
- 手动跑一次：`uv run langgraph dev`，观察到底卡在哪一步。
- 临时禁用可疑 MCP server。
- 需要更长时间可以临时把 `_HEALTH_TIMEOUT` 调大验证是不是纯粹慢启动。

---

## 轮次 2 - 如何查看 `DEEPAGENTS_CODE_DEBUG=1` 的日志

### 用户提问要点
已设置 `export DEEPAGENTS_CODE_DEBUG=1`，问怎么查看日志。

### 结论 / 方案

**该错误属于启动崩溃 → 应看 server 子进程日志，不是 client 日志。**

**日志位置**（macOS）：`$TMPDIR/deepagents_server_log_*.txt`（形如 `/var/folders/.../T/deepagents_server_log_<random>.txt`）。

**查看命令**：
```bash
# 列出最新日志
ls -lt ${TMPDIR:-/tmp}/deepagents_server_log_*.txt | head -5

# 实时追踪最新日志（另一个终端边跑边看）
tail -F "$(ls -t ${TMPDIR:-/tmp}/deepagents_server_log_*.txt | head -1)"
```

**关键行**：搜索 `Failed to initialize server graph`，下方的 traceback 才是真正失败原因（MCP 校验、sandbox 初始化、模型解析、subagent 加载…）。上方 uvicorn/lifespan 栈可忽略。

### 现场结果
在用户机器上执行 `ls` 只看到 7 月 4 日的两个日志（在设置环境变量之前生成），没有对应最近报错的保留日志。**必须重新复现一次**，才能在 `$TMPDIR` 找到最新的诊断文件。

### 两个 DEBUG 环境变量对照

| 变量 | 作用 |
| --- | --- |
| `DEEPAGENTS_CODE_DEBUG` | 主开关。退出时保留 server 子进程日志（stderr 打印路径），并给 client 加 `DEBUG` file handler |
| `DEEPAGENTS_CODE_DEBUG_FILE=<path>` | 覆盖 client 日志路径（默认 `/tmp/deepagents_debug.log`）。**只在主开关为 truthy 时生效**，不影响 server 子进程日志 |

对应文档：`libs/code/DEVELOPMENT.md#Debugging`。

---

## 轮次 3 - `/model` 命令完整链路总结（用于排查自定义供应商没回显）

### 用户提问要点
希望知道 `/model` 命令内部完整链路，用来定位「自定义供应商没有在 `/model` 列表中显示」的问题。

### 结论 / 方案（链路总览）

#### 1. 命令入口

- **注册**：`command_registry.py:135` — `SlashCommand(name="/model", bypass_tier=IMMEDIATE_UI, argument_hint="[<provider>:<model>|--model-params JSON|--default <model>|--clear]")`
- **分发**：`app.py:9432`
  - `cmd == "/model"` → `_show_model_selector()` 打开选择器
  - `cmd startswith "/model "` → 解析：
    - `--default <spec>` → `_set_default_model()` 写 `[models].default`
    - `--default --clear` → `_clear_default_model()`
    - `<provider:model>` → `_switch_model()` 直接切换
    - 支持 `--model-params <JSON>`（per-session，不持久化）

#### 2. 选择器数据加载 `_show_model_selector`

- **位置**：`app.py:12353`，挂载 `ModelSelectorScreen`（`widgets/model_selector.py`）。
- **`on_mount` → `_load_model_data`**（`widgets/model_selector.py:706` → `:550`），后台线程调用：
  ```python
  available = get_available_models()   # dict[provider, list[model]]
  config    = ModelConfig.load()       # 解析 ~/.deepagents/config.toml
  ```
- 展平为 `[(f"{provider}:{model}", provider), ...]` → `_unfiltered_models`。
- 追加"推荐但未安装/未列出"模型（`install_extras`）。
- 经 `_apply_subset` 得到 `_all_models`。

#### 3. 模型/供应商聚合来源 `get_available_models`（`model_config.py:928`）

**有进程级缓存** `_available_models_cache`，需要 `clear_caches()` 才会重算。按顺序做三件事：

1. **LangChain registry**：遍历 `_get_provider_profile_modules()` 中列出的内建供应商（`openai`, `anthropic`, `google_*`, `fireworks`, `ollama` …），从各包 `_profiles` 读模型；`config.is_provider_enabled(provider)` 为 False 时跳过。
2. **config.toml 里的自定义 providers**（`~/.deepagents/config.toml` → `[models.providers.<id>]`，`model_config.py:993`）：
   ```python
   for provider_name, provider_config in config.providers.items():
       if not config.is_provider_enabled(provider_name):
           continue                                       # enabled=false 直接跳过
       config_models = list(provider_config.get("models", []))
       # 若 models 为空且不在 registry → 尝试通过 class_path 找 _profiles 自动发现
       ...
       if provider_name not in available:
           available[provider_name] = config_models or ["custom_model"]
       else:
           # provider 已被 registry 命中 → 只**追加**未重复模型，不新建 provider 组
           existing = set(available[provider_name])
           for m in config_models:
               if m not in existing:
                   available[provider_name].append(m)
   ```
3. **Ollama 探活** + **`openai_codex` 镜像**（把 `openai` 中属于 `CODEX_MODELS` 的模型再挂到 `openai_codex` 下）。

#### 4. `/add-provider` 落盘 `save_custom_provider`（`model_config.py:3660`）

- 写入 `~/.deepagents/config.toml` 的 `[models.providers.<provider_id>]`。
- 结尾调用 `clear_caches()`，下一次 `get_available_models()` 会重新读盘。

#### 5. 渲染分组 `_update_display`（`widgets/model_selector.py:968`）

- 按 provider 分组。
- `_provider_availability_rank` 把可用 provider 排最上：`AVAILABLE < UNKNOWN < MISSING < UNINSTALLED`。
- `get_provider_auth_status()` 决定每行右侧凭证徽标。

### 「自定义供应商没有回显」的排查顺序

1. **落盘是否成功**：确认 `~/.deepagents/config.toml` 里 `[models.providers.<id>]` 存在，且 `models = [...]` 非空。
2. **是否被禁用**：`enabled = false` 会让 `is_provider_enabled` 返回 False，直接跳过（`model_config.py:997`）。
3. **是否和内建 provider 撞名**：若 `provider_id` 已在 registry（如 `openai`），只走"追加模型"分支——不会新建 provider 组，模型会并入原分组。
4. **`models` 为空且非 registry**：走 `_profile_module_from_class_path` 自动发现；失败则 fallback 成 `["custom_model"]`（`:1042`）。若只看到 `custom_model` 一条就是这条路径。
5. **缓存问题**：`_available_models_cache` 是进程级缓存。`save_custom_provider` 结尾会 `clear_caches()`，但若是**手工改了 config.toml** 或在另一个进程中添加，需在当前 TUI 里执行 `/reload` 才会重算。
6. **子集过滤盖住了**：`_apply_subset` 在 curated（onboarding）或 `_recommended_only`（Ctrl+R）模式下只显示推荐子集 ∪ MRU。按 **Ctrl+R** 切到完整视图，或直接在过滤框输入 `provider:model`。
7. **`get_provider_auth_status` 判为不可用**：不影响显示，但会被排到最底，滚不到会误以为没有。

### 快速诊断脚本（不改代码）

```bash
python - <<'PY'
from pathlib import Path
import tomllib
p = Path.home() / ".deepagents" / "config.toml"
data = tomllib.loads(p.read_text())
providers = data.get("models", {}).get("providers", {})
print("providers:", list(providers.keys()))
for k, v in providers.items():
    print(k, "enabled=", v.get("enabled", True), "models=", v.get("models"))
PY
```

之后在 TUI 里 `/reload` 强制清缓存 → `/model` + `Ctrl+R` 看完整列表。

### 关键文件与行号索引

| 位置 | 说明 |
| --- | --- |
| `libs/code/deepagents_code/command_registry.py:135` | `/model` 命令注册 |
| `libs/code/deepagents_code/app.py:9432` | `/model` 分发逻辑 |
| `libs/code/deepagents_code/app.py:12353` | `_show_model_selector` |
| `libs/code/deepagents_code/app.py:9474` | `/add-provider` 处理 |
| `libs/code/deepagents_code/widgets/model_selector.py:550` | `_load_model_data` |
| `libs/code/deepagents_code/widgets/model_selector.py:968` | `_update_display` 渲染 |
| `libs/code/deepagents_code/model_config.py:928` | `get_available_models` |
| `libs/code/deepagents_code/model_config.py:993` | 自定义 providers 合并逻辑 |
| `libs/code/deepagents_code/model_config.py:2324` | `ModelConfig.load` |
| `libs/code/deepagents_code/model_config.py:3660` | `save_custom_provider` |
| `libs/code/deepagents_code/model_config.py:775` | `clear_caches` |

### 后续 TODO
- 待用户重新复现 60s 超时错误后，回来读取 `$TMPDIR/deepagents_server_log_*.txt` 中的 `Failed to initialize server graph` traceback，定位真正根因。
- 待用户确认自定义供应商在 config.toml 中的实际写入形式，若被并入内建 provider 分组或落到 `custom_model` 兜底，则回到对应分支进一步排查。
