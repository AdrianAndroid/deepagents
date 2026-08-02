# dcode 二次开发版本构建、1Panel 分发、安装、升级与卸载指南

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T19:59:43+08:00
- Project: deepagents

## Prompt

总结上述会话,写一个总结文档,要详细一下,包括:
1. 如何构建whl
2. 如何上传到有1panel的服务器
3. 如何下载
4. 如何卸载
5. 如何想正常上线的安装包一样升级

## AI Response

已整理成本指南。

## 一、总体方案

目标：把二次开发后的 `deepagents-code` / `dcode` 打包成 Python wheel，然后通过部署了 1Panel 的云服务器作为下载分发平台。

推荐第一阶段采用：

```text
1Panel 静态网站 + 版本目录 + latest 目录 + install.sh/install.ps1
```

原因：

- 实现最快，不需要先搭私有 PyPI。
- 用户可以像安装普通 CLI 工具一样一键安装。
- 后续升级只需要上传新版本并切换 `latest`。
- 可以保留历史版本，方便回滚。
- 后续如果团队需要 `pip install` 风格，可以再升级为私有 PyPI。

最终用户安装体验：

macOS / Linux：

```bash
curl -fsSL http://8.152.204.58:40000/download/dcode/latest/install.sh | bash
```

Windows PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -c "irm http://8.152.204.58:40000/download/dcode/latest/install.ps1 | iex"
```

卸载体验：

```bash
uv tool uninstall deepagents-code
```

---

## 二、如何构建 whl

### 1. 进入 `deepagents-code` 包目录

本仓库是 monorepo，`deepagents-code` 位于：

```text
libs/code
```

执行：

```bash
cd /Users/zhaojian/Desktop/deepagents/libs/code
```

### 2. 确认版本号

版本号在：

```text
libs/code/pyproject.toml
```

例如：

```toml
[project]
name = "deepagents-code"
version = "0.1.24"
```

构建产物文件名会根据这个版本号生成，例如：

```text
deepagents_code-0.1.24-py3-none-any.whl
deepagents_code-0.1.24.tar.gz
```

如果要发布新版本，例如 `0.1.25`，需要先修改 `pyproject.toml` 中的版本号，再构建。

### 3. 构建前建议先跑测试

```bash
make test
```

当前会运行：

```bash
uv run --group test pytest -n auto --benchmark-disable --disable-socket --allow-unix-socket tests/unit_tests/ --cov=deepagents_code --cov-report=term-missing
```

之前验证结果：

```text
6896 passed
```

### 4. 构建 wheel 和源码包

在 `libs/code` 下执行：

```bash
uv build
```

成功后会生成：

```text
libs/code/dist/deepagents_code-0.1.24-py3-none-any.whl
libs/code/dist/deepagents_code-0.1.24.tar.gz
```

其中：

- `.whl`：推荐给用户安装使用。
- `.tar.gz`：源码分发包，主要用于源码构建、排查问题或兼容特殊环境。

---

## 三、如何上传到有 1Panel 的服务器

### 1. 在 1Panel 创建静态网站

进入 1Panel：

```text
网站 -> 创建网站 -> 静态网站
```

建议绑定域名，例如：

```text
http://8.152.204.58:40000/download
```

开启 HTTPS 证书。

假设网站根目录为：

```text
/opt/1panel/www/sites/download
```

实际路径以你的 1Panel 网站设置为准。

### 2. 推荐目录结构

服务器上建议使用如下结构：

```text
/opt/1panel/www/sites/download/
└── dcode/
    ├── latest/
    │   ├── deepagents_code-0.1.24-py3-none-any.whl
    │   ├── deepagents_code-0.1.24.tar.gz
    │   ├── install.sh
    │   ├── install.ps1
    │   ├── uninstall.sh
    │   └── uninstall.ps1
    └── releases/
        └── 0.1.24/
            ├── deepagents_code-0.1.24-py3-none-any.whl
            ├── deepagents_code-0.1.24.tar.gz
            ├── install.sh
            ├── install.ps1
            ├── uninstall.sh
            └── uninstall.ps1
