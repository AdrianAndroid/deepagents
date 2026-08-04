# learn 分支功能总览 —— zhaojian & ext_zhaojian03 全部改动

> **用途**: 便于在 main 分支下重新开发这些功能
> **对比基准**: fork point `970952550` → learn `ab9b2acac`
> **作者**: zhaojian (18310579837@163.com), ext_zhaojian03 (ext_zhaojian03@kuaishou.com)
> **提交数**: 137 个非合并提交 (2026-07-01 ~ 2026-08-03)
> **改动规模**: 35 个源码文件 (+3427/-258), 25 个测试文件, 2 个 SDK 文件, 脚本/工作流/文档若干

---

## 功能分类索引

| 编号 | 功能区域 | 核心文件 | 新增行数 | 复杂度 |
|------|---------|---------|---------|--------|
| A | 品牌化 (zjcode rebrand) | `_version.py`, `_constants.py`, `config.py`, `update_check.py` 等 ~15 文件 | ~400 | 低 |
| B | 自定义模型 Provider | `model_config.py`, `model_selector.py` | +884 | **高** |
| C | 图片粘贴与剪贴板复制 | `clipboard.py`, `media_utils.py`, `input.py`, `chat_input.py` | +611 | 中 |
| D | 会话/轮次结束状态追踪 | `session_end_summary.py`, `turn_end_summary.py`, `non_interactive.py`, `textual_adapter.py` | +1179 | **高** |
| E | UI 增强 | `messages.py`, `textual_adapter.py`, `app.py` | +754 | 中 |
| F | Web 终端支持 (`--no-mouse`) | `main.py`, `config_manifest.py`, `_env_vars.py` | ~50 | 低 |
| G | SDK Windows 路径兼容 | `filesystem.py`, `backends/utils.py` | +129 | 中 |
| H | Server 启动改进 | `client/launch/server.py` | +19 | 低 |
| I | 开发与发布工具链 | `bump-version.py`, `run-publish.sh`, `publish-zjcode.yml` 等 | ~200 | 低 |

---

## A. 品牌化 (zjcode Rebrand)

### A.1 核心常量

**`_version.py`** (+30 行):
```python
__version__ = "0.0.16"  # 独立 0.0.x 版本序列
DISTRIBUTION_NAME = "zjcode"   # PyPI 包名 (元数据查询、uv tool 命令)
BRAND_NAME = "zjcode"          # 用户可见品牌名 (CLI/splash/error)
PYPI_URL = f"https://pypi.org/pypi/{DISTRIBUTION_NAME}/json"
USER_AGENT = f"{DISTRIBUTION_NAME}/{__version__} update-check"
# DOCS_URL, CHANGELOG_URL 保留上游值
```

**`_constants.py`** (+19 行):
```python
CONFIG_DOTDIR: Final[str] = ".deepagents"     # 用户级 ~/.deepagents
PROJECT_DOTDIR: Final[str] = ".deepagents"    # 项目级 <root>/.deepagents
```
> 所有 `.deepagents` 路径引用统一改为读这两个常量。

**`_env_vars.py`** (+24 行):
```python
NO_MOUSE = "DEEPAGENTS_CODE_NO_MOUSE"          # 禁用鼠标追踪
PYPI_URL = "DEEPAGENTS_CODE_PYPI_URL"           # 覆盖更新检查 URL
SDK_PYPI_URL = "DEEPAGENTS_CODE_SDK_PYPI_URL"   # 覆盖 SDK 元数据 URL
```

### A.2 品牌化接线范围

| 文件 | 改动点 |
|------|--------|
| `pyproject.toml` | `name="zjcode"`, scripts `zjcode`+`deepagents-code`, extras 自引用 |
| `config.py` | `distribution(DISTRIBUTION_NAME)`, banner, 保留 `.deepagents` 路径不变 |
| `update_check.py` | FALLBACK_UPGRADE_COMMAND, brew, pkg_version, shadow 检测 bin 名, requirement 字符串, 用户提示全部→`DISTRIBUTION_NAME` |
| `main.py` | `--version` 输出, install 提示, 版本占位 |
| `app.py` | 依赖更新 diff 过滤, 更新提示, `/version` 输出 |
| `extras_info.py` | `collect_cli_version_info()`, 6 处 `distribution_name` 默认参数 |
| `agent.py` | `~/.deepagents/config.toml` → `~/{CONFIG_DOTDIR}/config.toml` |
| `mcp_tools.py` | MCP 配置发现路径 → `.deepagents/.mcp.json` |
| `project_utils.py` | skills/agents/AGENTS.md 路径 → `.deepagents/` |
| `ui.py` | help 文案路径, banner |
| `skills/commands.py` | skills 搜索路径文案 |

