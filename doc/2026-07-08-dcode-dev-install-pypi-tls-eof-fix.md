# 2026-07-08 dcode-dev 安装 pypi TLS 握手失败修复

## 问题现象

运行 `run-dcode-dev.ps1` 或 `dcode-dev.ps1` 时报错：

```
error: Request failed after 3 retries in 23.9s
  Caused by: Failed to fetch: `https://pypi.org/simple/langchain/`
  Caused by: error sending request for url (https://pypi.org/simple/langchain/)
  Caused by: client error (Connect)
  Caused by: tls handshake eof
[X] 安装后未找到 C:\Users\Administrator\AppData\Local\dcode-dev\Scripts\dcode.exe，安装失败
```

## 根因

`uv pip install` 直连 `pypi.org` 时 TLS 握手在传输层被切断（EOF），依赖没装上，导致 venv 里没有 `dcode.exe`。后续 "安装后未找到 dcode.exe" 只是表象，真因在上面的网络错误。

## 修复方案（已落地）

在两个脚本里持久化清华 TUNA PyPI 镜像，并加装失败即刻退出的检查。

- `libs/code/dcode-dev.ps1`
- `libs/code/run-dcode-dev.ps1`

关键改动：

```powershell
$IndexUrl = if ($env:UV_INDEX_URL) { $env:UV_INDEX_URL } else { "https://pypi.tuna.tsinghua.edu.cn/simple" }
& uv pip install --python $Python --index-url $IndexUrl -e $ScriptDir --upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Error "uv pip install 失败 (exit $LASTEXITCODE)"
    exit $LASTEXITCODE
}
```

- 通过 `$env:UV_INDEX_URL` 可临时切换到其他源（阿里、豆瓣等）。
- 安装失败直接 `exit`，不再走 "找不到 dcode.exe" 的误导分支。

## 使用

```powershell
# 默认走清华源
D:\deepagents\libs\code\run-dcode-dev.ps1

# 或切换镜像
$env:UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple"
D:\deepagents\libs\code\run-dcode-dev.ps1
```

## 备选镜像

- 清华 TUNA：`https://pypi.tuna.tsinghua.edu.cn/simple`
- 阿里云：`https://mirrors.aliyun.com/pypi/simple`
- 腾讯云：`https://mirrors.cloud.tencent.com/pypi/simple`
- 中科大：`https://pypi.mirrors.ustc.edu.cn/simple`
