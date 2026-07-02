# 1Panel 搭建私有 PyPI 完整指南
适用于 deepagents-code 私有更新源配置，全程可视化操作，兼容 pip/uv 所有包管理工具。
---
## 🚀 第一步：部署私有 PyPI 服务（基于 pypiserver）
### 1. 前置准备
- 云服务器已安装 1Panel（官方一键安装：`curl -sSL https://resource.fit2cloud.com/1panel/package/quick_start.sh | sudo bash`）
- 域名解析到云服务器公网IP：比如 `pypi.yourdomain.com`
- 安全组放开端口：`80`/`443`/`12480`（1Panel后台）/`9200`（pypiserver服务）
### 2. 创建存储目录
1Panel → 【文件】→ 在 `/opt` 下创建目录结构：
```
/opt/pypi
├── packages  # 存储所有上传的Python包
└── auth      # 存储认证密码文件
```
### 3. 生成认证密码
1Panel → 【终端】执行：
```bash
# CentOS/RHEL 安装 htpasswd
yum install -y httpd-tools
# Debian/Ubuntu 安装
# apt install -y apache2-utils
# 生成密码文件，用户名为admin，执行后输入自定义密码
htpasswd -c /opt/pypi/auth/.htpasswd admin
```
### 4. Docker 部署 pypiserver
1. 1Panel → 【容器】→【镜像】→ 拉取：`pypiserver/pypiserver:latest`
2. 【创建容器】配置：
| 配置项 | 值 |
|--------|----|
| 容器名称 | pypiserver |
| 镜像 | pypiserver/pypiserver:latest |
| 端口映射 | 宿主机`9200` → 容器`8080` |
| 目录挂载1 | 宿主机`/opt/pypi/packages` → 容器`/data/packages`（读写） |
| 目录挂载2 | 宿主机`/opt/pypi/auth/.htpasswd` → 容器`/data/.htpasswd`（只读） |
| 启动命令 | `-p 8080 -P .htpasswd -a update,download packages` |
| 重启策略 | Always |
3. 点击创建，启动后访问 `http://服务器IP:9200` 看到欢迎页即为成功。
---
## 🌐 第二步：配置域名与 HTTPS
1. 1Panel → 【网站】→【反向代理】→【添加】：
   - 主域名：`pypi.yourdomain.com`
   - 代理地址：`http://127.0.0.1:9200`
   - 其他默认，确认创建
2. 反向代理列表 → 点击对应行的【SSL】→ 选择【Let's Encrypt】→ 申请证书并开启强制HTTPS跳转。
现在访问 `https://pypi.yourdomain.com` 即可访问私有源。
---
## 📦 第三步：打包上传 deepagents-code
### 1. 本地打包
进入 `deepagents/libs/code` 目录执行：
```bash
# 安装build工具（已安装跳过）
uv add --dev build
# 打包，产物在dist目录下
uv build
```
生成文件：
- `deepagents-code-<版本号>.tar.gz`（源码包）
- `deepagents_code-<版本号>-py3-none-any.whl`（二进制包）
### 2. 上传到私有源
#### 方式一：twine 上传（推荐）
```bash
# 安装twine
uv add --dev twine
# 上传，输入刚才设置的admin账号密码
twine upload --repository-url https://pypi.yourdomain.com dist/*
```
#### 方式二：手动上传
直接把dist目录下的两个文件上传到云服务器 `/opt/pypi/packages` 目录，pypiserver自动识别。
### 3. 验证上传
访问 `https://pypi.yourdomain.com/simple/deepagents-code/` 能看到上传的版本即为成功。
---
## ⚙️ 第四步：dcode 适配私有源
### 1. 修改版本检查接口
编辑 `deepagents_code/_version.py`：
```python
# 官方源（修改前）
# PYPI_URL = "https://pypi.org/pypi/deepagents-code/json"
# 私有源（修改后，注意路径没有/pypi前缀！）
PYPI_URL = "https://pypi.yourdomain.com/deepagents-code/json"
```
### 2. 修改升级命令（可选，未配置全局源时需要）
编辑 `deepagents_code/update_check.py`：
```python
_UPGRADE_COMMANDS: dict[InstallMethod, str] = {
    # 加上私有源地址，不需要认证则去掉用户名密码部分
    "uv": "uv tool install -U deepagents-code --index-url https://admin:你的密码@pypi.yourdomain.com/simple --extra-index-url https://pypi.org/simple",
    "brew": "brew upgrade deepagents-code",
}
```
> `--extra-index-url` 用于依赖包从官方源 fallback，避免私有源缺少依赖导致安装失败。
### 3. 重新打包上传
- 升级版本号：修改 `_version.py` 中 `__version__` 和 `pyproject.toml` 中 `version`（比如从`0.1.24`→`0.1.25`）
- 重新执行第三步的打包上传流程
---
## 🧪 第五步：本地环境配置与测试
### 1. uv 全局配置私有源（推荐）
编辑 `~/.config/uv/config.toml`（Windows：`%APPDATA%\uv\config.toml`）：
```toml
[indices]
private = { url = "https://pypi.yourdomain.com/simple", priority = "default" }
pypi = { url = "https://pypi.org/simple", priority = "fallback" }
[credentials]
private = { username = "admin", password = "你的密码" }
```
### 2. 安装私有源 dcode
```bash
uv tool install deepagents-code
```
### 3. 测试更新
启动 dcode 输入 `/update`，会从私有源检查并安装新版本。
---
## 📌 常见问题
| 问题 | 解决方案 |
|------|----------|
| 版本检查返回404 | 检查`PYPI_URL`路径，pypiserver 路径是 `https://域名/包名/json`，没有`/pypi`前缀 |
| 升级时依赖找不到 | 升级命令加`--extra-index-url https://pypi.org/simple`，或全局配置官方源为 fallback |
| 未授权访问 | 确认启动命令加了`-P .htpasswd -a update,download`参数，密码输入正确 |
| 备份私有源 | 直接备份云服务器 `/opt/pypi/packages` 目录即可 |
