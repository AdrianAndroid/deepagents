# 2026-07-07 添加自定义供应商 Modal 的 Confirm 按钮

### 轮次 1 - 在左下角添加 Confirm 按钮

**用户提问要点**
- 在 `Add Custom Provider` 弹窗左下角（图中红框位置）添加一个确定/Confirm 按钮，与右下角的 `Cancel` 对齐。

**结论 / 方案**
- 源码位置：`libs/code/deepagents_code/widgets/model_selector.py` 中的 `CustomProviderModalScreen`。
- 原本 `compose` 已经同时 yield 了 `Cancel` 与 `Save` 两个按钮，但 CSS `.form-buttons` 使用默认布局 + `align: right middle`，导致按钮堆叠或视觉上只显示一个。
- 改动：
  1. CSS `.form-buttons` 改为 `layout: horizontal`，并新增两个子容器 `.form-buttons-left`（`align: left middle`）与 `.form-buttons-right`（`align: right middle`），各占 `1fr` 宽度。
  2. `compose` 将 `Save` 按钮改名为 `Confirm`，放入左侧容器；`Cancel` 放入右侧容器。按钮 `id="save-btn"` / `id="cancel-btn"` 保持不变，无需修改 `on_button_pressed` 与 `action_submit` 逻辑。

**关键文件改动**
- `libs/code/deepagents_code/widgets/model_selector.py`
  - `CustomProviderModalScreen.CSS`：更新 `.form-buttons` + 新增 `.form-buttons-left` / `.form-buttons-right`。
  - `CustomProviderModalScreen.compose`：底部按钮容器分为左右两栏，左栏 `Confirm`（primary），右栏 `Cancel`（default）。

**后续 TODO**
- 无（视觉与交互均沿用现有逻辑）。