```

设计原则：

- `releases/0.1.24/`：固定版本目录，发布后不要覆盖。
- `latest/`：当前推荐版本，用户默认从这里安装。
- 升级时新增 `releases/0.1.25/`，测试通过后再切换 `latest`。

### 3. 创建版本目录

服务器执行：

```bash
mkdir -p /opt/1panel/www/sites/download/dcode/releases/0.1.24
```

### 4. 上传构建产物

本地执行：

```bash
scp /Users/zhaojian/Desktop/deepagents/libs/code/dist/deepagents_code-0.1.24-py3-none-any.whl root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
scp /Users/zhaojian/Desktop/deepagents/libs/code/dist/deepagents_code-0.1.24.tar.gz root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
```

如果有脚本：

```bash
scp install.sh uninstall.sh root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
scp install.ps1 uninstall.ps1 root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
```

### 5. 同步 latest

服务器执行：

```bash
rm -rf /opt/1panel/www/sites/download/dcode/latest
cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.24 /opt/1panel/www/sites/download/dcode/latest
```

更安全的原子切换方式：

```bash
rm -rf /opt/1panel/www/sites/download/dcode/latest.tmp
cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.24 /opt/1panel/www/sites/download/dcode/latest.tmp
mv -Tf /opt/1panel/www/sites/download/dcode/latest.tmp /opt/1panel/www/sites/download/dcode/latest
```

macOS 本地 `mv -T` 不一定可用，但服务器如果是 Linux 一般可用。

---

## 四、如何下载安装

### 1. 直接下载 wheel

用户可以直接访问：

```text
https://download.example.com/dcode/latest/deepagents_code-0.1.24-py3-none-any.whl
```

或固定版本：

```text
https://download.example.com/dcode/releases/0.1.24/deepagents_code-0.1.24-py3-none-any.whl
```

手动安装：

```bash
pip install deepagents_code-0.1.24-py3-none-any.whl
```

但更推荐使用 `uv tool install`，因为 `dcode` 是 CLI 工具。

### 2. macOS / Linux 一键安装脚本 `install.sh`

建议内容：

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${DCODE_VERSION:-0.1.24}"
BASE_URL="${DCODE_BASE_URL:-https://download.example.com/dcode/releases/${VERSION}}"
WHEEL="deepagents_code-${VERSION}-py3-none-any.whl"
PYTHON="${DCODE_PYTHON:-3.13}"

if ! command -v uv >/dev/null 2>&1; then
  curl -fsSL https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

curl -fL "${BASE_URL}/${WHEEL}" -o "${tmp}/${WHEEL}"

uv tool install -U --python "$PYTHON" "${tmp}/${WHEEL}"

if command -v dcode >/dev/null 2>&1; then
  dcode --version
else
  deepagents-code --version
fi

echo "dcode ${VERSION} installed successfully"
```

用户执行：

```bash
curl -fsSL https://download.example.com/dcode/latest/install.sh | bash
```

安装指定版本：

```bash
DCODE_VERSION=0.1.24 DCODE_BASE_URL=https://download.example.com/dcode/releases/0.1.24 \
  curl -fsSL https://download.example.com/dcode/releases/0.1.24/install.sh | bash
```

### 3. Windows 一键安装脚本 `install.ps1`

建议内容：

```powershell
$ErrorActionPreference = "Stop"

$Version = if ($env:DCODE_VERSION) { $env:DCODE_VERSION } else { "0.1.24" }
$BaseUrl = if ($env:DCODE_BASE_URL) { $env:DCODE_BASE_URL } else { "https://download.example.com/dcode/releases/$Version" }
$Wheel = "deepagents_code-$Version-py3-none-any.whl"
$Python = if ($env:DCODE_PYTHON) { $env:DCODE_PYTHON } else { "3.13" }

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

$TempDir = New-Item -ItemType Directory -Force -Path ([System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "dcode-install"))
$WheelPath = Join-Path $TempDir $Wheel

Invoke-WebRequest "$BaseUrl/$Wheel" -OutFile $WheelPath
uv tool install -U --python $Python $WheelPath

dcode --version
Write-Host "dcode $Version installed successfully"
```

用户执行：

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://download.example.com/dcode/latest/install.ps1 | iex"
```

---

## 五、如何卸载

如果使用 `uv tool install` 安装，卸载非常简单。

### 1. macOS / Linux 手动卸载

```bash
uv tool uninstall deepagents-code
```

验证：

```bash
dcode --version
```

如果卸载成功，应提示命令不存在，或者不再显示版本。

可选清理用户数据：

```bash
rm -rf ~/.cache/deepagents-code ~/.config/deepagents-code ~/.local/share/deepagents-code
```

### 2. macOS / Linux `uninstall.sh`

建议内容：

```bash
#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv tool uninstall deepagents-code || true
else
  echo "uv not found; if dcode was installed another way, remove it manually."
fi

if [ "${DCODE_REMOVE_DATA:-0}" = "1" ]; then
  rm -rf ~/.cache/deepagents-code ~/.config/deepagents-code ~/.local/share/deepagents-code
  echo "Removed deepagents-code user data."
fi

echo "dcode uninstalled."
```

用户执行：

```bash
curl -fsSL https://download.example.com/dcode/latest/uninstall.sh | bash
```

连用户数据一起清理：

```bash
DCODE_REMOVE_DATA=1 curl -fsSL https://download.example.com/dcode/latest/uninstall.sh | bash
```

### 3. Windows 手动卸载

```powershell
uv tool uninstall deepagents-code
```

可选清理用户数据：

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\deepagents-code" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\deepagents-code" -ErrorAction SilentlyContinue
```

### 4. Windows `uninstall.ps1`

建议内容：

```powershell
$ErrorActionPreference = "Stop"

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool uninstall deepagents-code
} else {
    Write-Host "uv not found; if dcode was installed another way, remove it manually."
}

if ($env:DCODE_REMOVE_DATA -eq "1") {
    Remove-Item -Recurse -Force "$env:LOCALAPPDATA\deepagents-code" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "$env:APPDATA\deepagents-code" -ErrorAction SilentlyContinue
    Write-Host "Removed deepagents-code user data."
}

Write-Host "dcode uninstalled."
```

