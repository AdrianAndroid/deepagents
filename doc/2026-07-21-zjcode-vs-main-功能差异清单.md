# zjcode 分支功能差异清单（zjcode vs main）

> 本文档记录 `zjcode` 分支相对于 `main` 分支的所有功能改动，方便后续从 `main` 切新分支后按此文逐项应用。

---

## 一、品牌隔离层（zjcode 包）

### 1.1 新增 `libs/code/zjcode/` 包（上游不存在）

| 文件 | 作用 |
|---|---|
| `zjcode/__init__.py` | 包入口，导出品牌常量、MCP trust 函数、patch 函数 |
| `zjcode/brand.py` | 品牌专属配置：`DISTRIBUTION_NAME="zjcode"`、`CONFIG_DIR_NAME=".zjcode"`、`PYPI_URL`、`PATCH_MAP` 等 |
| `zjcode/patches.py` | 运行时品牌补丁应用器：`apply_brand_patches()` 动态修改模块属性；`patch_path_constants()` 修改 `DEFAULT_CONFIG_DIR`、`DEFAULT_CONFIG_FILE`、`STATE_DIR`、`PASTED_MEDIA_DIR`、`_GLOBAL_DOTENV_PATH` 等路径常量 |
| `zjcode/mcp_trust.py` | MCP trust store：基于指纹的项目级 MCP 配置信任管理（`compute_config_fingerprint`、`is_project_mcp_trusted`、`trust_project_mcp`、`revoke_project_mcp_trust`） |
| `zjcode/todo_list_prompt.md` | 自定义 todo list 提示词模板 |
| `zjcode/ZJCODE_BRAND_MIGRATION_GUIDE.md` | 品牌迁移指南 |

### 1.2 `deepagents_code/__init__.py` 品牌钩子（3 行）

在模块顶部加入 zjcode patch 入口：

```python
try:
    from zjcode import apply_all_patches
    apply_all_patches()
except ImportError:
    pass
```

### 1.3 品牌名称替换（全局 sed 级替换）

以下文件中将 `dcode` / `deepagents-code` 替换为 `zjcode`：

- `_version.py`: `__version__`、`PYPI_URL`、`USER_AGENT`
- `_invocation.py`: `DEFAULT_INVOKED_NAME`、`STANDARD_INVOKED_NAMES`
- `_env_vars.py`: 文档字符串中的品牌名
- `config.py`: `CODING_AGENT_INTEGRATION`、LangSmith metadata key（`zjcode_experimental`、`zjcode_auto_approve`、`zjcode_agent_name`、`zjcode_client_deepagents_version`）
- `config_manifest.py`: `LANGSMITH_PROJECT_DEFAULT`、`settings_field` 改名
- `update_check.py`: 升级命令、安装脚本 URL、prerelease 文件前缀
- `ui.py`: help 文本中的所有命令示例
- `main.py`: 版本文本、错误提示、安装命令
- `app.py`: 用户提示、更新消息、错误处理文本
- `doctor.py`: 诊断输出中的品牌名
- `extras_info.py`: 文档字符串
- `tool_catalog.py`: 文档字符串
- `auto_mode.py`: 分类器 policy 文本、临时文件前缀
- `skills/commands.py`: 帮助文本中的命令示例和路径
- `tui/widgets/auth.py`: 认证提示文本
- `tui/widgets/install_confirm.py`: 安装确认文本
- `client/launch/server.py`: 文档字符串

### 1.4 配置目录常量化

- `_constants.py`: 新增 `CONFIG_DOTDIR`、`PROJECT_DOTDIR` 常量（值由 zjcode patch 设为 `.zjcode`）
- `mcp_tools.py`: 用 `_constants.CONFIG_DOTDIR` 替换硬编码的 `.deepagents`
- `project_utils.py`: 用 `PROJECT_DOTDIR` 替换硬编码的 `.deepagents`
- `main.py`: `~/.deepagents` → `~/.zjcode`（`_recent_agent_is_valid`）
- `local_context.py`: `_section_files()` 用 `PROJECT_DOTDIR` 变量

### 1.5 pyproject.toml 改动

