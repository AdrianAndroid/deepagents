# /model 命令链路与自定义供应商回显排查

会话日期：2026-07-04
涉及包：`libs/code`（deepagents-code）

---

## 轮次 1 - `/model` 命令完整链路总结（用于排查自定义供应商没回显）

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
- 待用户确认自定义供应商在 config.toml 中的实际写入形式，若被并入内建 provider 分组或落到 `custom_model` 兜底，则回到对应分支进一步排查。

---

## 轮次 2 - `_apply_subset` 与 `is_provider_enabled` 的具体判断细节

### 用户提问要点
希望展开 `_apply_subset` 和 `is_provider_enabled` 的具体判断逻辑，并把之前"服务器启动错误"相关内容从本文档中删掉。

### `ModelConfig.is_provider_enabled`（`model_config.py:2482`）

**判断规则非常简单，只关心 `[models.providers.<id>].enabled` 一个字段**：

```python
def is_provider_enabled(self, provider_name: str) -> bool:
    provider = self.providers.get(provider_name)
    if not provider:
        return True                                   # 没配就当作启用
    return provider.get("enabled") is not False       # 只有显式 False 才禁用
```

真值表：

| `[models.providers.<id>]` | `enabled` 字段 | `is_provider_enabled` |
| --- | --- | --- |
| 未在 config.toml 中出现 | —（内建 provider 未被 override） | `True` |
| 有该 section，未写 `enabled` | 缺失 | `True` |
| 有该 section，`enabled = true` | `True` | `True` |
| 有该 section，`enabled = false` | `False` | `False` |
| 有该 section，`enabled = "yes"` 等非 `False` 值 | 非 `False` | `True`（宽松：只对 `is False` 敏感） |

**在 `get_available_models` 中的四个调用点**：

| 行号 | 场景 | 禁用后果 |
| --- | --- | --- |
| `:957` | 遍历 registry 内建 provider | 跳过，该 provider 所有内建模型不进 `available` |
| `:997` | 遍历 config.toml 里的自定义 provider | 跳过整个自定义 provider |
| `:1059` | Ollama daemon 探活 | 不再探活，不合并本地已 pull 的模型 |
| `:1080` | `openai_codex` 镜像 | 不再从 `openai` 镜像出 `openai_codex` 组 |

**排查提示**：
- 显式加 `enabled = false` 会**在任何列表/UI 逻辑之前**被静默过滤掉。
- 用 `enabled = true` 或直接删掉这一行都能恢复显示。
- 想临时屏蔽内建 provider（比如不想看到 `openai`），可以在 `[models.providers.openai]` 里加 `enabled = false`——registry 分支 (`:957`) 也会读这个字段。

### `ModelSelectorScreen._apply_subset`（`widgets/model_selector.py:649`）

**这一层不看 `enabled`，只在 UI 侧做"子集裁剪"**。它决定的是：从 `_unfiltered_models`（`get_available_models` 展平后的完整列表）里挑多少行赋给 `_all_models`。

```python
def _apply_subset(self, all_models):
    if self._curated:                                # ① onboarding curated
        return self._curate_models(all_models)
    if self._recommended_only:                       # ② /model 默认 (Ctrl+R 切换)
        curated = self._curate_models(all_models)
        curated_specs = {spec for spec, _ in curated}
        recent_extra = [
            (spec, provider)
            for spec, provider in all_models
            if spec in self._recent_specs and spec not in curated_specs
        ]
        return [*recent_extra, *curated]             # MRU 优先，随后是推荐
    return list(all_models)                          # ③ 完整视图
```

三种模式对照：

| 模式 | `_curated` | `_recommended_only` | 返回内容 |
| --- | --- | --- | --- |
| ① Onboarding curated | `True` | 忽略 | 仅 `_RECOMMENDED_MODELS` 命中的（若一个都没有，就返回全部避免空屏） |
| ② `/model` 默认（Ctrl+R = ON） | `False` | `True` | MRU（不含推荐重复的）+ 推荐子集 |
| ③ 完整视图（Ctrl+R = OFF） | `False` | `False` | `list(all_models)` 全量 |

**状态由构造函数设定**（`widgets/model_selector.py:403`）：

