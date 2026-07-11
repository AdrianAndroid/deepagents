# 创建可直接运行的 Jupyter Notebook 文件

### 轮次 3 - 用户要求生成可点击运行的 .ipynb（类 PyCharm 体验）

**用户提问要点**：
- 需要一个真正的 `.ipynb` 文件，打开后可以像 PyCharm 那样在文件中直接点击运行按钮
- 上一轮的 `.py` 只能复制到 Notebook，无法直接点运行

**结论/方案**：
生成标准的 `nbformat 4.5` Notebook 文件 `examples/learn/jupyter_selftest.ipynb`，含 5 段代码 + Markdown 说明单元格。VSCode 打开后每个 code cell 左侧自动出现 ▶️ 运行按钮，跟 PyCharm 的行为一致。

**Notebook 内容结构**：
1. Markdown 标题 + 使用说明
2. Code：环境自检（Python/系统/包版本）
3. Code：打印 + 富文本
4. Code：NumPy + Pandas DataFrame + groupby
5. Code：Matplotlib 双子图
6. Code：变量面板演示（最后一行表达式）

**关键操作 / 文件改动**：
- 新建：`examples/learn/jupyter_selftest.ipynb`（标准 nbformat 4.5 结构，含 kernelspec: `python3`）

**补充：PyCharm 风格的 .py 替代方案**

在普通 `.py` 里用 `# %%` 分隔符，VSCode 会显示 `Run Cell` / `Run Below` / `Debug Cell` 按钮，结果显示在 Interactive Window 里：

```python
# %%
import numpy as np
print("cell 1")

# %%
x = np.arange(10)
x * 2
```

## 后续 TODO
- 用户如果需要 `# %%` 风格的 `.py` 示例，可再生成一份 `jupyter_selftest_interactive.py`。