- `name` → `zjcode`
- `version` → `0.0.8`（独立版本线）
- `description` 更新
- `deepagents==0.7.0a7`（预发布版 pin）
- 多个依赖下限放宽（langchain、textual、langchain-openai 等）

---

## 二、新增功能模块

### 2.1 会话结束状态追踪 `session_end_summary.py`（329 行，新文件）

- 进程级关闭时记录退出原因（`completed`/`interrupted`/`error`）和运行时长
- 三个输出 sink：stderr 面板、`~/.deepagents/.state/session_end/<thread_id>.txt`、`~/.deepagents/session_end_log.jsonl`
- 通过 `atexit` + `sys.excepthook` 钩入关闭流程
- 幂等、never-raises、零重导入

### 2.2 单轮结束状态追踪 `turn_end_summary.py`（522 行，新文件）

- 单轮 agent turn 结束时记录原因和耗时
- 10 种结束原因：`completed`/`length_capped`/`content_filtered`/`tool_rejected`/`user_interrupted`/`stream_error`/`provider_error`/`timeout`/`recursion_limit`/`unknown_truncation`
- 三个 sink：TUI/console 显示、`~/.deepagents/turn_end_log.jsonl`、项目 `doc/YYYY-MM-DD-*.md` 追加
- `observe_finish_reason()` 从 response metadata 提取 finish_reason
- `classify_exception()` 将异常映射到结束原因
- `render_marker_text()` 渲染 `> ⏹ 结束状态：...` 标记

### 2.3 图片复制到剪贴板 `clipboard.py` 扩展

- 新增 `copy_image_to_clipboard(image_data)` 函数
- 支持 macOS（osascript），将 ImageData 复制到系统剪贴板

### 2.4 媒体输入增强（`input.py` 大幅重写，+600 行）

- 新增 `_MediaKindState` 泛型类：统一管理 image/video 两种媒体的 attach/detach/evict 状态
- 新增 `_MediaPartition` dataclass：re-split 结果
- `MAX_DETACHED_MEDIA=10`、`MAX_DETACHED_MEDIA_BYTES=32MB`：undo 池上限
- `_map_placeholder_span()`：用 SequenceMapper diff 在文本编辑后映射 placeholder 位置
- `ChatTextArea.undo()`/`redo()` 重写：支持 undo/redo 时恢复媒体
- `_reverse_history_batch()`：undo/redo 时同步媒体 tracker
- `_notify_stranded_media()`：undo 恢复了已驱逐的 placeholder 时警告用户
- `_media_edit_token()`：为 Textual edit batch 生成稳定标识

### 2.5 会话分隔符 `SessionSeparator`（`messages.py`）

- 新增 `SessionSeparator` widget：显示 `---\n✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨\n---`
- 在 `app.py` 中导入并使用

### 2.6 Copy Turn 按钮 `CopyTurnButton`（`messages.py`）

- 新增 `CopyTurnButton` widget：在 AssistantMessage 底部显示 `[ Copy ]` 按钮
- 点击复制整轮 Q&A（用户问题 + 助手回答）到剪贴板
- 流式输出完成后才显示

### 2.7 `--no-mouse` 标志

- `config_manifest.py`: 新增 `display.no_mouse` 配置项
- `_env_vars.py`: 新增 `NO_MOUSE` 环境变量（`ZJCODE_NO_MOUSE`）
- 用于 web 终端（1Panel、ttyd、wetty）禁用 Textual 鼠标追踪

### 2.8 `media_utils.py` 改动

- `ImageData.placeholder` 默认值改为 `""`（空字符串，未绑定状态）
- `VideoData.placeholder` 同上
- 移除 `get_image_from_path`、`get_video_from_path`、`_get_macos_clipboard_image` 等处的 `placeholder="[image]"` 硬编码

### 2.9 Kitty 键盘补丁增强（`_textual_patches.py`）

- 新增 `_kitty_colon_text_events()`：解码冒号分隔的 Kitty associated-text 码点
- 修复 Textual 8.2.8 无法解析 `126:47` 这类序列的问题
- 导入 `_character_to_key` from `textual.keys`

