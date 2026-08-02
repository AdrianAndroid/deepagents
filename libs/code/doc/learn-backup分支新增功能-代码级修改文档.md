# learn-backup 分支新增功能 · 代码级修改文档

> **用途**：本文档记录 `learn-backup-20260730-105659` 分支相对 `main` 分支的全部**代码级新增功能改动**，可直接用于「从 `main` 拉出新分支，按文档逐项补全功能」的移植工作。
>
> 文档只记录 backup 分支**独有的新增功能**，不记录 `main` 后来演进出、而 backup（基于较老 main）尚未合入的内容（例如 `main` 的 hooks/plugins/glm_5p2_profile/_repository_bounds 等都不在本文档范围内）。
>
> | 项 | 值 |
> | --- | --- |
> | 基准分支 | `main` (commit `970952550`) |
> | 目标分支 | `learn-backup-20260730-105659` (commit `f384d423c`) |
> | 对比命令 | `git diff main..learn-backup-20260730-105659 -- <file>` |
> | 查看目标文件 | `git show learn-backup-20260730-105659:<file>` |

## 关键背景（移植前必读）

1. **backup 没有 `zjcode/` 品牌隔离层包**。品牌定制是「直接硬改源码」方式：在 `deepagents_code/` 各源文件中把 `.deepagents` 路径、品牌常量直接改成 `.zjcode` / `zjcode`。移植时不要照搬任何 `zjcode/` 隔离层目录（本分支不存在）。
2. **backup 的 `model_config.py` 有完整的后端实现**：`save_custom_provider` / `fetch_provider_models` / `ModelDiscoveryError` 均已实现并接线（不是存根）。
3. **`mcp_trust.py`（配置指纹信任存储）在 backup 分支中实际是「已接线」的**（`main.py` / `mcp_tools.py` / `mcp_login_service.py` 都会调用它），并非死代码——详见第 6 章。`main` 分支没有此文件，`main` 用「allow/deny 名单策略」取代了指纹信任。
4. backup 基于较老的 `main`，许多文件的「整段差异」其实是 `main` 后来新增的功能被 diff 显示为「删除」。本文档只挑 backup **新增**的部分；凡 `main` 独有、backup 缺失的内容一律不写。

---

## 目录

