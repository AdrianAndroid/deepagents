# Explain Editable Dcode Dev Commands

- Time: 2026-07-01T14:23:23+08:00
- Project: deepagents

## Prompt

Called the Read tool with the following input: {"filePath":"/Users/zhaojian/Desktop/deepagents/doc/2026-07-01-141457-run-local-editable-dcode-dev.md"}<path>/Users/zhaojian/Desktop/deepagents/doc/2026-07-01-141457-run-local-editable-dcode-dev.md</path>
<type>file</type>
<content>
1: # Run Local Editable Dcode Dev
2: 
3: - Time: 2026-07-01T14:14:57+08:00
4: - Project: deepagents
5: 
6: ## Prompt
7: 
8: 如何在其它目录的终端下直接执行这个项目, 我想一边真实使用, 一边二次开发,二次开发完再使用
9: 
10: ## AI Response
11: 
12: 推荐用项目自带的 `dcode-dev` 可编辑安装：
13: 
14: ```bash
15: uv venv ~/.local/share/dcode-dev --python 3.13
16: uv pip install --python ~/.local/share/dcode-dev/bin/python -e /Users/zhaojian/Desktop/deepagents/libs/code
17: ln -sf ~/.local/share/dcode-dev/bin/dcode ~/.local/bin/dcode-dev
18: ```
19: 
20: 之后任意目录运行 `dcode-dev`；改完源码后重启 `dcode-dev` 即生效。依赖变更后再执行：
21: ```bash
22: uv pip install --python ~/.local/share/dcode-dev/bin/python -e /Users/zhaojian/Desktop/deepagents/libs/code --upgrade
23: ```

(End of file - total 23 lines)
</content>@doc/2026-07-01-141457-run-local-editable-dcode-dev.md 
详细解释一下这个文档的命令
精简一套可真实使用的命令<environment_details>
Current time: 2026-07-01T14:23:23+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: doc/2026-07-01-141457-run-local-editable-dcode-dev.md
Visible files:
  doc/2026-07-01-141457-run-local-editable-dcode-dev.md
Open tabs:
  doc/2026-07-01-141457-run-local-editable-dcode-dev.md
</environment_details>

## AI Response

## 命令解释

- `uv venv ~/.local/share/dcode-dev --python 3.13`：在用户目录创建一个独立 Python 虚拟环境，专门给开发版 `dcode-dev` 使用，不污染项目自身 `.venv`，也不影响正式版 `dcode`。
- `uv pip install --python ~/.local/share/dcode-dev/bin/python -e /Users/zhaojian/Desktop/deepagents/libs/code`：把当前源码目录 `libs/code` 以 editable 模式安装进这个虚拟环境。源码改动后不用重新安装，重启命令即可用新代码。
- `ln -sf ~/.local/share/dcode-dev/bin/dcode ~/.local/bin/dcode-dev`：创建一个全局可执行命令 `dcode-dev`，实际指向开发虚拟环境里的 `dcode`。
- `uv pip install ... --upgrade`：当 `pyproject.toml` 里的依赖变化时，重新解析并升级开发虚拟环境依赖。

## 精简可用版

```bash
mkdir -p ~/.local/bin
uv venv ~/.local/share/dcode-dev
uv pip install --python ~/.local/share/dcode-dev/bin/python -e /Users/zhaojian/Desktop/deepagents/libs/code
ln -sf ~/.local/share/dcode-dev/bin/dcode ~/.local/bin/dcode-dev
```

使用：

```bash
dcode-dev
```

如果提示找不到 `dcode-dev`，执行：

```bash
export PATH="$HOME/.local/bin:$PATH"
```