### A.3 版本号规则

- zjcode 独立 `0.0.x` 序列 (与 deepagents-code `0.1.x` 分离)
- PyPI 已发布 0.0.5 ~ 0.0.16
- bump-version.py 同步三处: `pyproject.toml` / `_version.py` / `.release-please-manifest.json`

### A.4 发布工作流

**`publish-zjcode.yml`** (110 行): tag `zjcode-v*` 触发 → 版本校验 → 放松 deepagents 依赖钉 → `uv build` → OIDC Trusted Publisher 发布到 PyPI。

---

## B. 自定义模型 Provider

> 让用户在 TUI 内注册任意 OpenAI 兼容网关 (火山引擎 Ark、DeepSeek、SiliconFlow 等),自动发现模型列表。

### B.1 model_config.py (+225 行)

```python
def save_custom_provider(
    provider_id: str,           # "volcengine-ark"
    display_name: str,          # "火山方舟"
    base_url: str,              # "https://ark.cn-beijing.volces.com/api/v3"
    models: list[str] | None = None,
    class_path: str = "langchain_openai:ChatOpenAI",
    api_key_env: str | None = None,
    api_key: str | None = None,
    default_model: str | None = None,
    max_input_tokens: int | None = None,
    config_path: Path | None = None,
) -> bool
```
- 原子写入 `config.toml` 的 `[models.providers.<id>]` 段
- API key 经 `auth_store.set_stored_key()` 持久化
- `max_input_tokens` 写入 `profile` 表 (让 per-call info 行渲染 `ctx=used/limit~(pct%)`)
- 成功后 `clear_caches()` 刷新内存

```python
class ModelDiscoveryError(Exception): ...  # 面向用户,可直接渲染

def fetch_provider_models(
    base_url: str,
    api_key: str | None = None,
    *,
    timeout: float = 10.0,
    include_retiring: bool = True,
) -> list[str]
```
- `GET {base_url}/models`, Bearer 鉴权
- 解析 OpenAI `{data:[...]}` 或裸 list
- 过滤 `status=="Shutdown"` (Volcengine Ark 扩展)
- 精细化错误: 401/403/404/超时/非JSON 各自抛 `ModelDiscoveryError`

**`get_available_models()` 增强**: 即使 provider 没声明模型也注册占位 `"custom_model"`。

### B.2 model_selector.py (+659 行)

三层模态栈: `ModelSelectorScreen` → `CustomProviderModalScreen` → `DiscoverModelsScreen`

**`CustomProviderModalScreen`** (表单):
- 字段: provider-id, display-name, base-url, api-key(密码框), default-model, discovered-status
- 编辑模式从 `config.toml` 预填, 禁用 ID 框防改名
- `action_discover()` → `fetch_provider_models()` → push `DiscoverModelsScreen`
- `action_submit()` → `save_custom_provider()` → dismiss `(success, provider_id, default_model)`

**`DiscoverModelsScreen`** (多选):
- `SelectionList[str]` 按 preselected 预勾选
- `Ctrl+A` 全选, `Ctrl+N` 全不选, `Enter` 确认

**关键设计**: 保存成功后直接用 `provider:model` spec 切换 (如 `volcengine-ark:doubao-pro`), 而非重载列表——裸模型名 (如 `gpt-4o`) 会被 `detect_provider` 误判为 `openai`。

**入口**: `Ctrl+A` 快捷键 / "Add Custom Provider" 按钮 / `/add-provider` 命令。

### B.3 config.py 默认模型选择链

