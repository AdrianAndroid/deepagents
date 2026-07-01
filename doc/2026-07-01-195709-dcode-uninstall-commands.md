# Dcode Uninstall Commands

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T19:57:09+08:00
- Project: deepagents

## Prompt

如果用户不想用量了,如何卸载?<environment_details>
Current time: 2026-07-01T19:57:09+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: libs/cli/scripts/install.sh
Visible files:
  libs/cli/scripts/install.sh
Open tabs:
  doc/dcode二次开发版本分发与1Panel部署指南.md
  libs/cli/scripts/install.sh
</environment_details>

## AI Response

如果用 `uv tool install` 安装，卸载命令是：

```bash
uv tool uninstall deepagents-code
```

验证：

```bash
dcode --version
# 应该提示 command not found
```

可选清理缓存/配置：

```bash
rm -rf ~/.cache/deepagents-code ~/.config/deepagents-code ~/.local/share/deepagents-code
```

Windows PowerShell：

```powershell
uv tool uninstall deepagents-code
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\deepagents-code" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\deepagents-code" -ErrorAction SilentlyContinue
```

建议下载站同时提供 `uninstall.sh` 和 `uninstall.ps1`。
