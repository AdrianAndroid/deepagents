# VS Code 远程开发操作文档（Ubuntu 22.04 服务器）

> 场景：本地 VS Code（Windows / macOS / Linux）通过 SSH 直连远端 Ubuntu 22.04 服务器，直接编辑、运行、调试服务器上的源码，无需 FTP/SFTP 同步。

---

## 一、准备工作

### 1.1 服务器端（Ubuntu 22.04）要求

| 项目 | 要求 | 检查命令 |
| --- | --- | --- |
| 系统版本 | Ubuntu 22.04 LTS | `lsb_release -a` |
| SSH 服务 | openssh-server 已启动 | `systemctl status ssh` |
| 网络 | 22 端口对本地可达（或自定义端口） | `ss -tlnp | grep ssh` |
| 架构 | x86_64 / aarch64 | `uname -m` |
| 磁盘空间 | 用户家目录 ≥ 500MB（用于 vscode-server） | `df -h ~` |
| glibc | ≥ 2.28（Ubuntu 22.04 自带 2.35，满足） | `ldd --version` |

若 SSH 未安装或未启动：

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo ufw allow 22/tcp   # 如启用了防火墙
```

### 1.2 本地端要求

- VS Code 最新稳定版：<https://code.visualstudio.com/>
- 本地已生成 SSH 密钥对（下文会创建）

---

## 二、安装 VS Code Remote 插件

打开 VS Code → 左侧扩展商店（`Ctrl+Shift+X` / `Cmd+Shift+X`）→ 搜索并安装：

- **Remote Development**（微软官方合集，包含以下三件套）
  - Remote - SSH
  - Dev Containers
  - WSL

只做 SSH 远程连 Ubuntu，装 `Remote - SSH` 也可以，但推荐直接装合集，后续容器/WSL 场景都能覆盖。

---

## 三、配置 SSH 免密登录（推荐）

### 3.1 本地生成密钥（如已有可跳过）

**Windows PowerShell / macOS / Linux 终端：**

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 一路回车，密钥默认放在：
#   Windows: C:\Users\你的用户名\.ssh\id_ed25519(.pub)
#   macOS/Linux: ~/.ssh/id_ed25519(.pub)
```

> 如果需要兼容老服务器，可用 `ssh-keygen -t rsa -b 4096`。

### 3.2 上传公钥到 Ubuntu 服务器

**macOS / Linux / Windows 10+（自带 OpenSSH）：**

```bash
ssh-copy-id -p 22 ubuntu@你的服务器IP
# 首次会要求输入服务器密码，之后免密
```

**Windows 无 `ssh-copy-id` 时手动方式：**

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh ubuntu@你的服务器IP "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### 3.3 验证免密登录

```bash
ssh ubuntu@你的服务器IP
# 不再提示输入密码即成功
```

### 3.4（可选）加固服务器 SSH

编辑 `/etc/ssh/sshd_config`：

```conf
PermitRootLogin no          # 禁止 root 直接登录
PasswordAuthentication no   # 免密成功后关闭密码登录
PubkeyAuthentication yes
```

重启 SSH：

```bash
sudo systemctl restart ssh
```

⚠️ 关闭密码登录前，请务必先在**新终端**验证密钥登录可用，否则可能自锁。

---

## 四、VS Code 中配置远程主机

### 4.1 打开 SSH 配置文件

1. 点击 VS Code 左下角 绿色 `><` 图标（或左侧 "远程资源管理器"）
2. 选择 `Connect to Host...` → `Configure SSH Hosts...`
3. 选择本地用户的配置文件：
   - Windows：`C:\Users\你的用户名\.ssh\config`
   - macOS/Linux：`~/.ssh/config`

### 4.2 写入配置

以 Ubuntu 22 服务器为例：

