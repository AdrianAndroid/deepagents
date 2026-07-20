# 2026-07-17 合并 upstream/learn 分支:冲突解决与测试修复

## 用户需求
- 拉取远程代码,解决合并冲突,并运行单元测试。
- 约束:不要修改 `config.toml`。

## 背景状态
- 当前分支:`learn-backup-20260714-225025`,已经处于 merge-in-progress 状态。
- `MERGE_HEAD` = `86d099de`(upstream `learn` 的 `learn分支修复+测试+lint`)。
- 冲突文件共 7 个:
  1. `libs/acp/uv.lock`
  2. `libs/code/COMMANDS.md`(auto-generated)
  3. `libs/code/deepagents_code/config_manifest.py`
  4. `libs/code/deepagents_code/tui/widgets/model_selector.py`
  5. `libs/code/tests/unit_tests/test_main.py`
  6. `libs/code/tests/unit_tests/test_server.py`
  7. `libs/evals/uv.lock`
- 冲突文件中并不包含 `config.toml`,合并全程也未修改任何 `config.toml`。

## 解决方案概述
### 冲突解决策略
| 文件 | 策略 |
|---|---|
| `COMMANDS.md` | 采用 upstream 版本(auto-generated,先接受再由 `make commands-catalog` 重新生成) |
| `config_manifest.py` | 采用 upstream(更新 `display.no_mouse` 描述并新增 `cli_flag="--no-mouse"`) |
| `tui/widgets/model_selector.py` | 保留 HEAD 的安全注释 + `error_widget.update("")` |
| `tests/unit_tests/test_main.py`(两处) | 采用 upstream(多行 `_fake_run_async` 签名 + `**_kwargs`) |
| `tests/unit_tests/test_server.py` | 采用 upstream 的详细注释 |
| `libs/acp/uv.lock` `libs/evals/uv.lock` | `git checkout --theirs` 取 upstream 版本后 `uv lock` 重新解析(evals 中因本地 code 版本为 0.0.8 而生成新哈希) |

### merge commit
```
Merge branch 'learn' from upstream, resolve conflicts
```
提交 SHA: `cb0e810d`。

## 全量单元测试第一轮:14 failed
`make test` 结果 `14 failed, 9071 passed`。失败集中在三个方向:

### 1. `test_command_registry.py` × 3
- 报错:`AssertionError: Duplicate command names found`(35 vs 34)。
- 根因:HEAD 与 MERGE_HEAD 都各自新增了 `/add-provider` SlashCommand(位置和描述不同,git 未标记为冲突)。
- 修复:合并为单条,保留 upstream 位置/描述,叠加本地 `argument_hint`;然后跑 `make commands-catalog` 重新生成 `COMMANDS.md`。

### 2. `test_app.py::TestToolsSlashCommand` × 8
- 报错:`assert mount.await_count == 2`,实际 3。
- 根因:本地 commit `20c1e57b` 在 `_handle_command` 顶层给几乎所有命令加了 `UserMessage` echo,但 `_handle_tools_command` 自己内部仍然在做 `await self._mount_message(UserMessage(command))` → 双重回显。
- 修复:删除 `_handle_tools_command` 内部的重复 echo,依赖顶层统一 echo。

### 3. `tui/widgets/test_model_selector.py::TestCustomProviderModalScreen::test_keyboard_accessibility` × 1
- 报错:tab 到按钮时,期望 `save-btn` 先聚焦,实际先聚焦 `cancel-btn`。
- 根因:upstream 把按钮布局改为 `Cancel(左) / Confirm(右)`,tab 顺序自然变为 cancel → save;但测试文件在合并时保留了旧顺序断言。
- 修复:更新测试断言为先 `cancel-btn` 后 `save-btn`。

### 4. `test_transcript_virtualization::test_scroll_down_hydrates_tail_below` × 1
- 单独运行通过,是全量运行下的偶发时序问题,不做特殊处理。

## 修复 commit
```
fix(code): repair post-merge test regressions
```
SHA: `fe7c95ea`,涉及文件:
- `deepagents_code/app.py`(去掉 `_handle_tools_command` 重复 echo)
- `deepagents_code/command_registry.py`(去重 `/add-provider`,保留 argument_hint)
- `COMMANDS.md`(重新生成)
- `tests/unit_tests/tui/widgets/test_model_selector.py`(修正 tab 顺序断言)

## 最终验证
`make test` 结果:**9085 passed**,一个 `TestGoalCommand::test_initial_goal_acceptance_submits_objective` 的 teardown 阶段偶发报错(teardown 26s,单跑正常),非断言失败,判定为环境时序问题,可忽略。

## 关键复盘 / 沉淀经验
1. **auto-generated 文件冲突**:遇到 `COMMANDS.md` 这种由脚本生成的文件,先择一版本合并冲突标记,然后立刻运行生成脚本(`make commands-catalog`),不要手改。
2. **重复添加同名命令**:双方分支各自新增 `/add-provider` 属于逻辑冲突(git 未标记),表现为 `test_command_registry` 挂了。合并后必须跑单元测试挖出这类隐冲突。
3. **命令 echo 单一职责**:本地把 UserMessage echo 上移到 `_handle_command`,后续新增或修改任何具体 `_handle_xxx_command` 时都不能再自行 mount `UserMessage`,否则回显翻倍。测试用 `mount.await_count == 2` 恰好卡住这一约束。
4. **UI 布局改动会顺带改变 tab 顺序**:PR 只调整按钮左右顺序也需要同步更新键盘可访问性测试。
5. **uv.lock 冲突推荐流程**:`git checkout --theirs uv.lock` 取新的一侧作为起点,再 `UV_FROZEN=false uv lock` 重新生成,可避免手工合并 lock 段落导致校验和不一致。
