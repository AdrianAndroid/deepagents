# Publish Built Package To 1Panel

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T19:43:23+08:00
- Project: deepagents

## Prompt

Successfully built dist/deepagents_code-0.1.24.tar.gz
Successfully built dist/deepagents_code-0.1.24-py3-none-any.whl

如何将这些产物发布到我的云服务器的1panel中<environment_details>
Current time: 2026-07-01T19:43:23+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/code/deepagents_code/config.py
Visible files:
  libs/code/deepagents_code/config.py
</environment_details>

## AI Response

推荐把 wheel 上传到服务器，然后在 1Panel 的终端或容器里安装。

本地上传：

```bash
scp libs/code/dist/deepagents_code-0.1.24-py3-none-any.whl root@你的服务器IP:/opt/deepagents/
```

服务器安装：

```bash
cd /opt/deepagents
python3 -m venv .venv
. .venv/bin/activate
pip install deepagents_code-0.1.24-py3-none-any.whl
```

验证：

```bash
deepagents-code --version
# 或
 dcode --version
```

如果要在 1Panel 中长期运行，建议用 1Panel 的“应用商店/容器/进程守护”创建一个 Python 容器或 Supervisor/OpenResty 反代服务，把启动命令设置为：

```bash
/opt/deepagents/.venv/bin/deepagents-code
```

如果只是发布 Python 包产物，优先上传 `.whl`；`.tar.gz` 主要用于源码分发或构建排查。
