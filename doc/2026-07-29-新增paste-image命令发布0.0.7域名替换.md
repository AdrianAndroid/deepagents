# 2026-07-29 - 新增/paste-image命令、发布0.0.7、web安装页域名化

## 1. 新增 `/paste-image` 命令

**需求：** 用户可以主动从剪贴板获取图片，不需要依赖 Ctrl+V 粘贴

**实现文件：**
- `libs/code/deepagents_code/command_registry.py` - 注册命令
- `libs/code/deepagents_code/app.py` - 命令处理逻辑

**功能特性：**
- 命令：`/paste-image`，别名 `/paste-img`
- 跨平台支持：macOS / Windows / Linux
- 自动调用 `get_clipboard_image()` 获取剪贴板图片
- 图片存档到 `~/.zjcode/pasted/` 目录
- 插入占位符到当前光标位置

**Bug 修复：**
- 第一次实现时错误使用 `chat_input.text` 和 `chat_input.insert()`
- ChatInput 组件的正确 API：
  - 获取内容：`chat_input.value`（属性 getter）
  - 插入内容：`chat_input._text_area.insert(content)`

## 2. 发布 zjcode 0.0.7 到 PyPI

**版本变更：** 0.0.6 → 0.0.7

**发布流程：**
1. 检查 git 状态（干净）
2. 检查分支（learn）
3. 运行 `bump-version.py 0.0.7` - 更新三处版本号：
   - `pyproject.toml`
   - `deepagents_code/_version.py`
   - `.release-please-manifest.json`
4. `uv lock` 更新 lockfile
5. `uv build` 本地构建验证
6. git commit + tag `zjcode-v0.0.7`
7. 推送 GitHub，触发 Actions 上传 PyPI

**PyPI 地址：** https://pypi.org/project/zjcode/0.0.7/

## 3. Web 安装页域名替换

**问题：** `web/index.html` 中所有安装脚本链接还是 IP 地址
```
http://8.152.204.58:40080/install.sh
http://8.152.204.58:40080/uninstall.sh
http://8.152.204.58:40080/install.ps1
...
```

**变更：**
- 7 处 `http://8.152.204.58:40080/` → `https://zjcode.zhaojian.xin/`
- 修改 `web/run-deploy.sh` 部署路径到域名目录

**部署问题排查：**
- **现象：** 上传后访问页面仍然显示旧内容（IP地址）
- **原因：** Nginx 配置是反向代理 `proxy_pass http://172.17.0.1:40080/`，指向的是老站点目录 `8.152.204.58/index/`，不是新创建的 `zjcode.zhaojian.xin/index/`
- **解决：** 把新的 `index.html` 同时 rsync 到老目录即可

**验证结果：**
```bash
✅ http://zjcode.zhaojian.xin/ 已全部使用 https://zjcode.zhaojian.xin/
   7 处域名替换完成
```

## 4. 修改文件清单

```
libs/code/deepagents_code/command_registry.py
libs/code/deepagents_code/app.py
libs/code/pyproject.toml
libs/code/deepagents_code/_version.py
libs/code/uv.lock
.release-please-manifest.json
web/index.html
web/run-deploy.sh
```

## 5. 提交记录

- `chore(zjcode): bump version to 0.0.7` - 4 files changed
- Tag: `zjcode-v0.0.7`