```python
def _get_configured_provider_default_model(config: ModelConfig) -> str | None
def _model_spec_auth_is_usable(model_spec: str) -> bool
def _format_provider_default_model_spec(provider: str, model: object) -> str | None
```
默认模型优先级链 (新增 provider 级 default_model):
1. `[models].default` (用户显式偏好)
2. **provider 级 `default_model`** ← 新增
3. `[models].recent` (新增鉴权校验)
4. 凭据自动检测

**`stream_usage=True` 注入**: OpenAI 兼容 provider 自动设 `stream_usage=True`, 确保 stream chunk 携带 `usage_metadata`。

### B.4 命令注册

```python
SlashCommand(name="/add-provider",
    argument_hint='<provider-id> "<display-name>" <base-url> "<models>" [class-path] [api-key-env] [max-input-tokens]',
    bypass_tier=BypassTier.QUEUED)
SlashCommand(name="/model",
    argument_hint='[<provider>:<model>|--model-params JSON|--default <model>|--clear]')  # 新增 --default/--clear
```

---

## C. 图片粘贴与剪贴板复制

### C.1 数据结构

**`media_utils.py`** (+346 行):
```python
@dataclass
class ImageData:
    base64_data: str
    format: str           # "png" / "jpeg" / "webp" / "gif"
    placeholder: str      # "[img_20250115143022]"

PASTED_MEDIA_DIR = Path.home() / ".deepagents" / "pasted"

def get_clipboard_image() -> ImageData | None    # 跨平台读取剪贴板图片
def save_pasted_media(base64_data, stem, image_format) -> Path | None  # 归档到本地
```
跨平台支持: macOS (pngpaste/osascript), Windows (PowerShell Get-Clipboard), Linux (wl-paste/xclip)。

### C.2 clipboard.py (+91 行)

```python
def copy_image_to_clipboard(image_data: ImageData) -> tuple[bool, str | None]
def copy_image_with_feedback(app: App, image_data: ImageData) -> bool
```
macOS osascript 实现: base64 解码 → 临时 PNG 文件 → AppleScript `set the clipboard to (read ... as «class PNGf»)`。

### C.3 input.py 媒体占位符重构 (+149 行)

**旧格式**: `[image 1]`, `[video 2]` (自增整数)
**新格式**: `[img_20250115143022]`, `[vid_20250115143022]` (时间戳)

```python
def _now_timestamp() -> str: ...           # YYYYMMDDHHMMSS
def _generate_media_id(kind: MediaKind) -> str: ...  # 可测试 hook
```
- `MediaTracker` 移除 `next_image_id`/`next_video_id` 计数器
- `add_media()` 用时间戳 + `_N` 后缀消歧
- 新增 `_all_placeholders()` / `_draft_placeholders()` 去重

### C.4 chat_input.py (+25 行)

`_on_paste` 事件处理: 检测剪贴板图片 → `get_clipboard_image()` → `add_image()` → `save_pasted_media()` → 插入占位符。

### C.5 命令

```python
SlashCommand(name="/copy-image", description="Copy the most recently pasted image to the system clipboard")
SlashCommand(name="/paste-image", aliases=("/paste-img",), description="Paste an image from the system clipboard at cursor position")
```

### C.6 BadRequestError 处理 (app.py)

```python
# _build_agent_error_body 新增 BadRequestError 分支
if err_type == "BadRequestError":
    return f"{text}\n\nThe request was rejected by the model provider. If you pasted an image, it may be too large..."

# _rollback_last_user_message() (新增)
# agent.astream() 失败后用 RemoveMessage(id=last_human_msg_id) + aupdate_state
# 从 checkpoint 删除"毒消息",防止 durability="exit" 持久化让会话永久砖化
```

---

## D. 会话/轮次结束状态追踪

### D.1 session_end_summary.py (新增 329 行)

**进程级退出追踪**, 通过 `atexit` + `sys.excepthook` 在 dcode 退出时写入退出原因/耗时。

