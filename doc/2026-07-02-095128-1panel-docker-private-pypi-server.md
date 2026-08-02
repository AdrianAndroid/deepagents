# 1Panel Docker 部署私有 PyPI 服务器

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-02T09:51:28+08:00
- Project: deepagents

## Prompt

如何在我的云服务器上,使用1panel的docker创建一个pypi私有服务器

## AI Response

推荐用 `pypiserver` 容器部署，最轻量，适合分发你的 `deepagents-code` wheel 包。

## 方案：1Panel Docker 部署 pypiserver

### 1. 在服务器创建目录

```bash
mkdir -p /opt/pypiserver/packages
mkdir -p /opt/pypiserver/auth
```

包文件放这里：

```text
/opt/pypiserver/packages
```

### 2. 上传 wheel 包

本地执行：

```bash
scp libs/code/dist/deepagents_code-0.1.24-py3-none-any.whl root@服务器IP:/opt/pypiserver/packages/
scp libs/code/dist/deepagents_code-0.1.24.tar.gz root@服务器IP:/opt/pypiserver/packages/
```

### 3. 创建账号密码文件

进入服务器：

```bash
docker run --rm httpd:2.4-alpine htpasswd -nbB 用户名 密码 > /opt/pypiserver/auth/.htpasswd
```

例如：

```bash
docker run --rm httpd:2.4-alpine htpasswd -nbB dcode StrongPassword123 > /opt/pypiserver/auth/.htpasswd
```

### 4. 在 1Panel 创建容器

1Panel 路径：

```text
容器 -> 创建容器
```

配置：

- 镜像：`pypiserver/pypiserver:latest`
- 容器名：`pypiserver`
- 端口映射：`8080:8080`
- 重启策略：`always`

挂载目录：

```text
/opt/pypiserver/packages -> /data/packages
/opt/pypiserver/auth/.htpasswd -> /data/.htpasswd
```

启动命令 / Command：

```bash
run -P . -a update,download,list -p /data/.htpasswd /data/packages
```

### 5. 反向代理域名

在 1Panel：

```text
网站 -> 创建网站 -> 反向代理
```

域名示例：

```text
pypi.example.com
```

代理地址：

```text
http://127.0.0.1:8080
```

开启 HTTPS。

### 6. 用户安装方式

```bash
pip install --index-url https://用户名:密码@pypi.example.com/simple/ deepagents-code
```

如果证书或内网域名有问题，可临时加：

```bash
pip install --index-url https://用户名:密码@pypi.example.com/simple/ deepagents-code --trusted-host pypi.example.com
```

### 7. 使用 uv 安装

```bash
uv tool install -U --index-url https://用户名:密码@pypi.example.com/simple/ deepagents-code
```

带 Python 版本：

```bash
uv tool install -U --python 3.13 --index-url https://用户名:密码@pypi.example.com/simple/ deepagents-code
```

### 8. 发布新版本

本地构建：

```bash
cd libs/code
uv build
```

上传新包：

```bash
scp dist/deepagents_code-0.1.25* root@服务器IP:/opt/pypiserver/packages/
```

pypiserver 会自动识别目录中的新包，通常不需要重启。

用户升级：

```bash
uv tool install -U --index-url https://用户名:密码@pypi.example.com/simple/ deepagents-code
```

### 9. 安全建议

- 必须开启 HTTPS。
- 密码不要放进公开文档。
- 推荐用 1Panel 防火墙限制访问 IP。
- 内部分发时建议只允许公司出口 IP 或 VPN 网段访问。
- 不建议开放匿名上传，只允许认证用户下载和上传。