1. [品牌定制（直接硬改源码方式）](#1-品牌定制直接硬改源码方式)
2. [图片粘贴与媒体模块](#2-图片粘贴与媒体模块)
3. [模型选择器与自定义供应商](#3-模型选择器与自定义供应商)
4. [每轮结束状态跟踪（turn_end_summary.py）](#4-每轮结束状态跟踪turn_end_summarypy)
5. [会话结束状态跟踪（session_end_summary.py）](#5-会话结束状态跟踪session_end_summarypy)
6. [MCP Trust 信任存储（mcp_trust.py）](#6-mcp-trust-信任存储mcp_trustpy)
7. [服务器启动改动](#7-服务器启动改动)
8. [非交互模式接入](#8-非交互模式接入)
9. [其他改动](#9-其他改动)
10. [移植检查清单](#10-移植检查清单)

---

## 1. 品牌定制（直接硬改源码方式）

> backup 不引入 `zjcode/` 隔离层包，而是在 `deepagents_code/` 源码内直接把 `~/.deepagents` -> `~/.zjcode`、`deepagents-code` -> `zjcode` 全量迁移。改动是「单点常量 + 散落路径字面量」混合，移植时需逐文件核对。

### 1.1 `_constants.py`（路径名单一来源）

两个 `Final[str]` 常量由 `.deepagents` 改为 `.zjcode`，作为全包路径名的「单一真相源」：

```python
CONFIG_DOTDIR: Final[str] = ".zjcode"
"""User-level config directory name (the `.zjcode` in `~/.zjcode/`).
Single source of truth for the private-brand directory name. `model_config`
builds the absolute `DEFAULT_CONFIG_DIR` from it ..."""

PROJECT_DOTDIR: Final[str] = ".zjcode"
"""Per-project config directory name (e.g. `<project-root>/.zjcode/`).
... both must move together when rebranding ..."""
```

- 模块其余常量（`DEFAULT_AGENT_NAME`、`FIREWORKS_*`、`MCP_REENABLED_PENDING_ERROR`、`SYSTEM_MESSAGE_PREFIX`）与品牌无关，保持不变。

### 1.2 `_version.py`（品牌常量集中点）

新增/改写一组品牌常量，所有需要品牌名的地方都从这里 import：

```python
__version__ = "0.0.8"  # x-release-please-version

DISTRIBUTION_NAME = "zjcode"
"""Distribution (wheel/PyPI) name ... (uv tool install <name>,
importlib.metadata.version(<name>), URL paths on PyPI, extras-preserving
upgrade commands) ..."""

BRAND_NAME = "zjcode"
"""Short user-visible command name shown in CLI help, splash, and errors.
Currently equal to DISTRIBUTION_NAME but kept separate ..."""

DOCS_URL = "https://docs.langchain.com/oss/python/deepagents/code"
"""URL for deepagents-code documentation (upstream - kept for now)."""

PYPI_URL = f"https://pypi.org/pypi/{DISTRIBUTION_NAME}/json"
"""PyPI JSON API endpoint for version checks."""

SDK_PYPI_URL = "https://pypi.org/pypi/deepagents/json"
"""PyPI JSON API endpoint for reading deepagents SDK release metadata.
The CLI only reads release-age metadata from this endpoint; it never
performs SDK update checks."""

CHANGELOG_URL = (
    "https://github.com/langchain-ai/deepagents/blob/main/libs/code/CHANGELOG.md"
)

USER_AGENT = f"{DISTRIBUTION_NAME}/{__version__} update-check"
"""User-Agent header sent with PyPI requests."""
```

> 注意：`PYPI_URL` 实际指向 `https://pypi.org/pypi/zjcode/json`（即公开 PyPI 的 `zjcode` 包）。

### 1.3 `_env_vars.py`

- `PYPI_URL` 常量的 docstring 改为「Override the JSON API URL used to check for `zjcode` updates. Defaults (in `_version.py`) to `https://pypi.org/pypi/zjcode/json`.」
- `SDK_PYPI_URL` 常量的 docstring 提到「Defaults (in `_version.py`) to the private static mirror.」
- 其余环境变量名（`DEEPAGENTS_CODE_*` 前缀）**保持不变**（这是 env 兼容性契约，不随品牌变）。
- 新增 `NO_MOUSE = "DEEPAGENTS_CODE_NO_MOUSE"` 常量（见 9.3）。

### 1.4 `config.py`（路径 + banner）

**路径迁移**（实际代码行，非注释）：

```python
# 全局 .env 路径
_GLOBAL_DOTENV_PATH = Path.home() / ".zjcode" / ".env"
# sentinel：
_GLOBAL_DOTENV_PATH = Path("/nonexistent/.zjcode/.env")

# ProjectContext 相关
def user_config_dir(self) -> Path:                       # ~/.zjcode
    return Path.home() / ".zjcode"
def get_agent_dir(self, agent_name: str) -> Path:        # ~/.zjcode/<name>
    return Path.home() / ".zjcode" / agent_name
def get_user_agents_md_path(...):                        # ~/.zjcode/<name>/AGENTS.md
    return Path.home() / ".zjcode" / agent_name / "AGENTS.md"
# project skills/agents 目录文档串：{project_root}/.zjcode/skills、.zjcode/agents
```

> 注：`config.py` 中仍残留约 19 处 `~/.deepagents` 字面量（多为 docstring/注释），属未完全清理的迁移痕迹；移植时以「实际路径行」为准迁移到 `.zjcode`，注释可一并清理。

**banner ASCII 艺术字**：`_UNICODE_BANNER` / `_ASCII_BANNER` 被替换为「私有品牌方块字」艺术字（区别于 `main` 的 "DEEP AGENTS" / "deep agents" 字样），末尾仍带 `v{__version__}`。`get_banner()` 逻辑不变（按 charset 选 Unicode/ASCII、`HIDE_SPLASH_VERSION` 去版本号、editable 加 `(local)`）：

```python
def get_banner() -> str:
    if _detect_charset_mode() == CharsetMode.ASCII:
        banner = _ASCII_BANNER
    else:
        banner = _UNICODE_BANNER
    if is_env_truthy(HIDE_SPLASH_VERSION):
        return banner.replace(f"v{__version__}", "")
    if _is_editable_install():
        banner = banner.replace(f"v{__version__}", f"v{__version__} (local)")
    return banner
```

> 移植提示：`_UNICODE_BANNER` / `_ASCII_BANNER` 的艺术字内容需整体从 backup 分支拷贝（`main` 的艺术字是 deep-agents 主题）。

### 1.5 `model_config.py`（`DEFAULT_CONFIG_DIR`）

```python
from deepagents_code import _constants
DEFAULT_CONFIG_DIR = Path.home() / _constants.CONFIG_DOTDIR
"""Directory for user-level Deep Agents configuration (`~/.zjcode`).
Renamed from `~/.deepagents` for the private-branded `zjcode` build so
config, sessions, tokens, and update caches are fully isolated ..."""

DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.toml"
DEFAULT_STATE_DIR = DEFAULT_CONFIG_DIR / ".state"
```

- `DEFAULT_CONFIG_DIR` 由硬编码 `~/.deepagents` 改为派生自 `_constants.CONFIG_DOTDIR`（`~/.zjcode`），实现「改一行即换品牌」。
- 后续 `turn_end_summary._log_path()`、`session_end_summary._log_path()` / `_summary_dir()`、`mcp_trust._default_store_path()` 都通过 `DEFAULT_CONFIG_DIR` / `DEFAULT_STATE_DIR` 间接落地到 `~/.zjcode`。

### 1.6 `update_check.py`

全部从 `_version` 导入品牌常量并用于升级命令与 PyPI 请求：

```python
from deepagents_code._version import (
    DISTRIBUTION_NAME, PYPI_URL, SDK_PYPI_URL, __version__, ...
)
FALLBACK_UPGRADE_COMMAND = f"uv tool install -U {DISTRIBUTION_NAME}"
"brew": f"brew upgrade {DISTRIBUTION_NAME}",
installed = _parse_version(pkg_version(DISTRIBUTION_NAME))
# PyPI 请求：
resp = requests.get(SDK_PYPI_URL, headers={"User-Agent": USER_AGENT}, timeout=3)
url = f"{PYPI_URL.removesuffix('/json')}/{version}/json"
# 升级 shim 目录/排除自身：
self.upgraded_bin_dir / DISTRIBUTION_NAME
for name in (DISTRIBUTION_NAME,):
requirement = f"{DISTRIBUTION_NAME}{extras_part}{version_suffix}"
```

- `main` 分支对应位置硬编码 `deepagents-code`；backup 全部替换为 `DISTRIBUTION_NAME`（= `zjcode`）。

### 1.7 `main.py`

- `--version` 文本首行用 `DISTRIBUTION_NAME`：`text = f"{DISTRIBUTION_NAME} {__version__}\ndeepagents (SDK) {sdk_version}"`（`_build_version_text`）。
- 进程重启命令用包名：`argv = [sys.executable, "-m", "deepagents_code", *sys.argv[1:]]`（包目录名 `deepagents_code` 不变）。
- 缺失依赖提示：`print(f"  uv tool install -U {DISTRIBUTION_NAME}")`。
- 旧安装检测路径：`return (_Path.home() / ".zjcode" / name).is_dir()`（`~/.deepagents/<name>` -> `~/.zjcode/<name>`）。
- 抑制警告提示串仍写 `~/.deepagents/config.toml`（注释残留，未清理）。
- `argparse` 的 `version=` 占位也用 `f"{DISTRIBUTION_NAME} {__version__}"`。

### 1.8 `managed_tools.py`

```python
BIN_DIR: Path = Path.home() / ".zjcode" / "bin"   # main: ".deepagents"
```

- `BIN_DIR` 由 `~/.deepagents/bin` 改为 `~/.zjcode/bin`（ripgrep 等托管工具的安装目录）。
- 注释中残留 `~/.deepagents/bin/`、`~/.deepagents` 字样未清理。

### 1.9 `project_utils.py`

- 通过 `from deepagents_code._constants import PROJECT_DOTDIR` 引用，项目级目录全部用常量：

```python
def project_skills_dir:   return self.project_root / PROJECT_DOTDIR / "skills"   # .zjcode/skills
def project_agents_dir:   return self.project_root / PROJECT_DOTDIR / "agents"   # .zjcode/agents
# AGENTS.md 查找顺序文档：project_root/.zjcode/AGENTS.md
return project_root_resolved / PROJECT_DOTDIR / "AGENTS.md"
```

- `main` 分支此处硬编码 `.deepagents`；backup 改用 `PROJECT_DOTDIR` 常量。

### 1.10 `skills/commands.py`、`subagents.py`

- `skills/commands.py`：注释/文档串把项目级 agent 目录写为 `.zjcode/agents/{agent_name}/AGENTS.md`。
- `subagents.py`：子代理 AGENTS.md 路径注释写为 `.zjcode/agents/{agent_name}/AGENTS.md`（`main` 为 `.deepagents/...`）。

### 1.11 `client/commands/mcp.py`

- **无品牌路径改动**（信任/路径逻辑不涉及 `.deepagents` 字面量）。
- 该文件相对 `main` 的差异是「信任机制文案」改动（把 `DANGEROUSLY_ENABLE_PROJECT_MCP_SERVERS` allowlist 文案改为「fingerprint trust store」文案），属于第 6 章 MCP Trust 的配套文案，不是品牌改动。

### 1.12 `theme.py` / `ui.py`（品牌微调）

- `theme.py`：仅一行——`_load_user_themes` 的默认 config 路径由 `Path.home() / ".deepagents" / "config.toml"` 改为 `".zjcode" / "config.toml"`。
- `ui.py`：`show_help()` 顶部品牌标题仍打印 `deepagents-code`（**未**改为 `zjcode`，属半成品迁移）；help 文本相对 `main` 的差异主要是 `main` 后来新增的命令（hooks/install/--recursion-limit 等）被移除，不属于 backup 新增功能。banner 颜色用 `theme.PRIMARY_DEV if _is_editable_install() else theme.PRIMARY`。

### 1.13 `pyproject.toml`（包名/入口/描述）

```toml
name = "zjcode"
description = "Private-branded terminal coding agent forked from deepagents-code."
# 复合 extras 自引用：
"zjcode[anthropic,baseten,bedrock,...,xai]"
"zjcode[agentcore,daytona,modal,runloop,vercel]"
# 控制台入口（包目录名 deepagents_code 不变）：
zjcode = "deepagents_code:cli_main"
```

### 1.14 辅助脚本（backup 独有）

- `libs/code/bump-version.py`（main 无）：单包版本号同步脚本，更新 `pyproject.toml` / `_version.py`（按 `# x-release-please-version` 定位）/ 根 `.release-please-manifest.json`，用于 `zjcode` 品牌发版。用法 `python bump-version.py <new-version>` / `--show` / `--dry-run`。
- `libs/code/dcode-dev.ps1`（main 无）：Windows 本地开发环境一键脚本（`uv venv` + 安装 `dcode`），`DCODE_DEV_VENV` 可覆盖 venv 目录。
- 根 `release-please-config.json` 的 `pull-request-header` 文案微调（release notes 预览说明），与品牌无强关联，移植可选。

> **品牌移植要点**：改 `_constants.CONFIG_DOTDIR/PROJECT_DOTDIR`、`_version.DISTRIBUTION_NAME/BRAND_NAME/PYPI_URL`、`model_config.DEFAULT_CONFIG_DIR`、`managed_tools.BIN_DIR`、`config.py` 路径行、`theme.py` config 路径、`pyproject.toml` 包名/入口、`update_check.py`/`main.py` 中 `DISTRIBUTION_NAME` 引用即可覆盖核心；散落 `~/.deepagents` 注释按需清理。

---

## 2. 图片粘贴与媒体模块

> 与 learn 分支一致。新增跨平台剪贴板图片读取/写入、Ctrl+V 直接粘贴、`/paste-image` `/copy-image` 命令、时间戳命名占位符。`main` 分支仅有 macOS 单平台 `get_clipboard_image`（无 Windows/Linux、无 `save_pasted_media`、无 `copy_image_to_clipboard`、保留 `is_media_path`）。

### 2.1 `media_utils.py`

**常量**

```python
IMAGE_EXTENSIONS: frozenset[str] = frozenset({
    ".png",".jpg",".jpeg",".gif",".bmp",".tiff",".tif",".webp",".ico"})
VIDEO_EXTENSIONS: frozenset[str] = frozenset({
    ".mp4",".mov",".avi",".webm",".m4v",".wmv"})
MAX_MEDIA_BYTES: int = 20 * 1024 * 1024
"""Maximum media file size (20 MB). Keeps base64 payload under ~27 MB."""
PASTED_MEDIA_DIR: pathlib.Path = pathlib.Path.home() / ".zjcode" / "pasted"
"""Images pasted into the TUI are decoded and written here (local archive).
The base64 payload is still what gets sent to the model; this local copy is
purely an archive of what was pasted."""
```

**`save_pasted_media(base64_data, stem, image_format) -> Path | None`**（新增）：把 base64 解码写入 `PASTED_MEDIA_DIR/<stem>.<ext>`（`jpeg`->`jpg`）。失败仅 `logger.warning` 并返回 `None`，绝不抛出（归档是便利而非硬要求）。`stem` 由调用方传入时间戳占位符 id（如 `img_20250115143022`），保证本地文件名与用户所见 token 一致。

**跨平台剪贴板写入**

```python
def _set_macos_clipboard_image(image_bytes: bytes) -> bool:
    """Write image bytes to macOS clipboard using osascript.
    临时文件 + `set the clipboard to (read (POSIX file ...) as «class PNGf»)`;
    失败/超时(5s)/OSError 均返回 False，finally 删临时文件。"""
```

**跨平台剪贴板读取**（`get_clipboard_image` 按平台分发）

```python
def get_clipboard_image() -> ImageData | None:
    """Attempt to read an image from the system clipboard.
    - macOS via `pngpaste` or `osascript`  (_get_macos_clipboard_image)
    - Windows via PowerShell                          (_get_windows_clipboard_image)
    - Linux via `wl-paste` (Wayland) or `xclip` (X11) (_get_linux_clipboard_image)
    """
    if sys.platform == "darwin":   return _get_macos_clipboard_image()
    if sys.platform == "win32":    return _get_windows_clipboard_image()
    if sys.platform.startswith("linux"): return _get_linux_clipboard_image()
    logger.warning("Clipboard image paste is not supported on %s ...", sys.platform)
    return None
```

- `_get_windows_clipboard_image()`（新增）：PowerShell `Get-Clipboard -Format Image` -> PNG bytes；**超大图片拒绝**（`len > MAX_MEDIA_BYTES` 时 `logger.warning` 返回 `None`）。
- `_get_linux_clipboard_image()`（新增）：依次尝试 `wl-paste -t image/png`（Wayland）与 `xclip -selection clipboard -t image/png -o`（X11）；每路都对 `result.stdout > MAX_MEDIA_BYTES` 做拒绝。
- `_get_macos_clipboard_image()` / `_get_clipboard_via_osascript()`（保留并增强）：先 `pngpaste`，回退 `osascript`；读取后对 `image_data > MAX_MEDIA_BYTES` 同样拒绝（避免 provider `BadRequestError` 与线程 checkpoint 污染）。

> **超大图片拒绝**：三个平台读取路径 + `get_image_from_path`/`get_video_from_path`/`get_media_from_path` 统一在尺寸超 `MAX_MEDIA_BYTES`（20MB）时 `logger.warning(... MB, max %d MB)` 并返回 `None`。

**`copy_image_to_clipboard(image_data: ImageData) -> bool`**（新增）：仅 macOS，base64 解码后调用 `_set_macos_clipboard_image`；非 macOS `logger.debug` 返回 False。

**删除 `is_media_path`**：`main` 的 `media_utils.is_media_path(path)` 在 backup 中被删除（路径媒体判断改由调用方直接用扩展名集合）。

> 数据类 `ImageData` / `VideoData`（含 `base64_data`、`format`、`placeholder`、`placeholder_span`、`to_message_content()`）与 `encode_to_base64` / `create_multimodal_content` / `strip_media_placeholders` / `_valid_placeholder_spans` 保留不变。

### 2.2 `input.py`（MediaTracker 重写 + 时间戳命名）

**占位符模式与命名**

```python
IMAGE_PLACEHOLDER_PATTERN = re.compile(r"\[img_(?P<id>[0-9]+(?:_[0-9]+)?)\]")
"""e.g. [img_20250115143022]; id 是本地时间戳 YYYYMMDDHHMMSS，
或（测试中）纯计数器，可带 _N 消歧同秒冲突。"""
VIDEO_PLACEHOLDER_PATTERN = re.compile(r"\[vid_(?P<id>[0-9]+(?:_[0-9]+)?)\]")
_MEDIA_PLACEHOLDER_PREFIX = {"image": "img_", "video": "vid_"}

def _now_timestamp() -> str:                       # YYYYMMDDHHMMSS
    return datetime.now().strftime("%Y%m%d%H%M%S")
def _generate_media_id(kind: MediaKind) -> str:    # noqa: ARG001 测试可替换
    return _now_timestamp()
```

**`MediaTracker` 重写**（删除计数器，改时间戳 + 同秒去重）

```python
class MediaTracker:
    def __init__(self) -> None:
        self.images: list[ImageData] = []
        self.videos: list[VideoData] = []
        # 占位符 ID 现由时间戳派生，不再有 per-tracker 计数器。

    def add_media(self, data, kind, *, existing_text="") -> str:
        prefix = _MEDIA_PLACEHOLDER_PREFIX[kind]
        base_id = _generate_media_id(kind)
        existing = self._all_placeholders() | self._draft_placeholders(existing_text)
        candidate = f"[{prefix}{base_id}]"
        suffix = 2
        while candidate in existing:              # 同秒冲突 -> _2/_3 后缀
            candidate = f"[{prefix}{base_id}_{suffix}]"
            suffix += 1
        data.placeholder = candidate
        (self.images if kind == "image" else self.videos).append(data)
        return candidate
    # add_image / add_video / get_images / get_videos / clear /
    # snapshot / restore / sync_to_text / remap_spans_to_text ... 均保留
```

- `_draft_placeholders(text)`（静态方法）：返回文本中字面出现的媒体占位符集合，用于防止把用户手敲的同名 token 绑到新媒体。
- `main` 用 `[image {next_image_id}]` / `[video {next_video_id}]` 计数器；backup 全改为时间戳命名并做同秒去重。

### 2.3 `tui/widgets/chat_input.py`（`_on_paste` 图片检测）

`_on_paste` 在原有「路径粘贴 / 大段折叠」逻辑之前，先做图片检测：

```python
async def _on_paste(self, event: events.Paste) -> None:
    """Handle paste events, detecting images, file paths, and large pastes."""
    # 1) 先查剪贴板是否有图（Ctrl+V 直接粘贴图片）
    image = await asyncio.to_thread(get_clipboard_image)
    if image is not None:
        event.prevent_default(); event.stop()
        existing_text = self.text
        placeholder = self._chat_input_owner._image_tracker.add_image(
            image, existing_text=existing_text)
        stem = placeholder.strip("[]")
        from deepagents_code.media_utils import save_pasted_media
        await asyncio.to_thread(save_pasted_media, image.base64_data, stem, image.format)
        self.insert(placeholder)            # 在光标处插入占位符
        return
    # 2) 原有文本/路径/折叠粘贴逻辑不变 ...
```

- `main` 的 `_on_paste` 无图片分支；backup 顶部 `from deepagents_code.media_utils import get_clipboard_image`。

### 2.4 `clipboard.py`（`copy_image_to_clipboard` + `copy_image_with_feedback`）

新增两个函数（`main` 无）：

```python
def copy_image_to_clipboard(image_data: "ImageData") -> tuple[bool, str | None]:
    """Copy an ImageData to the system clipboard. 仅 macOS（osascript 临时文件 +
    `set the clipboard to ... «class PNGf»`）。非 macOS 返回
    (False, "Image clipboard copy is currently only supported on macOS")。
    成功返回 (True, None)。"""

def copy_image_with_feedback(app: "App", image_data: "ImageData") -> bool:
    """Copy + toast 反馈。成功 app.notify("Image copied to clipboard")；
    失败 app.notify(f"Failed to copy image: {error}", severity="warning")。"""
```

- 模块原有 `copy_text_to_clipboard` / `copy_text_with_feedback` / `copy_selection_to_clipboard` / `_copy_osc52` 保留不变。

### 2.5 `command_registry.py`（`/paste-image`、`/copy-image` 注册）

在 `COMMANDS` 元组中新增两个 `SlashCommand`（`main` 无）：

```python
SlashCommand(
    name="/copy-image",
    description="Copy the most recently pasted image to the system clipboard",
    bypass_tier=BypassTier.SIDE_EFFECT_FREE,
    hidden_keywords="image clipboard",
),
SlashCommand(
    name="/paste-image",
    description="Paste an image from the system clipboard at cursor position",
    bypass_tier=BypassTier.QUEUED,
    hidden_keywords="image clipboard paste",
    aliases=("/paste-img",),
),
```

### 2.6 `app.py`（命令处理逻辑）

在 `DeepAgentsApp` 的命令分发处新增两个分支（`main` 无）。`self._image_tracker = MediaTracker()` 在 `__init__` 中初始化，并随 `ChatInput` 传入（`image_tracker=self._image_tracker`）。

```python
elif cmd == "/copy-image":
    await self._mount_message(UserMessage(command))
    if not self._image_tracker.images:
        await self._mount_message(AppMessage("No images have been pasted yet."))
        return
    from deepagents_code.clipboard import copy_image_to_clipboard
    latest_image = self._image_tracker.images[-1]      # 复制最近一张
    success, error = copy_image_to_clipboard(latest_image)
    if success:
        await self._mount_message(AppMessage("Copied latest image to clipboard."))
    else:
        await self._mount_message(AppMessage(
            f"Failed to copy image to clipboard: {error}" if error
            else "Failed to copy image to clipboard."))

elif cmd == "/paste-image":
    await self._mount_message(UserMessage(command))
    from deepagents_code.media_utils import get_clipboard_image, save_pasted_media
    import asyncio
    image = await asyncio.to_thread(get_clipboard_image)
    if image is None:
        await self._mount_message(AppMessage("No image found in clipboard."))
        return
    chat_input = self.query_one(ChatInput)
    existing_text = chat_input.value
    placeholder = self._image_tracker.add_image(image, existing_text=existing_text)
    stem = placeholder.strip("[]")
    await asyncio.to_thread(save_pasted_media, image.base64_data, stem, image.format)
    chat_input._text_area.insert(placeholder)
    await self._mount_message(AppMessage(f"Pasted image from clipboard: {placeholder}"))
```

- `app.py` 还通过 `self._image_tracker.snapshot()` / `restore(snapshot)` 在会话切换/恢复时保存与还原媒体状态。

---

## 3. 模型选择器与自定义供应商

> 和 learn 一致，但 `model_config` 后端**完整存在**（`save_custom_provider`/`fetch_provider_models`/`ModelDiscoveryError` 均已实现）。`main` 分支没有这三个后端函数，也没有 `CustomProviderModalScreen`/`DiscoverModelsScreen`。

### 3.1 `tui/widgets/model_selector.py`

**`ModelSelectorScreen` 新增绑定与动作**

```python
class ModelSelectorScreen(ModalScreen[tuple[str, str] | None]):
    BINDINGS: ClassVar[list[BindingType]] = [
        ...
        Binding("ctrl+a", "add_custom_provider", "Add custom provider",
                show=False, priority=True),   # 新增：Ctrl+A 打开添加供应商模态
        ...
    ]
    # _help_text() 里新增提示："Ctrl+A add provider"
    # compose() 里新增按钮 "Add Custom Provider (Ctrl+A)"，点击触发 action_add_custom_provider
```

```python
async def action_add_custom_provider(self) -> None:
    """Open the custom provider add modal."""
    def _on_provider_saved(result):
        if isinstance(result, tuple):
            success, provider_id, default_model = result
        else:
            success, provider_id, default_model = result, None, None
        if success and provider_id:
            # 直接切到新供应商并关全部模态。下发完整 provider:model spec，
            # 否则裸模型名会被 detect_provider 误判（如 gpt-* 误判为 openai），
            # 导致 server 用不上该供应商的 base_url/api_key。
            model = default_model or "custom_model"
            self._dismiss_with_result((f"{provider_id}:{model}", provider_id))
        elif success:
            # 旧回退路径：重载列表
            self._reload_task = asyncio.create_task(self._reload_model_list())
            ...
    self.app.push_screen(CustomProviderModalScreen(), _on_provider_saved)

async def _reload_model_list(self) -> None:
    """添加自定义供应商后重载模型列表（get_available_models 是文件 I/O，offload 到线程）。"""
    data = await asyncio.to_thread(self._load_model_data, ...)
    self._unfiltered_models = data.all_models
    self._default_spec = data.default_spec
    ...  # 重新 apply subset / filter / update display / footer
```

**`CustomProviderModalScreen`（约 396 行，2107-2502）**

```python
class CustomProviderModalScreen(ModalScreen[bool | tuple[bool, str, str | None]]):
    """Modal screen for adding/editing a custom OpenAI-compatible provider."""
    BINDINGS = [Binding("enter","submit","Save provider",priority=True),
                Binding("escape","cancel","Cancel",priority=True)]
    def __init__(self, provider_id: str | None = None, **kwargs):
        # provider_id 为 None=新增，非 None=编辑（ID 不可改）
        self.existing_providers: dict[str, dict] = {}
        self._discovered_models: list[str] = []   # Discover 选中的模型
    # compose() 表单字段：provider-id / display-name / base-url / api-key(password)
    #                   / default-model / discovered-status(hint) / error-message
    # 按钮：Cancel / Discover / Confirm
    # on_mount()：tomllib 读 config.toml 的 [models.providers] 预填编辑项
    # on_input()：输入 provider-id 命中已存在则自动填充并锁定
    async def action_submit(self) -> None:
        # 校验：ID 必填且仅 [a-z0-9-_]；display_name/base_url 必填；
        #       base_url 必须 http(s)://；default_model 长度<=255 且仅 [-_.:/] 字符集
        models_to_save = list(self._discovered_models) or None
        if models_to_save and default_model and default_model not in models_to_save:
            models_to_save.append(default_model)
        success = await asyncio.to_thread(save_custom_provider,
            provider_id=..., display_name=..., base_url=...,
            api_key=..., default_model=..., models=models_to_save)
        if success: self.dismiss((success, provider_id, default_model))
        else:       error_widget.update("Failed to save custom provider ...")
    async def action_discover(self) -> None:
        # 用 base_url(+可选 api_key) 调 fetch_provider_models；编辑态空 key 时
        # 回退 auth_store.get_stored_key(provider_id)。
        # 失败(ModelDiscoveryError/其它) 在 error_widget 显示 "Discover failed: ..."
        # 成功后 push DiscoverModelsScreen(discovered, preselected=...)，回调里
        # 把选中集写入 _discovered_models，并把首个选中设为 default_model。
    def _update_discovered_status(self): ...   # "N model(s) selected via Discover"
    def action_cancel(self): self.dismiss(False)
```

**`DiscoverModelsScreen`（约 146 行，2503-2648）**

```python
class DiscoverModelsScreen(ModalScreen[list[str] | None]):
    """Multi-select picker for models fetched from a provider's /models endpoint."""
    BINDINGS = [Binding("enter","submit","Save selection",priority=True),
                Binding("escape","cancel","Cancel",priority=True),
                Binding("ctrl+a","select_all","Select all"),
                Binding("ctrl+n","select_none","Select none")]
    def __init__(self, models: list[str], preselected: set[str] | None = None, **kwargs):
        self._models = list(models); self._preselected = set(preselected or ())
    # compose(): Static 标题("Discover Models - N found (space to toggle)") +
    #            SelectionList[(mid, mid, mid in preselected)] + 提示行 + Cancel/Save 按钮
    def on_mount(self): self.query_one(SelectionList).focus()
    def action_submit(self):                      # 返回选中 list[str]
        selected = list(self.query_one(SelectionList).selected)
        self.dismiss(selected)
    def action_cancel(self): self.dismiss(None)   # 不改变调用方状态
    def action_select_all(self): self.query_one(SelectionList).select_all()
    def action_select_none(self): self.query_one(SelectionList).deselect_all()
```

- `_MAX_MODEL_ID_LEN = 255`：default_model 长度上限常量。
- 顶部 `from deepagents_code.model_config import (... ModelDiscoveryError, ... fetch_provider_models)`。

### 3.2 `model_config.py`（自定义供应商后端，完整实现）

**`save_custom_provider(...)`（新增，完整实现）**

```python
def save_custom_provider(
    provider_id: str, display_name: str, base_url: str,
    models: list[str] | None = None,
    class_path: str = "langchain_openai:ChatOpenAI",
    api_key_env: str | None = None, api_key: str | None = None,
    default_model: str | None = None,
    max_input_tokens: int | None = None,
    config_path: Path | None = None,
) -> bool:
    """Save a custom OpenAI-compatible provider to config.toml.
    Returns True on success, False on I/O error."""
    if config_path is None: config_path = DEFAULT_CONFIG_PATH
    model_list = list(models or [])
    if default_model and default_model not in model_list: model_list.append(default_model)
    # api_key_env 默认推断：ChatOpenAI -> OPENAI_API_KEY；否则 <PROVIDER>_API_KEY
    if not api_key_env and class_path == "langchain_openai:ChatOpenAI":
        api_key_env = "OPENAI_API_KEY"
    elif api_key and not api_key_env:
        api_key_env = _provider_api_key_env(provider_id)
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = tomllib.load(config_path.open("rb")) if config_path.exists() else {}
        providers_section = data.setdefault("models", {}).setdefault("providers", {})
        provider_config: ProviderConfig = {
            "display_name": display_name, "base_url": base_url,
            "class_path": class_path, "models": model_list}
        if api_key_env: provider_config["api_key_env"] = api_key_env
        if default_model: provider_config["default_model"] = default_model
        if isinstance(max_input_tokens, int) and max_input_tokens > 0:
            provider_config["profile"] = {"max_input_tokens": max_input_tokens}
        providers_section[provider_id] = provider_config
        # 原子写：tempfile.mkstemp + tomli_w.dump + Path.replace，异常删临时文件
        fd, tmp = tempfile.mkstemp(dir=config_path.parent, suffix=".tmp")
        with os.fdopen(fd, "wb") as f: tomli_w.dump(data, f)
        Path(tmp).replace(config_path)
    except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError):
        logger.exception("Could not save custom provider %s", provider_id); return False
    if api_key:    # 存 key 到 auth_store
        try: auth_store.set_stored_key(provider_id, api_key, base_url=base_url)
        except RuntimeError: logger.exception(...); return False
    clear_caches()
    return True
```

> 辅助 `_provider_api_key_env(provider_id)`：`<PROVIDER_ID大写去连字符>_API_KEY`。

**`ModelDiscoveryError`（新增）**

```python
class ModelDiscoveryError(Exception):
    """Raised when discovering models from a provider's /models endpoint fails.
    The message is user-facing and safe to render verbatim in the TUI."""
```

**`fetch_provider_models(base_url, api_key=None, *, timeout=10.0, include_retiring=True) -> list[str]`（新增，完整实现）**

```python
def fetch_provider_models(base_url, api_key=None, *, timeout=10.0, include_retiring=True):
    """GET {base_url}/models，解析 OpenAI 格式，返回排序去重的 model id 列表。"""
    import httpx  # 局部导入，避免模块导入期拉 httpx
    if not base_url: raise ModelDiscoveryError("Base URL is required to discover models.")
    url = base_url.rstrip("/") + "/models"
    headers = {"Accept": "application/json"}
    if api_key: headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = httpx.get(url, headers=headers, timeout=timeout)
    except httpx.TimeoutException as exc:
        raise ModelDiscoveryError(f"Request to {url} timed out after {timeout:.0f}s.") from exc
    except httpx.HTTPError as exc:
        raise ModelDiscoveryError(f"Could not reach {url}: {exc}") from exc
    # 状态码错误处理（消息可直接渲染给用户）：
    if response.status_code == 401:
        raise ModelDiscoveryError("Authentication failed (HTTP 401). Check the API key.")
    if response.status_code == 403:
        raise ModelDiscoveryError("Forbidden (HTTP 403). The API key may lack permission.")
    if response.status_code == 404:
        raise ModelDiscoveryError(f"{url} returned 404. This provider may not expose /models.")
    if response.status_code >= 400:
        raise ModelDiscoveryError(f"HTTP {response.status_code} from {url}: {response.text[:200]}")
    payload = response.json()   # 非 JSON -> ModelDiscoveryError
    # OpenAI 形状：{"data": [{"id": ...}]}；部分供应商返回裸 list。
    data = payload.get("data", payload.get("models", [])) if isinstance(payload, dict) else payload
    if not isinstance(data, list): raise ModelDiscoveryError("Unexpected /models response shape ...")
    ids: set[str] = set()
    for entry in data:
        if isinstance(entry, str): ids.add(entry); continue
        if not isinstance(entry, dict): continue
        model_id = entry.get("id") or entry.get("name") or entry.get("model")
        if not isinstance(model_id, str) or not model_id: continue
        status = entry.get("status")          # Volcengine Ark 生命周期字段
        if isinstance(status, str):
            if status == "Shutdown": continue            # 始终过滤已下线
            if not include_retiring and status == "Retiring": continue
        ids.add(model_id)
    return sorted(ids)
```

> 过滤 `Shutdown`（始终）与 `Retiring`（`include_retiring=False` 时）是 Volcengine Ark 扩展。

### 3.3 `config.py`（默认模型 spec 辅助函数）

新增三个辅助函数，并把 `_get_default_model_spec` 的检查顺序扩展为「含供应商级 default_model」（`main` 仅有 4 步：default / recent / openai / anthropic / google_genai）：

```python
def _format_provider_default_model_spec(provider: str, model: object) -> str | None:
    """把供应商配置里的 default_model 规整成 provider:model spec。
    已经是合法 ModelSpec 则原样返回；否则拼 `provider:stripped`。"""
    from deepagents_code.model_config import ModelSpec
    if not isinstance(model, str): return None
    stripped = model.strip()
    if not stripped: return None
    if ModelSpec.try_parse(stripped): return stripped
    return f"{provider}:{stripped}"

def _get_configured_provider_default_model(config: ModelConfig) -> str | None:
    """遍历已启用的自定义供应商，返回第一个 auth 可用(default_model) 的 spec。"""
    from deepagents_code.model_config import get_provider_auth_status
    for provider, provider_config in config.providers.items():
        if not config.is_provider_enabled(provider): continue
        spec = _format_provider_default_model_spec(provider, provider_config.get("default_model"))
        if spec is None: continue
        if get_provider_auth_status(provider).as_legacy_bool() is not False:
            return spec
    return None

def _model_spec_auth_is_usable(model_spec: str) -> bool:
    """recent_model 的 spec 若指向某供应商，校验该供应商 auth 是否可用。
    无法解析（裸模型名）则返回 True（交由 detect_provider 处理）。"""
    from deepagents_code.model_config import ModelSpec, get_provider_auth_status
    parsed = ModelSpec.try_parse(model_spec)
    if not parsed: return True
    return get_provider_auth_status(parsed.provider).as_legacy_bool() is not False

def _get_default_model_spec() -> str:
    """检查顺序：
    1. [models].default          用户显式偏好
    2. 供应商级 default_model     _get_configured_provider_default_model（新增步）
    3. [models].recent           最近一次 /model（经 _model_spec_auth_is_usable 过滤，新增）
    4. 凭据自动探测               openai:gpt-5.5 / anthropic:claude-opus-4-7 /
                                google_genai:gemini-3.1-pro-preview
    无凭据则 raise NoCredentialsConfiguredError。"""
    config = ModelConfig.load()
    if config.default_model: return config.default_model
    provider_default = _get_configured_provider_default_model(config)
    if provider_default: return provider_default
    if config.recent_model and _model_spec_auth_is_usable(config.recent_model):
        return config.recent_model
    if get_provider_auth_status("openai").as_legacy_bool() is True:     return "openai:gpt-5.5"
    if get_provider_auth_status("anthropic").as_legacy_bool() is True:  return "anthropic:claude-opus-4-7"
    if get_provider_auth_status("google_genai").as_legacy_bool() is True: return "google_genai:gemini-3.1-pro-preview"
    raise NoCredentialsConfiguredError("No credentials configured. Please set one of: ...")
```

- `main` 的 `_get_default_model_spec` 没有第 2 步（供应商级 default_model），且第 3 步直接 `if config.recent_model: return`（不校验 auth）。backup 新增这两个能力，使自定义供应商的 default_model 能成为启动默认。

---

## 4. 每轮结束状态跟踪（turn_end_summary.py）

> 新增模块，共 522 行。记录单个 agent turn 为什么结束、运行多久，并在 turn 结束后**必定**输出一个紧凑标记（无论正常回复/流截断/工具错误/Ctrl-C/超时）。零配置、永不开关、永不抛出、单 turn 幂等。`main` 无此文件。

### 4.1 原因常量与优先级

```python
REASON_COMPLETED       = "completed"
REASON_LENGTH_CAPPED   = "length_capped"
REASON_CONTENT_FILTERED= "content_filtered"
REASON_TOOL_REJECTED   = "tool_rejected"
REASON_USER_INTERRUPTED= "user_interrupted"
REASON_STREAM_ERROR    = "stream_error"
REASON_PROVIDER_ERROR  = "provider_error"
REASON_TIMEOUT         = "timeout"
REASON_RECURSION_LIMIT = "recursion_limit"
REASON_UNKNOWN_TRUNCATION = "unknown_truncation"   # 默认/最不具信息量
ALL_REASONS: frozenset[str] = frozenset({...10 项...})

_REASON_PRIORITY: dict[str, int] = {
    REASON_UNKNOWN_TRUNCATION: 0,   # 任何显式信号都能升级过它
    REASON_COMPLETED: 1,
    REASON_LENGTH_CAPPED: 2, REASON_CONTENT_FILTERED: 2,
    REASON_TOOL_REJECTED: 3, REASON_TIMEOUT: 3,
    REASON_PROVIDER_ERROR: 3, REASON_RECURSION_LIMIT: 3,
    REASON_STREAM_ERROR: 4,
    REASON_USER_INTERRUPTED: 5,      # 最高，用户中断永远胜出
}
```

- 配套 `_REASON_EMOJI` / `_REASON_LABEL`（中文标签，如 `正常结束`/`输出被截断(max_tokens)`/`用户中断`/`疑似截断(无 finish_reason)`）。

### 4.2 finish_reason 映射

```python
_FINISH_REASON_MAP = {
    "stop": REASON_COMPLETED, "end_turn": REASON_COMPLETED,
    "complete": REASON_COMPLETED, "finished": REASON_COMPLETED, "eos": REASON_COMPLETED,
    "length": REASON_LENGTH_CAPPED, "max_tokens": REASON_LENGTH_CAPPED,
    "model_length": REASON_LENGTH_CAPPED, "model_max_tokens": REASON_LENGTH_CAPPED,
    "output_length": REASON_LENGTH_CAPPED, "max_output_tokens": REASON_LENGTH_CAPPED,
    "content_filter": REASON_CONTENT_FILTERED,
    "safety": REASON_CONTENT_FILTERED, "blocked": REASON_CONTENT_FILTERED,
}
_TOOL_CALL_FINISH_REASONS = frozenset({"tool_calls", "tool_use", "function_call"})
# tool_calls 等返回 None（工具交接，不算 turn 结束）
```

### 4.3 状态与公共 API

```python
@dataclass
class _TurnState:                 # 线程内可变状态，_state_lock(RLock) 保护
    start_monotonic / thread_id / turn_id / turn_number
    reason = REASON_UNKNOWN_TRUNCATION / detail / finish_reason_raw
    finalized = False / started = False
_current: _TurnState = _TurnState()

@dataclass
class TurnEndRecord:              # finalize_turn 返回的不可变快照
    reason / detail / duration_seconds / duration_pretty
    thread_id / turn_id / turn_number / finish_reason_raw
    ended_at = field(default_factory=time.time)

def mark_turn_start(*, thread_id="", turn_id=None, turn_number=None) -> None:
    """重置 per-turn 状态并记录开始时间（time.monotonic）。"""
def classify_finish_reason(finish_reason) -> str | None:
    """raw finish_reason -> 归一化 reason；tool_call 或未知返回 None。"""
def observe_finish_reason(finish_reason) -> None:
    """更新 finish_reason_raw；若可分类则 mark_turn_reason 升级。"""
def mark_turn_reason(reason, detail="") -> None:
    """仅当 reason 优先级 >= 当前才升级（高优先级覆盖低优先级）。"""
def classify_exception(exc: BaseException) -> tuple[str, str]:
    """按类名+消息分类异常：
       KeyboardInterrupt/CancelledError -> (USER_INTERRUPTED, name)
       *timeout* -> TIMEOUT；*graphrecursion*/*recursionerror* -> RECURSION_LIMIT
       *httpstatus*/*clientresponse*/connect/transport/network -> PROVIDER_ERROR
       其余 -> STREAM_ERROR。detail 截断到 500 字符。"""
def is_active() -> bool: ...        # started 且未 finalized
```

### 4.4 finalize_turn（3 个输出 sink）

```python
def finalize_turn() -> TurnEndRecord | None:
    """Emit sinks and return the record. 幂等：未 start 或已 finalize 返回 None。"""
    with _state_lock:
        if not _current.started or _current.finalized: return None
        _current.finalized = True
        ...  # 快照各字段
    duration = time.monotonic() - started if started is not None else 0.0
    record = TurnEndRecord(...)
    # Sink 1（TUI/console）：由调用方 mount render_marker_text(record)（headless 打 stderr）
    # Sink 2（JSONL 审计日志）：_append_jsonl(record)   始终尝试
    # Sink 3（doc/ 自动追加）：_append_to_doc(record)   doc/ 不存在则静默 no-op
    return record
```

### 4.5 渲染

```python
def render_marker_text(record) -> str:
    """单行人类可读标记：
       '⏹ 结束状态：<emoji> <label>[ (detail)] | ⏱ 总耗时：<pretty> | 🕒 结束时间：<ts>'
       结束时间用 datetime.fromtimestamp(ended_at).strftime('%Y-%m-%d %H:%M:%S')。"""
def render_marker_line(record) -> str:
    """Markdown 引用块形式：'> ' + render_marker_text，用于追加到 doc。"""
```

> 该单行标记在视觉上充当「线程内每轮的分隔符」（每轮回复后挂一条状态行）。

### 4.6 Sink 2：JSONL

```python
def _log_path() -> Path:
    """~/.zjcode/turn_end_log.jsonl（DEFAULT_CONFIG_DIR.mkdir 兜底）。"""
def _append_jsonl(record):
    payload = {ts, thread_id, turn_id, turn_number, pid, reason,
               reason_detail, finish_reason_raw, duration_seconds, duration_pretty}
    with _log_path().open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")  # POSIX 原子追加
```

### 4.7 Sink 3：doc/ 自动追加（项目根目录检测）

```python
_PROJECT_ROOT_MARKERS = ("AGENTS.md", ".git", "pyproject.toml",
                         "package.json", "Cargo.toml", "go.mod")

def _find_project_root(start: Path | None = None) -> Path | None:
    """从 start(默认 cwd) 向上走，命中任一 marker 即定为根；最多 40 层。
       resolve() 失败返回 None。"""
def _pick_today_doc(doc_dir: Path) -> Path | None:
    """在 doc/ 下挑名字以今日 'YYYY-MM-DD-' 开头、后缀 .md 的文件中 mtime 最大者；
       不存在或目录不可读返回 None。"""
def _append_to_doc(record):
    """root=_find_project_root(); 若 root 为 None 则静默返回。
       doc_dir = root/'doc'; target=_pick_today_doc(doc_dir); 无则返回。
       行前补换行（读最后一字节判断），追加 render_marker_line(record)+'\n'。
       全程 best-effort，失败 logger.debug。"""
```

- 测试辅助：`_reset_for_tests()` 重置模块状态；`_snapshot_for_tests()` 返回当前 `_TurnState` 浅拷贝。

### 4.8 TUI 接入（`tui/textual_adapter.py`）

在 `_run_agent_loop`（主 agent 循环）接入：

```python
# 回合开始：每个 prompt 都 mark_turn_start
from deepagents_code import turn_end_summary
turn_end_summary.mark_turn_start(thread_id=thread_id or "", turn_id=turn_id or "",
                                 turn_number=turn_number)
# 流中观察 finish_reason（主 agent 才记，避免子代理噪声）：
if is_main_agent:
    _fr = _meta.get("finish_reason") or _meta.get("stop_reason")
    if _fr: turn_end_summary.observe_finish_reason(_fr)
# except (CancelledError, KeyboardInterrupt)：先标记 USER_INTERRUPTED，再 cleanup
turn_end_summary.mark_turn_reason(turn_end_summary.REASON_USER_INTERRUPTED,
                                  type(_interrupt_exc).__name__)
# finally（所有退出路径）：
_exc = sys.exc_info()[1]
if _exc is not None and not isinstance(_exc, (asyncio.CancelledError, KeyboardInterrupt)):
    _reason, _detail = turn_end_summary.classify_exception(_exc)
    turn_end_summary.mark_turn_reason(_reason, _detail)
_record = turn_end_summary.finalize_turn()
if _record is not None:
    await adapter._mount_message(AppMessage(turn_end_summary.render_marker_text(_record)))
```

- finalize 幂等，嵌套 finally 双调用安全；mount 失败仅 `logger.debug`，绝不遮蔽传播中的异常。

---

## 5. 会话结束状态跟踪（session_end_summary.py）

> 新增模块，共 329 行。通过 `atexit` + `sys.excepthook` 钩子，在进程退出时记录会话为什么结束、运行多久，并输出到三个 sink。自包含、幂等、永不抛出、导入期零重依赖。`main` 无此文件。

### 5.1 原因常量与优先级

```python
REASON_COMPLETED  = "completed"    # 正常退出（/exit、Ctrl-D、脚本结束、sys.exit(0)）
REASON_INTERRUPTED= "interrupted"  # 用户/OS 终止（Ctrl-C、SIGTERM、SIGHUP、SIGQUIT）
REASON_ERROR      = "error"        # 未处理异常上抛
# 升级顺序：高优先级覆盖。先到的 error 不会被后续 atexit 的 completed 覆盖。
_REASON_PRIORITY = {REASON_COMPLETED: 0, REASON_INTERRUPTED: 1, REASON_ERROR: 2}
_SIGNAL_NAMES = {"SIGINT":"SIGINT","SIGTERM":"SIGTERM","SIGHUP":"SIGHUP","SIGQUIT":"SIGQUIT"}
```

### 5.2 安装与钩子

```python
def install(*, thread_id: str = "") -> None:
    """注册 atexit(_finalize) + 链式 excepthook；记录 start_monotonic。
       可重复调用（幂等）；非空 thread_id 填补空槽。"""
def _install_excepthook() -> None:
    """在原 excepthook 外包一层分类：
       KeyboardInterrupt -> mark_reason(INTERRUPTED, 'KeyboardInterrupt')
       SystemExit        -> 不升级（正常退出路径）
       其余              -> mark_reason(ERROR, f'{type}: {exc}'[:500])"""
def set_thread_id(thread_id: str) -> None:
    """client 学到真实 thread id 后回填（空串忽略）。"""
def mark_reason(reason, detail="") -> None:
    """仅当 reason 优先级 >= 当前才升级。"""
def mark_signal(signum: int) -> None:
    """main.py 信号处理里在 raise SystemExit 前调用（SystemExit 不走 excepthook，
       这是唯一能把信号归因到 reason 的机会）。name=_SIGNAL_NAMES.get(signum,...)。"""
```

### 5.3 三个 sink

```python
def _summary_dir() -> Path:   # ~/.zjcode/.state/session_end/  (DEFAULT_STATE_DIR)
def _log_path() -> Path:      # ~/.zjcode/session_end_log.jsonl (DEFAULT_CONFIG_DIR)

def _print_stderr_panel(reason_line, duration_pretty, thread_id) -> None:
    """UI 拆解后打到 stderr 的纯文本面板（atexit 在 alt-screen 退出后跑，不被吞）：
       ─────────── Session ended ───────────
       Reason:   <reason_line>
       Duration: <duration_pretty>
       Thread:   <thread_id>
       Log:      ~/.deepagents/session_end_log.jsonl
       ──────────────────────────────────────"""

def _finalize() -> None:
    """幂等。计算 duration；依次：
       1. _print_stderr_panel(...)
       2. _summary_dir()/<safe_thread_id>.txt 写 'Session ended\nReason...\nDuration...\nThread...\nPID...'
          (_sanitize_filename 把线程 id 中的路径分隔符等替换为 _，空则 'unknown')
       3. _log_path() 追加 JSON 行 {ts, thread_id, pid, reason, reason_detail,
                                   duration_seconds, duration_pretty}"""
```

- `_format_duration` 懒加载 `formatting.format_duration`，失败本地兜底（`XhMMmSSs`/`MmSSs`/`Ss`）。
- 测试辅助 `_reset_for_tests()`：`atexit.unregister(_finalize)` 并重置全部状态。

---

## 6. MCP Trust 信任存储（mcp_trust.py）

> 新增模块，共 207 行。基于**配置指纹**的项目级 MCP 信任存储：配置内容变化则需重新批准。`main` 分支没有此文件--`main` 改用「allow/deny 名单策略」（`load_mcp_server_trust_lists`）取代了指纹信任。
>
> **接线状态说明**：尽管部分文档曾把 `mcp_trust.py` 描述为「未接线的死代码」，但在 backup 分支中它**实际已被接线**（`main.py:_check_mcp_project_trust`、`mcp_tools.py`、`mcp_login_service.py` 都调用其指纹/信任函数，见下）。移植到 `main` 时需注意 `main` 已有 `load_mcp_server_trust_lists` 名单机制，二者**互斥**，需选择其一或协调共存。

### 6.1 存储路径与版本

```python
_STORAGE_VERSION = 1
def _default_store_path() -> Path:
    """~/.zjcode/.state/mcp_trust.json（DEFAULT_STATE_DIR）。
       运行时解析（非导入期），测试可 monkeypatch DEFAULT_STATE_DIR 重定向。"""
```

### 6.2 指纹与信任查询

```python
def compute_config_fingerprint(config_paths: list[Path]) -> str:
    """对排序后的配置文件内容做 SHA-256，返回 'sha256:<hex>'。
       读不到的文件 logger.warning 但不中断（跳过）。"""

def is_project_mcp_trusted(project_root: str, fingerprint: str, *, store_path=None) -> bool:
    """store['projects'][project_root] == fingerprint 则可信。"""

def trust_project_mcp(project_root: str, fingerprint: str, *, store_path=None) -> bool:
    """持久化信任：data['projects'][project_root]=fingerprint; data['version']=1; _save_store。"""

def revoke_project_mcp_trust(project_root: str, *, store_path=None) -> bool:
    """移除信任（不存在也算成功）。"""
```

### 6.3 存储读写（原子写 + 容错）

```python
def _load_store(store_path) -> dict:
    """读 JSON；缺失/不可读/损坏一律降级为 {}（nothing trusted）。
       损坏时 logger.warning 留痕（解释后续为何重弹批准）。"""
def _save_store(data, store_path) -> bool:
    """原子写：mkdir + tempfile.mkstemp + json.dump(indent=2) + Path.replace；
       异常删临时文件并 logger.exception，返回 False。"""
def _read_projects(store_path) -> dict:
    """store['projects']（非 dict 则 {}）。"""
```

### 6.4 接线点（backup 分支实际调用）

- **`main.py:_check_mcp_project_trust(trust_flag=...)`**：TUI 启动前调用。`--trust-project-mcp` 直接返回 True；否则 `compute_config_fingerprint(project_configs)` + `is_project_mcp_trusted(project_root, fingerprint)`，可信则放行，不可信则弹交互批准（批准后调 `trust_project_mcp` 持久化）。`DEEPAGENTS_CODE_DEBUG_MCP_PROJECT_TRUST` 调试态下跑完提示即 `sys.exit(0)`。
- **`mcp_tools.py`**：加载项目级 `.mcp.json` 时，`trust_project_mcp` 显式 True/False 优先；否则 `compute_config_fingerprint` + `is_project_mcp_trusted` 决定 `project_trusted`，再叠加 `load_mcp_server_trust_lists` 的 allow/deny 名单。
- **`mcp_login_service.py:resolve_mcp_config`**：`/mcp login` 解析配置时，项目级配置仅在指纹匹配时纳入，否则记为 `untrusted`。

> 配套：`client/commands/mcp.py` 文案改为「fingerprint trust store」表述；`_server_config.py` / `main.py` / `non_interactive.py` / `server_manager.py` 透传 `trust_project_mcp: bool | None` 标志（`--trust-project-mcp` / `TRUST_PROJECT_MCP` env）。

---

## 7. 服务器启动改动

### 7.1 `client/launch/server.py`

新增 `--allow-blocking` 标志 + `LANGGRAPH_ALLOW_BLOCKING` 环境变量（`main` 无）。目的：允许 agent graph 工厂在 dev server 事件循环中做同步文件 I/O（dotenv 发现、项目根检测、`Path.resolve()`/`os.getcwd()`），否则 `langgraph dev` 的 blockbuster 会抛 `BlockingError` 致 graph 就绪检查失败。

```python
def _build_server_cmd(...) -> list[str]:
    return [
        sys.executable, "-m", "langgraph_cli", "dev",
        "--host", host, "--port", str(port),
        "--no-browser", "--no-reload",
        # 关键：langgraph dev 会用自己的 --allow-blocking 覆盖 LANGGRAPH_ALLOW_BLOCKING
        # （默认 false），所以仅设 env 不够，必须同时传这个 flag。
        "--allow-blocking",
        "--config", str(config_path),
    ]

def _build_server_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["LANGGRAPH_AUTH_TYPE"] = "noop"
    # 完整性兜底：langgraph dev 仍会以 --allow-blocking 覆盖它，所以两者都要设。
    env["LANGGRAPH_ALLOW_BLOCKING"] = "true"
    ...
```

> 注意：`_server_config.py` 不涉及该变量；它只存在于 `server.py` 的命令构造与环境构造中。

---

## 8. 非交互模式接入

### 8.1 `client/non_interactive.py`

`turn_end_summary` 与 `session_end_summary` 在 headless 单任务流程接入（`main` 无）：

**`turn_end_summary`**

```python
# 回合开始（_run_non_interactive 主循环）：
from deepagents_code import turn_end_summary
turn_end_summary.mark_turn_start(thread_id=thread_id if isinstance(thread_id, str) else "")
# 每条 AIMessage 的 response_metadata finish_reason 观察（让标记反映 length/content_filter 等）：
_fr = _resp_meta.get("finish_reason") or _resp_meta.get("stop_reason")
if _fr: turn_end_summary.observe_finish_reason(_fr)
# finally（所有退出路径）：
_exc = sys.exc_info()[1]
if isinstance(_exc, (asyncio.CancelledError, KeyboardInterrupt)):
    turn_end_summary.mark_turn_reason(turn_end_summary.REASON_USER_INTERRUPTED, type(_exc).__name__)
elif _exc is not None:
    _reason, _detail = turn_end_summary.classify_exception(_exc)
    turn_end_summary.mark_turn_reason(_reason, _detail)
_record = turn_end_summary.finalize_turn()
if _record is not None and not quiet:
    console.print(turn_end_summary.render_marker_text(_record))   # headless 打 console
```

**`session_end_summary`**

```python
# 任务完成后回填 thread id 给 atexit 驱动的退出面板：
try:
    from deepagents_code import session_end_summary
    session_end_summary.set_thread_id(thread_id)
except Exception:
    logger.debug("session_end_summary.set_thread_id failed", exc_info=True)
```

- `session_end_summary.install()` 在 `main.py` 启动早期调用（见 9.1），非交互模式复用同一 atexit 钩子。

---

## 9. 其他改动

### 9.1 `main.py`（session_end_summary 安装 + 信号归因）

```python
# 启动早期（在 check_cli_dependencies 之前）：
try:
    from deepagents_code import session_end_summary
    session_end_summary.install()           # 注册 atexit + excepthook
except Exception:
    logger.debug("Failed to install session_end_summary", exc_info=True)

# 终止信号处理（POSIX SIGHUP/SIGTERM/SIGQUIT），raise SystemExit(128+signum) 前：
try:
    from deepagents_code import session_end_summary
    session_end_summary.mark_signal(signum)  # SystemExit 不走 excepthook，这是唯一机会
except Exception:
    pass
raise SystemExit(128 + signum)
```

### 9.2 `todo_list_prompt.md`（新增）

`main` 无此文件，backup 新增 12 行 Todo 管理提示（供 `write_todos` 工具的系统提示拼装）：

```markdown
### Todo List Management

When using the write_todos tool:

1. Use todos for any task with 2+ steps - they give the user visibility
2. Mark tasks `in_progress` before starting, `completed` immediately after
3. Don't batch completions - mark each item done as you finish it
4. If a task reveals sub-tasks, add them right away
5. For simple 1-step tasks, just do them directly
{todo_guidance}

The todo list is a planning tool - use it judiciously to avoid overwhelming the user with excessive task tracking.
```

### 9.3 `--no-mouse` flag（`main.py` + `_env_vars.py`，backup 独有）

为 web 终端（1Panel、ttyd、wetty）泄漏鼠标上报序列（如 `[<35;36;33M...`）导致输入乱码而加的开关。

```python
# _env_vars.py
NO_MOUSE = "DEEPAGENTS_CODE_NO_MOUSE"
"""Disable Textual mouse tracking. ... Equivalent to passing --no-mouse."""

# main.py argparse
parser.add_argument("--no-mouse", action="store_true",
    help="Disable Textual mouse tracking. Use for web terminals (1Panel, "
         "ttyd, wetty) that leak garbled mouse-report sequences into input.")

def _resolve_no_mouse(args) -> bool:
    """True when --no-mouse 或 DEEPAGENTS_CODE_NO_MOUSE 为真。"""
    from deepagents_code._env_vars import NO_MOUSE, is_env_truthy
    if getattr(args, "no_mouse", False): return True
    return is_env_truthy(NO_MOUSE)

# 启动 TUI：
mouse=not _resolve_no_mouse(args)
```

### 9.4 `theme.py` / `ui.py` 品牌微调

- `theme.py`：`_load_user_themes` 默认 config 路径 `.deepagents` -> `.zjcode`（见 1.12）。
- `ui.py`：`show_help()` 标题仍 `deepagents-code`（半成品迁移）；相对 `main` 的 help 文本差异多为 `main` 后续新增命令被移除，非 backup 新增。

### 9.5 `turn_end_summary` 的 `textual_adapter.py` 接入

见 4.8（每轮回合标记挂载、finish_reason 观察、中断/异常分类、finally finalize）。

---

## 10. 移植检查清单

> 按阶段排列。建议从 `main` 拉新分支后按序勾选。每项可用 `git show learn-backup-20260730-105659:<file>` 取对照源码。

### 阶段 A：品牌定制（直接硬改源码，无隔离层）

- [ ] `_constants.py`：`CONFIG_DOTDIR` / `PROJECT_DOTDIR` 改 `.zjcode`
- [ ] `_version.py`：`DISTRIBUTION_NAME` / `BRAND_NAME` / `PYPI_URL` / `USER_AGENT` / `SDK_PYPI_URL` / `CHANGELOG_URL` / `DOCS_URL`
- [ ] `_env_vars.py`：`PYPI_URL` / `SDK_PYPI_URL` docstring 改 `zjcode`；新增 `NO_MOUSE`
- [ ] `model_config.py`：`DEFAULT_CONFIG_DIR = Path.home() / _constants.CONFIG_DOTDIR`
- [ ] `config.py`：`_GLOBAL_DOTENV_PATH` / `user_config_dir` / `get_agent_dir` / `get_user_agents_md_path` 路径改 `.zjcode`；banner 艺术字替换
- [ ] `managed_tools.py`：`BIN_DIR` 改 `~/.zjcode/bin`
- [ ] `project_utils.py`：项目级目录用 `PROJECT_DOTDIR` 常量
- [ ] `skills/commands.py` / `subagents.py`：`.zjcode/agents/...` 文档串
- [ ] `update_check.py`：全部引用 `DISTRIBUTION_NAME` / `PYPI_URL` / `SDK_PYPI_URL` / `USER_AGENT`
- [ ] `main.py`：`_build_version_text` 首行 / 缺失依赖提示 / 旧安装检测路径用 `DISTRIBUTION_NAME`、`.zjcode`
- [ ] `theme.py`：`_load_user_themes` config 路径改 `.zjcode`
- [ ] `pyproject.toml`：`name="zjcode"` / `description` / extras 自引用 / 入口 `zjcode = "deepagents_code:cli_main"`
- [ ] `bump-version.py` / `dcode-dev.ps1`（可选辅助脚本）
- [ ] 散落 `~/.deepagents` 注释清理（可选）

### 阶段 B：图片粘贴与媒体模块

- [ ] `media_utils.py`：`PASTED_MEDIA_DIR`（`~/.zjcode/pasted`）、`save_pasted_media`、`_set_macos_clipboard_image`、`_get_windows_clipboard_image`、`_get_linux_clipboard_image`、`copy_image_to_clipboard`；`get_clipboard_image` 改三平台分发；删 `is_media_path`；超大图片（>20MB）拒绝
- [ ] `input.py`：`_now_timestamp` / `_generate_media_id`；`MediaTracker` 重写（时间戳命名 + 同秒去重 `_N`）；`IMAGE/VIDEO_PLACEHOLDER_PATTERN` 支持 `YYYYMMDDHHMMSS[_N]`
- [ ] `chat_input.py`：`_on_paste` 开头 `get_clipboard_image` 检测 + `add_image` + `save_pasted_media` + 插占位符
- [ ] `clipboard.py`：`copy_image_to_clipboard`（macOS osascript）+ `copy_image_with_feedback`（toast）
- [ ] `command_registry.py`：`/paste-image`（alias `/paste-img`）、`/copy-image` 命令注册
- [ ] `app.py`：`/copy-image` / `/paste-image` 命令处理；`self._image_tracker = MediaTracker()`

### 阶段 C：模型选择器与自定义供应商

- [ ] `model_config.py`：`save_custom_provider`（tomllib 读写 + 原子写 + auth_store 存 key + clear_caches）
- [ ] `model_config.py`：`ModelDiscoveryError` + `fetch_provider_models`（httpx.get /models，OpenAI 解析，过滤 Shutdown/Retiring，401/403/404/4xx 处理）
- [ ] `config.py`：`_format_provider_default_model_spec` / `_get_configured_provider_default_model` / `_model_spec_auth_is_usable`
- [ ] `config.py`：`_get_default_model_spec` 加入供应商级 default_model 步 + recent 经 auth 过滤
- [ ] `model_selector.py`：`action_add_custom_provider` / `_reload_model_list` / Ctrl+A 绑定 / "Add Custom Provider" 按钮
- [ ] `model_selector.py`：`CustomProviderModalScreen`（表单 + Discover + 校验 + save_custom_provider）
- [ ] `model_selector.py`：`DiscoverModelsScreen`（SelectionList 多选 + Ctrl+A/N + select_all/none）
- [ ] `model_selector.py`：顶部 import `ModelDiscoveryError` / `fetch_provider_models`

### 阶段 D：状态跟踪（turn_end / session_end）

- [ ] `turn_end_summary.py`（522 行）：10 原因常量 + 优先级 + finish_reason 映射 + `mark_turn_start` / `observe_finish_reason` / `mark_turn_reason` / `classify_exception` / `finalize_turn` / `render_marker_text` / `render_marker_line`
- [ ] `turn_end_summary.py`：3 sink（TUI/JSONL/doc 追加）；`_find_project_root` / `_pick_today_doc` / `_append_to_doc`
- [ ] `tui/textual_adapter.py`：`_run_agent_loop` 接入（mark_turn_start / observe / 中断+异常分类 / finally finalize + mount marker）
- [ ] `session_end_summary.py`（329 行）：`REASON_*` + 优先级；`install` / `_install_excepthook` / `set_thread_id` / `mark_reason` / `mark_signal`
- [ ] `session_end_summary.py`：3 sink（stderr 面板 / 每线程 .txt / JSONL）；`_finalize` 幂等
- [ ] `main.py`：`session_end_summary.install()` 启动早期调用 + 信号处理 `mark_signal(signum)`
- [ ] `client/non_interactive.py`：turn_end（mark_turn_start / observe / finally finalize + console.print）+ session_end `set_thread_id`

### 阶段 E：MCP Trust / 服务器 / 其他

- [ ] `mcp_trust.py`（207 行）：`compute_config_fingerprint` / `is_project_mcp_trusted` / `trust_project_mcp` / `revoke_project_mcp_trust` + 原子写存储
- [ ] `main.py:_check_mcp_project_trust` 接线（指纹查询 + 交互批准 + 持久化）
- [ ] `mcp_tools.py` / `mcp_login_service.py` 接线指纹信任（注意与 main 的 `load_mcp_server_trust_lists` 名单机制协调）
- [ ] `client/commands/mcp.py` 信任文案改「fingerprint trust store」
- [ ] `client/launch/server.py`：`--allow-blocking` flag + `LANGGRAPH_ALLOW_BLOCKING=true` env
- [ ] `todo_list_prompt.md`（新增 12 行）
- [ ] `main.py` + `_env_vars.py`：`--no-mouse` flag + `NO_MOUSE` env + `_resolve_no_mouse` + `mouse=not _resolve_no_mouse(args)`

### 阶段 F：验证

- [ ] `git diff main..learn-backup-20260730-105659 -- libs/code/deepagents_code/<file>` 逐文件核对
- [ ] 跑 backup 侧新增测试：`test_mcp_trust.py` / `test_media_utils.py` / `test_turn_end_summary.py` / `test_session_end_summary.py` / `test_model_config.py`（save_custom_provider/fetch_provider_models）/ `test_model_switch.py`（CustomProvider/Discover）
- [ ] 品牌冒烟：`zjcode --version`（首行 `zjcode 0.0.8`）、`~/.zjcode/` 目录生成、`zjcode --help`
- [ ] TUI 冒烟：模型选择器 Ctrl+A 加供应商、Ctrl+V 粘贴图片、`/paste-image` `/copy-image`、每轮结束标记、退出面板

---

> **文档结束**。所有改动均经 `git show learn-backup-20260730-105659:<file>` 与 `git diff main..learn-backup-20260730-105659 -- <file>` 核对。如发现遗漏，用上述对比命令补查。