```python
def install() -> None                    # 注册 atexit + excepthook
def mark_reason(reason: str, detail: str = "") -> None
def mark_signal(signum: int) -> None     # SIGTERM/SIGINT 归因
def set_thread_id(thread_id: str) -> None
```
3 类原因: `completed` / `interrupted` / `error` (优先级 error > interrupted > completed)。
3 个 sink: stderr 面板 / `<state>/session_end/<thread>.txt` / `session_end_log.jsonl`。

**接线** (`main.py`):
- `cli_main()` 中 `session_end_summary.install()`
- `_handle_termination_signal` 中 `mark_signal(signum)` (SystemExit 绕过 excepthook)
- `except KeyboardInterrupt` 中 `mark_reason(REASON_INTERRUPTED)`

### D.2 turn_end_summary.py (新增 522 行)

**单轮级结束标记**, 记录每轮 user→assistant 交互的结束状态和耗时。

```python
def mark_turn_start(thread_id: str = "") -> None
def observe_finish_reason(finish_reason: str) -> None
def classify_exception(exc: BaseException) -> tuple[str, str]
def mark_turn_reason(reason: str, detail: str = "") -> None
def finalize_turn() -> TurnEndRecord | None
def render_marker_text(record: TurnEndRecord) -> str
```

**10 类结束状态** (`_FINISH_REASON_MAP`):

| finish_reason | 状态标签 |
|---|---|
| `stop` / `end_turn` | `completed` |
| `length` / `max_tokens` | `length_capped` |
| `content_filter` / `safety` | `content_filtered` |
| `tool_calls` / `tool_use` | None (不终结轮次) |
| (异常) | `classify_exception` 分类 |
| (用户中断) | `user_interrupted` (优先级最高) |
| (无 finish_reason) | `unknown_truncation` |

3 个 sink: TUI 聊天气泡 / `turn_end_log.jsonl` / 自动追加到当天最新 `doc/YYYY-MM-DD-*.md`。

### D.3 接线分布

**`non_interactive.py`** (headless, +57 行):
- `_process_ai_message`: 从 AI 消息提取 `finish_reason` → `observe_finish_reason()`
- `_run_agent_loop` 开头: `mark_turn_start(thread_id=...)`
- `_run_agent_loop` finally: 异常分类 + `finalize_turn()` + `render_marker_text()` 输出
- 循环结束: `session_end_summary.set_thread_id(thread_id)`

**`textual_adapter.py`** (TUI, +271 行):
- 同套 `mark_turn_start` → `observe_finish_reason` → `classify_exception` → `finalize_turn` → `render_marker_text`
- 标记挂成聊天气泡 (AppMessage, dim italic)

**`app.py`**: `session_end_summary.set_thread_id` 回填。

---

## E. UI 增强

### E.1 messages.py (+182 行)

**`SessionSeparator(Static)`** (新增):
```
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
```
每轮 user 消息前挂载。

**`CopyTurnButton(Static)`** (新增):
- 默认 `display:none`, `-visible` class 显示
- 点击反向遍历兄弟 widget 找最近 UserMessage + AssistantMessage
- 拼接后 `copy_text_with_feedback()`
- `AssistantMessage` 新增 `_stream_finalized` 标志, 在 `stop_stream`/`set_content`/`on_mount` 后显隐

**工具组默认展开**: `ToolGroupSummary._collapsed` 从 `var(True)` → `var(False)`

**edit_file 强制展开**: `self._tool_name == "edit_file" and not _is_search_no_result_output` 时 `self._expanded = True`

**todo 宽度**: `_DEFAULT_TODO_WRAP_WIDTH` 80 → 60

### E.2 textual_adapter.py (+271 行, 排除 turn_end)

**`_format_model_call_info()`** (新增): 构建单行模型调用摘要:
```
model=gpt-4o finish=stop tokens in=120/out=85/total=205 cache_read=0 ctx=205/128000~ (0.2%) elapsed=1.2s
```

**`_render_model_label()`** (新增): 区分路由别名 (`requested→served`) 和网关隐藏 (哨兵值 `auto`/`none`/`null`/`""` 仅显示 requested)。

**per-call 元数据追踪**: 四个 per-namespace dict 记录 start_time/usage/response_metadata/requested_model, 首个 chunk 开始计时, `chunk_position=="last"` 时挂载信息行并清空。

