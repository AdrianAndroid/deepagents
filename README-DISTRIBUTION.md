# dcode 0.1.24 分发文件

本目录文件用于上传到 1Panel 静态下载站。

## 文件

- `deepagents_code-0.1.24-py3-none-any.whl`：Python wheel 安装包
- `deepagents_code-0.1.24.tar.gz`：源码分发包
- `install.sh`：macOS / Linux 安装脚本
- `install.ps1`：Windows PowerShell 安装脚本
- `uninstall.sh`：macOS / Linux 卸载脚本
- `uninstall.ps1`：Windows PowerShell 卸载脚本

## macOS / Linux 安装

```bash
curl -fsSL https://download.example.com/dcode/latest/install.sh | bash
```

## Windows 安装

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://download.example.com/dcode/latest/install.ps1 | iex"
```

## macOS / Linux 卸载

```bash
curl -fsSL https://download.example.com/dcode/latest/uninstall.sh | bash
```

连用户数据一起删除：

```bash
DCODE_REMOVE_DATA=1 curl -fsSL https://download.example.com/dcode/latest/uninstall.sh | bash
```

## Windows 卸载

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://download.example.com/dcode/latest/uninstall.ps1 | iex"
```

连用户数据一起删除：

```powershell
$env:DCODE_REMOVE_DATA="1"
powershell -ExecutionPolicy Bypass -c "irm https://download.example.com/dcode/latest/uninstall.ps1 | iex"
```

## 上传到 1Panel

```bash
scp libs/code/dist/deepagents_code-0.1.24* install.sh install.ps1 uninstall.sh uninstall.ps1 README-DISTRIBUTION.md root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
```

同步 latest：

```bash
ssh root@服务器IP 'rm -rf /opt/1panel/www/sites/download/dcode/latest.tmp && cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.24 /opt/1panel/www/sites/download/dcode/latest.tmp && mv -Tf /opt/1panel/www/sites/download/dcode/latest.tmp /opt/1panel/www/sites/download/dcode/latest'
```
