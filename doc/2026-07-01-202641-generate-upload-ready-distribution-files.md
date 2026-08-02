# Generate Upload Ready Distribution Files

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T20:26:41+08:00
- Project: deepagents

## Prompt

ERROR: Cannot read "image.png" (this model does not support image input). Inform the user.生成这几个文件,方便我上传.<environment_details>
Current time: 2026-07-01T20:26:41+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
</environment_details>

## AI Response

已在项目根目录生成可上传到 1Panel 下载站的分发文件：

- `install.sh`
- `install.ps1`
- `uninstall.sh`
- `uninstall.ps1`
- `README-DISTRIBUTION.md`

并已给 shell 脚本增加可执行权限：

```bash
chmod +x install.sh uninstall.sh
```

文件用途：

- `install.sh`：macOS / Linux 安装脚本，自动安装 uv、下载 wheel、执行 `uv tool install -U`。
- `install.ps1`：Windows PowerShell 安装脚本。
- `uninstall.sh`：macOS / Linux 卸载脚本。
- `uninstall.ps1`：Windows PowerShell 卸载脚本。
- `README-DISTRIBUTION.md`：上传目录说明和用户安装/卸载命令。

上传命令示例：

```bash
scp libs/code/dist/deepagents_code-0.1.24* install.sh install.ps1 uninstall.sh uninstall.ps1 README-DISTRIBUTION.md root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
```

同步 latest：

```bash
ssh root@服务器IP 'rm -rf /opt/1panel/www/sites/download/dcode/latest.tmp && cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.24 /opt/1panel/www/sites/download/dcode/latest.tmp && mv -Tf /opt/1panel/www/sites/download/dcode/latest.tmp /opt/1panel/www/sites/download/dcode/latest'
```

注意：脚本默认下载域名是 `https://download.example.com`，上传前需要把脚本和 README 中的 `download.example.com` 替换成你的真实下载域名。