```ssh-config
Host ubuntu-dev
  HostName 192.168.1.100          # 或公网 IP / 域名
  User ubuntu                     # 你在服务器上的用户名
  Port 22
  IdentityFile ~/.ssh/id_ed25519  # Windows 写 C:\Users\xxx\.ssh\id_ed25519
  ServerAliveInterval 30          # 每 30 秒发一次心跳，防止断线
  ServerAliveCountMax 3
  ForwardAgent yes                # 可选：把本地 ssh-agent 转发到服务器（如需 git 推送）
```

多台服务器：

```ssh-config
Host ubuntu-prod
  HostName 8.8.8.8
  User deploy
  Port 22022
  IdentityFile ~/.ssh/id_ed25519

Host ubuntu-test
  HostName 10.0.0.5
  User ubuntu
  Port 22
  IdentityFile ~/.ssh/id_ed25519
```

保存后 VS Code 左侧远程资源管理器会自动出现 `ubuntu-dev` 等主机。

---

## 五、连接远程服务器

1. 左侧远程资源管理器 → 找到 `ubuntu-dev` → 点击右侧 "在当前窗口连接" 或 "在新窗口连接"
2. 首次连接会做两件事：
   - 本地 VS Code 通过 SSH 登录服务器
   - 自动在服务器 `~/.vscode-server/` 下载并安装 vscode-server（约 100–200 MB）
3. 状态栏左下角显示 `SSH: ubuntu-dev` 即连接成功

### 打开远端项目

- 顶部菜单 `File → Open Folder...`
- 会弹出**服务器端**的目录树，选择你的项目目录（例如 `/home/ubuntu/projects/myapp`）
- VS Code 会在远端启动语言服务、Git 集成、终端等，所有操作都发生在服务器上

### 打开终端

- `Ctrl+`` `（反引号）或菜单 `Terminal → New Terminal`
- 这是**服务器上的 bash**，可以直接 `apt`, `git`, `python`, `docker` 等

---

## 六、开发常用能力

| 功能 | 使用方法 |
| --- | --- |
| 代码补全 / 跳转 | 在远端安装对应语言插件（如 Python / Go / C++），本地插件按需推送到远端 |
| 断点调试 | `Run → Add Configuration` 生成 `.vscode/launch.json`，直接对远端进程调试 |
| Git | 状态栏 / 源代码管理面板，直连服务器上的仓库 |
| 端口转发 | 底部 `PORTS` 面板 → `Forward a Port` 输入远端端口（如 `8080`），自动映射到 `localhost:8080` |
| 文件上传/下载 | 直接在 VS Code 资源管理器拖拽；或 `code --remote` 打开 |
| 设置同步 | 本地设置/主题/快捷键自动生效；远端仅同步必要插件 |

---

## 七、Ubuntu 22 服务器上常见开发环境准备

按需在服务器执行（首次连接后在 VS Code 集成终端里跑）：

```bash
# 基础
sudo apt update && sudo apt install -y build-essential git curl wget vim

# Python（22.04 自带 3.10；如需 3.12）
sudo apt install -y python3 python3-venv python3-pip

# Node.js（用 nvm，避免污染系统）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install --lts

# Docker
sudo apt install -y docker.io
sudo usermod -aG docker $USER   # 重登生效

# Go / Rust / Java 等按需装
```

---

## 八、常见问题排查

### 8.1 vscode-server 下载慢 / 卡住

服务器直连 GitHub 慢导致。可以：

- 方案 A：给服务器配置代理（`~/.bashrc` 加 `export https_proxy=...`）
- 方案 B：手动下载 `vscode-server` 上传：
  1. 本地 VS Code 帮助 → 关于，记下 commit SHA
  2. `wget https://update.code.visualstudio.com/commit:<SHA>/server-linux-x64/stable`
  3. 解压到服务器 `~/.vscode-server/bin/<SHA>/`
- 方案 C：使用国内镜像（如 <https://vscode.cdn.azure.cn/>）

### 8.2 连接反复断开

`~/.ssh/config` 里加：

```ssh-config
ServerAliveInterval 30
ServerAliveCountMax 3
TCPKeepAlive yes
```

服务器 `/etc/ssh/sshd_config`：