### E.3 app.py UI 改动

- `SessionSeparator` 集成 (`_handle_user_message` 开头)
- `/scrollbar`、`/timestamps`、`/editor` toggle 命令不再回显 UserMessage
- `run_textual_cli_async` 新增 `mouse: bool = True` 参数

---

## F. Web 终端支持 (`--no-mouse`)

**问题**: web 终端 (1Panel/ttyd/wetty) 转发鼠标事件但剥离 SGR 序列 ESC 前缀, 导致输入框乱码 (`[<35;36;33M...`)。

**`main.py`** (+79 行):
```python
# CLI 参数
parser.add_argument("--no-mouse", action="store_true", ...)

def _resolve_no_mouse(args: argparse.Namespace) -> bool:
    if getattr(args, "no_mouse", False): return True
    return is_env_truthy(NO_MOUSE)

# 透传
async def run_textual_cli_async(..., mouse: bool = True) -> AppResult:
    app = DCodeApp(mouse=mouse, ...)
```

**`config_manifest.py`**: 新增 `display.no_mouse` ConfigOption (BOOL, env=NO_MOUSE, cli=--no-mouse)。

---

## G. SDK Windows 路径兼容

**问题**: Windows 上 `D:\proj\file.py` 盘符路径被 `validate_path()` 拒绝。

**`backends/utils.py`** (+32 行):
```python
def validate_path(path: str, *, allow_native_absolute: bool = False) -> str:
    # 路径遍历检查 (../, ~/) 仍在最前, 不受新参数影响
    # Windows 盘符: allow_native_absolute=True → 直接返回原始路径
    #                allow_native_absolute=False → 抛 ValueError
```

**`filesystem.py`** (+97 行):
```python
def _accepts_native_absolute_paths(backend: BackendProtocol) -> bool:
    # CompositeBackend → 取 default 后端
    # 非虚拟 FilesystemBackend (含 LocalShellBackend) → True
    # 虚拟模式/非文件系统后端 → False
```
12 个 FS 工具包装器 (ls/read_file/write_file/edit_file/delete/glob/grep 的同步+异步) 均新增 `allow_native_absolute=_accepts_native_absolute_paths(resolved_backend)` 参数。

---

## H. Server 启动改进

**`client/launch/server.py`** (+19 行):
```python
# _build_server_cmd: 追加 --allow-blocking
"--allow-blocking",

# _build_server_env: 追加环境变量
env["LANGGRAPH_ALLOW_BLOCKING"] = "true"
```
**原因**: agent graph 工厂在构造期做合法阻塞读 (dotenv 发现、Path.resolve()), `langgraph dev` 的 blockbuster 集成会检测到并抛 `BlockingError`。`langgraph dev` 会用自己的 `--allow-blocking` 覆盖 env var, 所以必须同时在命令行传 flag。

---

## I. 开发与发布工具链

| 文件 | 用途 |
|------|------|
| `bump-version.py` (250 行) | 版本同步: pyproject + _version.py + .release-please-manifest.json |
| `run-publish.sh` (18 行) | `uv build` + `uv publish` 发布脚本 |
| `run-dcode-dev.sh` / `.ps1` | 本地开发启动脚本 |
| `setup-dev-env.ps1` / `run-setup-dev-env.sh` | 开发环境安装脚本 |
| `.github/workflows/publish-zjcode.yml` (110 行) | tag 触发 PyPI 发布工作流 (OIDC Trusted Publisher) |
| `scripts/benchmark_huoshan_models.py` (822 行) | 火山引擎模型编码能力基准测试 |

---

## 跨文件依赖关系

