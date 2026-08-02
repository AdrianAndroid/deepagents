# Explain Pypiserver Package Already Exists

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-02T13:59:19+08:00
- Project: deepagents

## Prompt

用户执行 `twine upload --repository-url http://8.152.204.58:40001/ -u admin -p 123456 deepagents_code-0.1.24-py3-none-any.whl --verbose`，返回 `400 Bad Request`，提示：

```text
Package 'deepagents_code-0.1.24-py3-none-any.whl' already exists!
You may start server with `--overwrite` option.
```

## AI Response

这不是上传失败，而是包已经上传成功过了。`pypiserver` 默认不允许覆盖同名文件，所以第二次上传同一个 `deepagents_code-0.1.24-py3-none-any.whl` 会返回 400。

处理方式：

1. 不需要重复上传，直接安装测试：

```bash
pip install --index-url http://admin:123456@8.152.204.58:40001/simple/ deepagents-code==0.1.24 --trusted-host 8.152.204.58
```

或：

```bash
uv tool install -U --python 3.13 --index-url http://admin:123456@8.152.204.58:40001/simple/ deepagents-code==0.1.24
```

2. 如果确实要覆盖同版本包，有两种方式：

- 删除服务器包目录里的旧文件后重新上传：

```bash
rm /opt/pypiserver/packages/deepagents_code-0.1.24-py3-none-any.whl
```

- 或启动 pypiserver 时增加 `--overwrite`，但不推荐长期打开，容易误覆盖历史版本。

3. 正常发布流程应该 bump 版本，例如 `0.1.25`，重新构建后上传新文件，而不是覆盖 `0.1.24`。
