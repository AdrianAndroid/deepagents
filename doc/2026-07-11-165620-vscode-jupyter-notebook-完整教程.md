# VSCode 创建并运行 Jupyter Notebook 完整教程

### 轮次 1 - 用户分享 VSCode + Jupyter 完整使用教程

**用户提问要点**：用户直接分享了一份完整的 "VSCode 创建并运行 Jupyter Notebook 教程"，覆盖前置安装、创建 Notebook、选择内核、编写运行代码、常见报错修复、附加功能等，并询问是否需要一段完整测试代码。

**结论/方案**：内容作为知识沉淀记录到项目 `doc/` 目录，供后续复用。核心要点整理如下。

---

## 一、前置安装（必须全部完成）

### 1. 安装 VSCode 扩展
1. `Ctrl+Shift+X` 打开扩展市场
2. 搜索安装 **2 个官方插件**：
   - **Python**（微软官方，Python 语法、解释器管理）
   - **Jupyter**（微软官方，Notebook 核心）

安装完成后重启 VSCode。

### 2. 安装 Python 依赖（终端执行）
在 VSCode 内置终端，切到目标 Python 环境后执行：

```bash
# 安装 jupyter 内核依赖（缺一不可）
pip install jupyter notebook ipykernel
```

- Windows 多 Python 版本用 `pip3`
- Conda 环境：`conda install jupyter ipykernel notebook`

### 3. 选定 Python 解释器
`Ctrl+Shift+P` → 输入 `Python: Select Interpreter` → 选择装了 `ipykernel` 的 Python 环境（虚拟环境 / 系统 Python）。

---

## 二、3 种方式创建 Jupyter 文件（.ipynb）

### 方式 1：命令面板（推荐）
1. `Ctrl+Shift+P` 打开命令面板
2. 输入 `Jupyter: Create New Jupyter Notebook`
3. 回车即可新建空白 Notebook 文件

### 方式 2：手动新建文件
资源管理器右键 → 新建文件 → 命名为 `test.ipynb`（后缀必须是 `.ipynb`）

### 方式 3：顶部菜单栏
文件 → 新建文件 → 下拉选择 `Jupyter Notebook`

---

## 三、选择内核（首次必操作）
打开 `.ipynb` 后，右上角显示 **Select Kernel**：
1. 点击 `Select Kernel`
2. 选择前面指定的 Python 解释器（带版本号）
3. VSCode 自动启动 Jupyter 内核，状态栏显示内核名即连接成功

> 若报错找不到内核：重新执行 `pip install ipykernel`，再重启 VSCode。

---

## 四、编写 & 运行代码测试

### 1. 基础单元格代码
```python
# 测试1：打印输出
print("VSCode Jupyter 运行成功！")

# 测试2：简单运算
a = 10 + 20
print(a)

# 测试3：绘图验证（可选）
import matplotlib.pyplot as plt
plt.plot([1, 2, 3], [4, 1, 2])
plt.show()
```

### 2. 运行快捷键
| 快捷键 | 功能 |
|--------|------|
| `Shift+Enter` | 运行当前单元格，自动跳到下一格 |
| `Ctrl+Enter`  | 运行当前单元格，光标停留 |
| `Alt+Enter`   | 运行当前单元格，下方新增一格 |

也可点击单元格左侧 ▶️ 运行按钮。

### 3. Markdown 单元格（写笔记）
单元格右上角下拉，把 `Code` 切换为 `Markdown`，输入 Markdown 语法，`Shift+Enter` 渲染。

---

## 五、常见报错快速修复

1. **Failed to start the Kernel 内核启动失败**
   ```bash
   pip uninstall ipykernel -y
   pip install ipykernel
   python -m ipykernel install --user
   ```
2. **运行无输出、内核一直 Busy**
   `Ctrl+Shift+P` → `Jupyter: Restart Kernel and Clear All Outputs` 重启内核。
3. **打开 .ipynb 是纯文本，没有运行按钮**
   右键文件 → Open With → 选择 **Jupyter Notebook Editor**。
4. **模块找不到（ModuleNotFoundError）**
   确认右上角内核是安装过该库的 Python 环境，不要选错解释器。

---

## 六、常用附加功能
1. **导出文件**：右上角「导出」，支持 py / html / pdf / md
2. **变量查看**：侧边栏「变量」面板，实时查看单元格变量
3. **调试代码**：单元格左侧虫子图标，逐行断点调试
4. **清理输出**：单格清空 / 全部清空输出

---

## 关键操作 / 文件改动
- 新增本教程文档：`doc/2026-07-11-165620-vscode-jupyter-notebook-完整教程.md`

## 后续 TODO
- 如需，用户可要求提供一段可直接复制的完整测试代码（打印 / 数值计算 / 绘图 / pandas 表格等）。
