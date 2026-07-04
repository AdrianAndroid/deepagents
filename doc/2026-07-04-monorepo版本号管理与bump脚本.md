# 2026-07-04 monorepo版本号管理与bump脚本

## 轮次 1 - 三处版本号说明

**用户提问要点**：如何修改版本号，看到有多个地方都有版本号。

**结论/方案**：`libs/code`（`deepagents-code`）包的版本号存在 **3 处**，正常由 release-please 自动同步，只有非常规场景才手动改。

三处位置（以 0.1.30 为例）：

| 文件 | 说明 |
|---|---|
| `libs/code/pyproject.toml` 第 7 行 `version = "0.1.30"` | 构建工具读取（hatchling / uv build / pip） |
| `libs/code/deepagents_code/_version.py` 第 5 行 `__version__ = "0.1.30"  # x-release-please-version` | 运行时代码使用；行尾注释是 release-please 的锚点 |
| 仓库根 `.release-please-manifest.json` 中 `"libs/code": "0.1.30"` | release-please 自身状态游标 |

配置在 `release-please-config.json` 的 `packages["libs/code"].extra-files` 里显式列出前两个文件。

**推荐做法**：按 Conventional Commits 提交（`feat(code): …`、`fix(code): …`），merge 到 `main` 后 release-please 自动开 `release(deepagents-code): X.Y.Z` PR 并同步三处。

**手动改**：必须三处一起改成同一个值，改完在 `libs/code` 目录跑 `uv lock`，然后 `make lint test`。

## 轮次 2 - 为什么三处不能统一

**用户提问要点**：这三个地方，不能统一使用一个吗？

**结论/方案**：技术上可以（`[project].dynamic = ["version"]` + `[tool.hatch.version].path` 指向 `_version.py`；或反过来运行时用 `importlib.metadata.version(...)` 读包元数据），但当前仓库故意保留三处，权衡结果：

**为什么保留三处**：
- 三处各自有不同"读者"，都需要静态字符串直接读取
  - `pyproject.toml` — PyPI 构建工具读，需要静态字符串（除非声明 `dynamic`）
  - `_version.py` — 运行时代码用（`--version`、User-Agent），不 import 包元数据是为避免启动开销和循环依赖
  - manifest — release-please 的**状态**，不是版本副本，无法消除
- release-please 是唯一写入者，`extra-files` + 行尾锚点注释让 1、2 在一次 PR 中原子同步
- 有 CI 校验（`.github/workflows/check_*`）保证不漂移

**统一方案的代价**：
- 方案 A（`pyproject.toml` 为源，运行时 `importlib.metadata`）：未安装时抛异常、增加启动开销（`libs/code` TUI 明确关注启动性能）
- 方案 B（`_version.py` 为源，`pyproject.toml` 用 dynamic）：旧版 pip / 部分工具对 dynamic 支持较差
- 方案 C（消除 manifest）：做不到，除非换掉整个 release-please 工具链

**最实际的做法**：不改配置，而是写脚本一次改三处。

## 轮次 3 - 编写 bump-version.py 脚本

**用户提问要点**：可以（同意写脚本）。

**关键操作**：
- 新建 `/Users/zhaojian/code/deepagents/scripts/` 目录
- 新增 `scripts/bump-version.py`（Python 3，无第三方依赖）

**脚本特性**：
- 从 `release-please-config.json` 的 `extra-files` **动态发现**要改的文件，不硬编码路径
- 支持三种方式定位包：
  - 完整路径：`libs/code`、`libs/partners/quickjs`
  - 包名：`deepagents-code`、`langchain-quickjs`
  - 短别名（路径最后一段）：`code`、`quickjs`
- 严格保留 `# x-release-please-version` 锚点注释（正则匹配整行）
- semver 校验（拒绝无效版本号）
- 漂移检测：改前如果三处不一致，会打印警告
- `--dry-run` 预览
- `--list` 列出所有包及当前版本
- 只改文件，不 commit / tag / push

**使用命令**：
```bash
python3 scripts/bump-version.py --list                  # 列出所有包
python3 scripts/bump-version.py code 0.1.31 --dry-run   # 预览
python3 scripts/bump-version.py code 0.1.31             # 落盘
```

**验证结果**：
- `--list` 正确输出 10 个包（cli / deepagents / acp / code / talon / 5 个 partners）及当前版本
- `--dry-run` 正确识别 `code` 别名，显示会更新 `libs/code/pyproject.toml`、`libs/code/deepagents_code/_version.py`、`.release-please-manifest.json` 三个文件

**关键文件改动**：
- 新增：`scripts/bump-version.py`（可执行，已 chmod +x）

## 后续 TODO
- 无。用户如需改版本号，直接 `python3 scripts/bump-version.py <pkg> <ver>`，然后 `cd libs/<pkg> && uv lock`。
