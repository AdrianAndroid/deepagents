# VSCode Jupyter Notebook 一键自检代码（会话追加）

### 轮次 2 - 用户要求提供完整测试代码

**用户提问要点**：在上一轮教程基础上，要求给出一段可直接复制的完整测试代码，包含打印、数值计算、绘图（并希望覆盖 pandas / 数据处理 / 变量面板等常用场景）。

**结论/方案**：生成 5 段结构化单元格代码，覆盖环境自检、打印/富文本、NumPy+Pandas、Matplotlib 双子图、变量面板演示，并保存到 `examples/learn/jupyter_selftest.py` 方便复制到 `.ipynb`。

**关键操作 / 文件改动**：
- 新建代码文件：`examples/learn/jupyter_selftest.py`
- 追加本轮记录到教程文档同名 md（此文件为独立追加，未合并到 165620 教程正文以保持原教程整洁）

## 5 段单元格用途速览

| 单元格 | 内容 | 验证目标 |
|--------|------|----------|
| 1 | `sys / platform / os` + 关键库版本探测 | Python 解释器、numpy/pandas/matplotlib 是否可用 |
| 2 | `print` + `IPython.display.Markdown` | 基本输出 + 富文本渲染 |
| 3 | NumPy 随机数 + Pandas DataFrame + `groupby` | 数据处理链路 + 表格渲染 |
| 4 | Matplotlib 双子图（sin/cos 折线 + 分数柱状） | 内联绘图 (`%matplotlib inline` 默认) |
| 5 | 汇总变量 `summary` 作为最后一行表达式 | 演示 Jupyter 表达式自动输出 + 变量面板 |

## 常见踩坑
- **缺依赖**：`python -m pip install numpy pandas matplotlib`（用 `python -m pip` 避免装到其他解释器）
- **中文字体警告**：仅 `axes.unicode_minus = False` 即可解决负号显示，中文标题需额外配置 `font.family`
- **绘图不显示**：老版本 VSCode 需要显式 `%matplotlib inline`，新版本 Jupyter 扩展默认已启用

## 后续 TODO
- 用户若在实际环境运行遇到具体报错，把报错贴过来再帮忙定位。
