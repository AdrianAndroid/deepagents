# Run Local Editable Dcode Dev

- Time: 2026-07-01T14:14:57+08:00
- Project: deepagents

## Prompt

如何在其它目录的终端下直接执行这个项目, 我想一边真实使用, 一边二次开发,二次开发完再使用

## AI Response

推荐用项目自带的 `dcode-dev` 可编辑安装：

```bash
uv venv ~/.local/share/dcode-dev --python 3.13
uv pip install --python ~/.local/share/dcode-dev/bin/python -e /Users/zhaojian/Desktop/deepagents/libs/code
ln -sf ~/.local/share/dcode-dev/bin/dcode ~/.local/bin/dcode-dev
```

之后任意目录运行 `dcode-dev`；改完源码后重启 `dcode-dev` 即生效。依赖变更后再执行：
```bash
uv pip install --python ~/.local/share/dcode-dev/bin/python -e /Users/zhaojian/Desktop/deepagents/libs/code --upgrade
```