---

## 三、SDK 改动（`libs/deepagents/`）

### 3.1 `backends/utils.py`: `validate_path` 支持 Windows 原生路径

- 新增 `allow_native_absolute: bool = False` 参数
- 当 `True` 时保留 Windows 驱动器路径（如 `D:\...`）不拒绝
- 用于非虚拟本地文件系统后端

### 3.2 `middleware/filesystem.py`: 所有 FS 工具传递 `allow_native_absolute`

- 新增 `_accepts_native_absolute_paths(backend)` 判断函数
- `ls`、`read_file`、`write_file`、`edit_file`、`delete` 的 sync/async 版本全部调用 `validate_path(..., allow_native_absolute=_accepts_native_absolute_paths(backend))`

---

## 四、Approval Mode 改动

### 4.1 `agent.py` `_approval_mode_source`

- YOLO 模式：即使缺少 Store key 也直接返回 `_DecidedMode(ApprovalMode.YOLO)`
- Auto 模式：缺少 Store key 时 fallback 到 Manual（不再直接 raise）
- 修改了 legacy_auto 兼容逻辑

### 4.2 `tui/textual_adapter.py` `execute_task_textual`

- YOLO 模式无 Store writer 时不再 fallback 到 Manual，而是通过 context 携带
- 只有 Auto/Manual 无 Store key 时才 fallback
- 移除了 `raise RuntimeError` 阻塞逻辑

### 4.3 `auto_mode.py` `_live_mode`

- 无 Store key 时检查 context 中的 `approval_mode`，若为 YOLO 则直接返回
- Store key 为 None 时同样检查 context

---

## 五、Model Config 增强（`model_config.py`）

### 5.1 内置模型 profiles

- 新增 `_BUILTIN_MODEL_PROFILES` 字典：OpenAI（GPT-5 全系列）和 Anthropic（Claude Opus 5）的 reasoning effort 配置
- 新增 `_with_builtin_profiles()` 函数：合并上游 profiles 和内置 profiles
- 在 `get_available_models()` 和 `get_model_profiles()` 中使用

---

## 六、Server 改动（`client/launch/server.py`）

- `_build_server_cmd`: 添加 `--allow-blocking` 标志
- `_build_server_env`: 添加 `LANGGRAPH_ALLOW_BLOCKING=true`
- 解决 langgraph dev 的 blockbuster 在图构造时 `BlockingError` 问题

---

## 七、MCP Trust 独立化

- `deepagents_code/mcp_trust.py`: 变为 re-export shim（12 行），从 `zjcode.mcp_trust` 导入
- `zjcode/mcp_trust.py`: 完整实现（207 行）

---

## 八、构建与发布

### 8.1 GitHub Actions

- `.github/workflows/publish-zjcode.yml`（新文件）：通过 tag `zjcode-v*` 触发，Trusted Publisher (OIDC) 发布到 PyPI

### 8.2 脚本

- `scripts/bump-version.py`（242 行）：同步 bump `pyproject.toml` / `_version.py` / `.release-please-manifest.json` 三处版本号
- `scripts/check-brand-after-merge.sh`（84 行）：合并后检查品牌常量是否被覆盖
- `scripts/zjcode-brand-migration.py`（458 行）：品牌迁移自动化脚本

### 8.3 开发脚本

- `libs/code/dcode-dev.ps1`（Windows）
- `libs/code/zjcode-dev.ps1`
- `libs/code/bump-version.py`

### 8.4 Web 安装页面

- `web/index.html`、`web/404.html`
- `web/install.sh`、`web/install.ps1`
- `web/uninstall.sh`、`web/uninstall.ps1`
- `web/run-deploy.sh`、`web/run-serve.sh`

---

## 九、文档与示例

- `AGENTS.md`: 大幅扩展，增加发布默认目标、文档留存规则、会话分隔符规范、单轮结束标记规范
- `libs/code/BRAND_MIGRATION_README.md`: 品牌迁移说明
- `examples/README_zh.md`: 中文 README
- `examples/langchain1.2_tutorial/`: LangChain 1.2 教程（大量 notebook）
- `资料文档/`: 私有 PyPI 搭建、安装脚本、分发说明等