```python
self._recommended_only = not curated
```

也就是说：
- **onboarding 入口** (`curated=True`) → `_curated=True`, `_recommended_only=False`，走 ①。
- **普通 `/model`** (`curated=False`) → `_curated=False`, `_recommended_only=True`，**默认走 ②**，即"只显示推荐 + MRU"。
- 用户在选择器里按 **Ctrl+R** 会切换 `_recommended_only`（`:1788`），切到 ③ 完整视图。

### `_curate_models`（`widgets/model_selector.py:683`）

```python
frontier = [
    (spec, provider)
    for spec, provider in all_models
    if spec in _RECOMMENDED_MODELS
]
return frontier or all_models
```

- `_RECOMMENDED_MODELS` 是一个**硬编码 frozenset**（`widgets/model_selector.py:66`），全部是形如 `"anthropic:claude-opus-4-8"`、`"openrouter:openai/gpt-5.5-pro"` 之类的 `provider:model` 全 spec。
- 只有 spec 完全匹配才会入选。
- 如果全都不匹配（比如你只装了自定义 provider），fallback 到 `all_models`——**这里避免了完全空屏**。

### 「自定义供应商没回显」在 `_apply_subset` 的具体表现

一个典型场景：

1. 你 `/add-provider huoshan1 ...` 落盘成功。
2. `get_available_models()` 里 huoshan1 的模型进了 `available`。
3. `_load_model_data` 展平到 `_unfiltered_models`，**里面已经有 huoshan1 的模型**。
4. `_apply_subset` 走默认分支 ②（`_recommended_only=True`）。
5. `_curate_models` 挑 `_RECOMMENDED_MODELS`（一个都不匹配 huoshan1）。
6. `recent_extra` 也是空的（你还没用过 huoshan1）。
7. 结果 `_all_models = [*recent_extra, *curated]` = 只有推荐——**huoshan1 在这里被过滤掉**。

**这时候要做的**：
- 按 **Ctrl+R** 切换到分支 ③（完整视图），或
- 在过滤框里直接输入 `huoshan1:` / 模型名 —— 有过滤文字时 `_update_display` 会跳过 `_apply_subset` 后的 `_all_models`、直接从 `_unfiltered_models` 搜（`:854`, `:1010`）。

用一次之后 spec 会进入 MRU（`_recent_specs`），下次开 `/model` 直接进入分支 ②，就会通过 `recent_extra` 分支把它保留下来。

### 汇总：一次 `/model` 打开时数据经过的过滤链

```
config.toml (~/.deepagents/config.toml)
        │  ModelConfig.load()
        ▼
ModelConfig.providers  ──┐
        │  get_available_models() 遍历 registry + config providers  │
        │  → 每个 provider 都用 is_provider_enabled 过滤            │  <-- 关卡 A（enabled=false 在这里被杀）
        ▼                                                           ▼
available: dict[provider, [models]]                          registry providers
        │  _load_model_data 展平
        ▼
_unfiltered_models: list[(spec, provider)]                          <-- 全量
        │  _apply_subset:
        │    ①  _curated       → 只留推荐
        │    ②  _recommended_only → MRU + 推荐                     <-- 关卡 B（默认在这里被 UI 侧过滤）
        │    ③  完整             → 保持全量
        ▼
_all_models
        │  过滤框 / Ctrl+R / _update_filtered_list
        ▼
_filtered_models
        │  _update_display 分组 + _provider_availability_rank 排序
        ▼
屏幕上的列表
```

关卡 A（`is_provider_enabled`）和关卡 B（`_apply_subset`）是"自定义供应商回显不出来"的两条最常见路径。前者是**硬过滤**（`enabled=false`），后者是**软过滤**（Ctrl+R 可切换）。

### 关键文件与行号索引（追加项）

| 位置 | 说明 |
| --- | --- |
| `libs/code/deepagents_code/widgets/model_selector.py:66` | `_RECOMMENDED_MODELS` frozenset 定义 |
| `libs/code/deepagents_code/widgets/model_selector.py:403` | 构造函数中 `_recommended_only = not curated` |
| `libs/code/deepagents_code/widgets/model_selector.py:1788` | Ctrl+R 切换 `_recommended_only` |