用户执行：

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://download.example.com/dcode/latest/uninstall.ps1 | iex"
```

---

## 六、如何像正式上线安装包一样升级

核心思想：

```text
固定版本目录不可变，latest 目录代表当前稳定版。
```

### 1. 发布新版本流程

假设从 `0.1.24` 升级到 `0.1.25`。

#### 步骤 1：修改版本号

编辑：

```text
libs/code/pyproject.toml
```

修改：

```toml
version = "0.1.25"
```

如项目中还有 `_version.py` 或版本同步检查，也要保持一致。

#### 步骤 2：测试

```bash
cd /Users/zhaojian/Desktop/deepagents/libs/code
make test
```

#### 步骤 3：构建

```bash
uv build
```

生成：

```text
dist/deepagents_code-0.1.25-py3-none-any.whl
dist/deepagents_code-0.1.25.tar.gz
```

#### 步骤 4：上传到新版本目录

服务器创建目录：

```bash
ssh root@服务器IP 'mkdir -p /opt/1panel/www/sites/download/dcode/releases/0.1.25'
```

上传：

```bash
scp dist/deepagents_code-0.1.25* root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.25/
scp install.sh install.ps1 uninstall.sh uninstall.ps1 root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.25/
```

#### 步骤 5：先测试固定版本链接

macOS / Linux：

```bash
DCODE_VERSION=0.1.25 DCODE_BASE_URL=https://download.example.com/dcode/releases/0.1.25 \
  curl -fsSL https://download.example.com/dcode/releases/0.1.25/install.sh | bash
```

Windows：

```powershell
$env:DCODE_VERSION="0.1.25"
$env:DCODE_BASE_URL="https://download.example.com/dcode/releases/0.1.25"
powershell -ExecutionPolicy Bypass -c "irm https://download.example.com/dcode/releases/0.1.25/install.ps1 | iex"
```

#### 步骤 6：确认没问题后切换 latest

服务器执行：

```bash
rm -rf /opt/1panel/www/sites/download/dcode/latest.tmp
cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.25 /opt/1panel/www/sites/download/dcode/latest.tmp
mv -Tf /opt/1panel/www/sites/download/dcode/latest.tmp /opt/1panel/www/sites/download/dcode/latest
```

### 2. 用户升级方式

用户不需要知道具体版本，只需要重复执行安装命令：

macOS / Linux：

```bash
curl -fsSL https://download.example.com/dcode/latest/install.sh | bash
```

Windows：

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://download.example.com/dcode/latest/install.ps1 | iex"
```

因为脚本内部使用：

```bash
uv tool install -U
```

所以会自动升级已有安装。

### 3. 回滚方式

如果 `0.1.25` 有问题，要回滚到 `0.1.24`：

```bash
rm -rf /opt/1panel/www/sites/download/dcode/latest.tmp
cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.24 /opt/1panel/www/sites/download/dcode/latest.tmp
mv -Tf /opt/1panel/www/sites/download/dcode/latest.tmp /opt/1panel/www/sites/download/dcode/latest
```

然后通知用户重新执行安装命令即可：

```bash
curl -fsSL https://download.example.com/dcode/latest/install.sh | bash
```

### 4. 版本保留策略

建议至少保留最近 3-5 个版本：

```text
releases/0.1.23
releases/0.1.24
releases/0.1.25
latest -> 当前稳定版本内容
```

不要直接覆盖旧版本目录，否则无法精准回滚。

---

## 七、1Panel 上的安全建议

1. 必须开启 HTTPS，避免安装包被中间人篡改。
2. 内部分发建议加访问控制：
   - 1Panel 网站密码访问
   - IP 白名单
   - VPN / 内网域名
3. 不建议直接开放目录列表，除非确实需要。
4. 每个版本可以额外提供 checksum 文件：

```bash
shasum -a 256 deepagents_code-0.1.24-py3-none-any.whl > SHA256SUMS.txt
```

用户可校验：

```bash
shasum -a 256 -c SHA256SUMS.txt
```

5. 发布前先在干净机器上测试 `install.sh` / `install.ps1`。

---

## 八、后续可演进方案

### 方案 A：私有 PyPI

适合团队内部 Python 开发者使用：

```bash
pip install --index-url https://pypi.example.com/simple/ deepagents-code
```

可以在 1Panel 部署 `pypiserver`。

### 方案 B：Docker 镜像仓库

适合容器化运行：

```bash
docker run -it --rm registry.example.com/dcode:0.1.24
```

可以在 1Panel 部署 Harbor。

### 方案 C：SaaS 服务端

适合做成在线服务，用户只安装轻量客户端或通过浏览器访问。需要额外设计：

- 用户系统
- 鉴权
- 会话存储
- 任务隔离
- 模型密钥托管
- 沙箱安全

第一阶段不建议直接上 SaaS，先把 CLI 分发链路跑通。