```
_constants.CONFIG_DOTDIR / PROJECT_DOTDIR
   ├─> model_config.DEFAULT_CONFIG_DIR
   ├─> config.py 各路径方法
   ├─> agent.py, mcp_tools.py, project_utils.py, ui.py, skills/commands.py

_version.DISTRIBUTION_NAME / BRAND_NAME
   ├─> update_check.py (全文件品牌化)
   ├─> main.py (version 输出, install 提示)
   ├─> config.py (distribution() 查询)
   ├─> app.py (依赖更新消息)
   └─> extras_info.py (元数据查询)

_env_vars.NO_MOUSE
   └─> main.py (_resolve_no_mouse)

model_config.save_custom_provider / fetch_provider_models / ModelDiscoveryError
   ├─> model_selector.py (CustomProviderModalScreen, DiscoverModelsScreen)
   └─> command_registry.py (/add-provider)

session_end_summary / turn_end_summary (新模块)
   ├─> non_interactive.py (headless 接线)
   ├─> textual_adapter.py (TUI 接线)
   ├─> main.py (install, mark_signal)
   └─> app.py (set_thread_id)

media_utils.ImageData / get_clipboard_image / save_pasted_media
   ├─> clipboard.py (copy_image_to_clipboard)
   ├─> chat_input.py (_on_paste)
   ├─> input.py (MediaTracker 占位符)
   └─> command_registry.py (/copy-image, /paste-image)
```

---

## 在 main 上重新开发的建议

### 优先级排序

| 优先级 | 功能 | 理由 |
|--------|------|------|
| P0 | 品牌化 (A) | PyPI 发布必需, 改动机械, 风险低 |
| P1 | 图片粘贴 (C) | 用户高频需求, 自包含, 可独立移植 |
| P1 | Web 终端 --no-mouse (F) | 改动小, 解决实际痛点 |
| P2 | 自定义 Provider (B) | 功能价值高, 但 model_selector.py 与 main 差异大 (+659 行), 需仔细适配 |
| P2 | UI 增强 (E) | CopyTurnButton/工具组展开/模型调用信息行, 提升体验 |
| P3 | 会话/轮次追踪 (D) | 诊断价值, 但接线点分散 (4 个文件), 与 main 的 app.py/textual_adapter.py 差异大 |
| P3 | SDK Windows 路径 (G) | 应直接向上游提 PR |
| P3 | Server --allow-blocking (H) | 改动小, 可快速移植 |

### main 分支 API 差异注意

1. **model_selector.py**: main 已有 fuzzy matching / 导航 / footer, learn 的增量主要是两个新模态屏, 可叠加
2. **textual_adapter.py**: main 已大幅重构 (+1672 行 vs fork point), learn 的 per-call info 行和 turn_end 接线需重新定位插入点
3. **app.py**: main 25444 行 (vs learn ~14000 行), `_build_agent_error_body` / `_handle_user_message` 等函数位置和签名可能变化
4. **clipboard.py**: main 的 `copy_selection_to_clipboard(app, *, screen)` 签名与 learn 旧版 `(app)` 不同, 移植时保留 main 签名
5. **input.py**: main 的 `MediaTracker` 可能有新改动, 需确认占位符格式兼容
6. **_invocation.py**: main 新增文件 (learn 无), STANDARD_INVOKED_NAMES 需同步更新
7. **config.py**: main 的默认模型选择链可能已演进, 需确认 provider default_model 逻辑可叠加

---

## 提交历史摘要

关键提交 (按时间顺序):

| 日期 | 提交 | 功能 |
|------|------|------|
| 07-01 | `4d94e9f27` | 更改域名 |
| 07-08 | `8ea551286` | 修改默认目录改成品牌名称 |
| 07-11 | `0c6e08f5e` | 图片粘贴 BadRequestError-Agent 失效修复 |
| 07-12 | `938081cc9` | 显示 model |
| 07-12 | `e957e0949` | 添加 TURN 结束标记到调试日志 |
| 07-15 | `856eacb74` | merge main into learn |
| 07-17 | `c5094b8ae` | zjcode 0.0.12 (custom provider support) |
| 07-18 | `8afebc7df` | add session delimiter |
| 07-18 | `f54be8a8e` | customize on first install |
| 07-27 | `786aefeb7` | merge main into learn |
| 07-29 | `0d6e2d0c2` | zjcode 0.0.7 (paste-image, 域名替换) |
| 08-02 | `ecb46befb` | zjcode 0.0.16 |
| 08-02 | `ab9b2acac` | skill |

---

*文档生成时间: 2026-08-04*
*基础: fork point 970952550 → learn ab9b2acac*