---

## 十、Skills

- `.zjcode/skills/publish-zjcode-version/SKILL.md`: 发布 zjcode 新版本的 skill
- `.zjcode/skills/zjcode-brand-migration/SKILL.md`: 品牌迁移 skill
- `.zjcode/skills/publish-zjcode-version/scripts/relax-pin-step.yml`: 发布时放宽 SDK pin 的步骤

---

## 十一、其他改动

### 11.1 `app.py` BadRequestError 处理

- `_build_agent_error_body`: 新增 `BadRequestError` 分支，提示用户图片可能过大或格式不支持，并移除失败消息

### 11.2 `.release-please-manifest.json`

- 增加 zjcode 版本基线

### 11.3 `.gitignore`

- 增加 zjcode 相关忽略项

### 11.4 `config.py` distribution lookup

- `distribution("deepagents-code")` → `distribution("zjcode")`

### 11.5 `config.py` LangSmith metadata keys

- `dcode_experimental` → `zjcode_experimental`
- `dcode_auto_approve` → `zjcode_auto_approve`
- `dcode_agent_name` → `zjcode_agent_name`
- `dcode_client_deepagents_version` → `zjcode_client_deepagents_version`
- `lc_versions` key: `deepagents-code` → `zjcode`

### 11.6 `config_manifest.py` settings_field

- `deepagents_langchain_project` → `zjcode_langchain_project`

### 11.7 `local_context.py`

- `_section_files()` 中的 `.deepagents` 替换为 `PROJECT_DOTDIR` 变量（f-string）
- awk 脚本中的花括号转义

### 11.8 `tui/widgets/update_confirm.py` 和 `update_progress.py`

- 品牌文本替换

### 11.9 测试文件

- 大量测试文件中的品牌名称同步更新
- 新增 `test_filesystem_middleware_init.py`（SDK filesystem middleware init 测试）
- 新增 `backends/test_utils.py`（validate_path allow_native_absolute 测试）

---

## 快速应用指南（从 main 切新分支后）

1. **创建 `libs/code/zjcode/` 包**：复制 `brand.py`、`patches.py`、`mcp_trust.py`、`todo_list_prompt.md`、`__init__.py`
2. **`deepagents_code/__init__.py`**: 添加 3 行 patch 钩子
3. **品牌名称替换**：全局将 `dcode`→`zjcode`、`deepagents-code`→`zjcode`（注意 `_constants.py` 中的 `Harzjcoded` 误替换也需保留）
4. **配置目录常量化**：`_constants.py` 添加 `CONFIG_DOTDIR`/`PROJECT_DOTDIR`，在 `mcp_tools.py`、`project_utils.py`、`local_context.py`、`main.py` 中替换硬编码 `.deepagents`
5. **pyproject.toml**: 改 name/version/description/依赖版本
6. **新增功能文件**：`session_end_summary.py`、`turn_end_summary.py`
7. **修改功能文件**：`clipboard.py`（图片复制）、`input.py`（媒体追踪重写）、`messages.py`（SessionSeparator + CopyTurnButton）、`_textual_patches.py`（Kitty 补丁）、`model_config.py`（内置 profiles）、`media_utils.py`（placeholder 默认值）
8. **SDK 改动**：`backends/utils.py`（validate_path）、`middleware/filesystem.py`（allow_native_absolute）
9. **Approval mode**：`agent.py`、`tui/textual_adapter.py`、`auto_mode.py`
10. **Server**：`client/launch/server.py`（--allow-blocking）
11. **MCP trust shim**：`deepagents_code/mcp_trust.py` 改为 re-export
12. **构建发布**：`publish-zjcode.yml`、`scripts/` 三个脚本、`web/` 目录
13. **config.py**：distribution lookup 和 LangSmith metadata key 改名
14. **config_manifest.py**：`LANGSMITH_PROJECT_DEFAULT`、`settings_field`、`display.no_mouse` 选项
15. **运行 `scripts/check-brand-after-merge.sh`** 验证品牌常量未被覆盖
