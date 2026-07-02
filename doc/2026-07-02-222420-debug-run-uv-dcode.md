# Debug Run Uv Dcode

- Time: 2026-07-02T22:24:20+08:00
- Project: deepagents

## Prompt

如何直接debug运行,uv run dcode<environment_details>
Current time: 2026-07-02T22:24:20+08:00
Working directory: /Users/zhaojian/code/deepagents
Workspace root folder: /Users/zhaojian/code/deepagents
Open tabs:
  doc/2026-07-01-195709-dcode-uninstall-commands.md
  doc/dcode二次开发版本分发与1Panel部署指南.md
  doc/2026-07-01-140631-configure-custom-compatible-api-base-url.md
  libs/code/tests/unit_tests/conftest.py
  libs/code/deepagents_code/model_config.py
  libs/code/deepagents_code/_env_vars.py
  libs/code/doc/private_pypi_setup_guide.md
  doc/2026-07-01-195608-windows-install-script-for-dcode-distribution.md
  .mcp.json
</environment_details>

## AI Response

在 `libs/code` 包目录运行：

```bash
cd /Users/zhaojian/code/deepagents/libs/code
DEEPAGENTS_CODE_DEBUG=1 DEEPAGENTS_CODE_DEBUG_FILE=/tmp/dcode.log uv run dcode
```

如果在仓库根目录运行，用：

```bash
DEEPAGENTS_CODE_DEBUG=1 DEEPAGENTS_CODE_DEBUG_FILE=/tmp/dcode.log uv --directory libs/code run dcode
```

看日志：

```bash
less /tmp/dcode.log
```

如果要断点调试：

```bash
cd /Users/zhaojian/code/deepagents/libs/code
uv run python -m debugpy --listen 5678 --wait-for-client -m deepagents_code
```