```conf
ClientAliveInterval 30
ClientAliveCountMax 3
```

### 8.3 大型项目卡顿

- 在项目 `.vscode/settings.json` 里排除大目录：

  ```json
  {
    "files.watcherExclude": {
      "**/node_modules/**": true,
      "**/.venv/**": true,
      "**/dist/**": true,
      "**/build/**": true
    },
    "search.exclude": {
      "**/node_modules": true,
      "**/.venv": true
    }
  }
  ```

### 8.4 权限问题（编辑文件报 Permission denied）

- 确认 SSH 登录用户就是文件所有者
- 或 `sudo chown -R ubuntu:ubuntu /path/to/project`
- 避免用 `root` 打开需要普通用户运行的项目

### 8.5 服务器无公网 IP / 内网穿透

- 使用 VS Code **Remote Tunnels**（不需要公网 SSH）
- 服务器上：

  ```bash
  # 下载 code CLI
  curl -L "https://code.visualstudio.com/sha/download?build=stable&os=cli-linux-x64" -o code.tar.gz
  tar -xf code.tar.gz
  sudo mv code /usr/local/bin/
  code tunnel   # 首次登录 GitHub/微软账号，会给出 vscode.dev 链接
  ```

- 本地 VS Code 命令面板 → `Remote Tunnels: Connect to Tunnel` 选择服务器即可

### 8.6 磁盘满：`~/.vscode-server` 越来越大

```bash
du -sh ~/.vscode-server
# 断开所有 VS Code 连接后可清理旧版本
rm -rf ~/.vscode-server/bin/<旧commit>
# 或整体重装（下次连接会重新下载）
rm -rf ~/.vscode-server
```

### 8.7 端口被占用 / 端口转发失败

```bash
# 服务器上查看谁占用了端口
sudo ss -tlnp | grep :8080
# VS Code PORTS 面板右键端口 → Stop Forwarding
```

---

## 九、完整工作流示例

以在 Ubuntu 22 上开发一个 Python + FastAPI 项目为例：

1. **本地**：VS Code 打开 → 左下角 `><` → `Connect to Host` → 选 `ubuntu-dev`
2. **远端**：`File → Open Folder` → `/home/ubuntu/projects/myapi`
3. **终端**（远端）：

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn
   uvicorn app:app --reload --port 8000
   ```

4. **端口转发**：底部 `PORTS` 面板自动/手动转发 `8000`，本地浏览器打开 `http://localhost:8000`
5. **调试**：`.vscode/launch.json` 配置 `debugpy`，F5 直接断点调试
6. **提交**：源代码管理面板 `git commit / push`，走服务器上的 SSH key

全程本地 VS Code 只作为 UI，代码、依赖、进程、Git 全部在 Ubuntu 服务器上。

---

## 十、附：可直接复制的 SSH config 模板

```ssh-config
# ~/.ssh/config

# ---- Ubuntu 22 开发机 ----
Host ubuntu-dev
  HostName YOUR_SERVER_IP_OR_DOMAIN
  User ubuntu
  Port 22
  IdentityFile ~/.ssh/id_ed25519
  ServerAliveInterval 30
  ServerAliveCountMax 3
  ForwardAgent yes

# ---- 通过跳板机连接内网服务器 ----
Host bastion
  HostName bastion.example.com
  User ops
  IdentityFile ~/.ssh/id_ed25519

Host ubuntu-inner
  HostName 10.0.1.20
  User ubuntu
  Port 22
  IdentityFile ~/.ssh/id_ed25519
  ProxyJump bastion
```

Windows 用户把 `IdentityFile` 替换为绝对路径（例）：

```ssh-config
IdentityFile C:\Users\zhaojian\.ssh\id_ed25519
```

---

## 十一、参考

- VS Code Remote-SSH 官方文档：<https://code.visualstudio.com/docs/remote/ssh>
- Ubuntu OpenSSH 文档：<https://ubuntu.com/server/docs/service-openssh>
- Remote Tunnels：<https://code.visualstudio.com/docs/remote/tunnels>
