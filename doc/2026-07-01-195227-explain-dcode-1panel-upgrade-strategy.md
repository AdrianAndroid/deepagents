# Explain Dcode 1Panel Upgrade Strategy

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T19:52:27+08:00
- Project: deepagents

## Prompt

后续升级怎么办?<environment_details>
Current time: 2026-07-01T19:52:27+08:00
Working directory: /Users/zhaojian/Desktop/deepagents
Workspace root folder: /Users/zhaojian/Desktop/deepagents
Active file: doc/dcode二次开发版本分发与1Panel部署指南.md
Visible files:
  doc/dcode二次开发版本分发与1Panel部署指南.md
Open tabs:
  doc/dcode二次开发版本分发与1Panel部署指南.md
</environment_details>

## AI Response

后续升级建议采用“版本目录不可变 + latest 指针切换”的发布模式。

发布新版本时：

1. 本地打包新版本，例如 `0.1.25`：

```bash
cd libs/code
uv build
```

2. 上传到服务器独立版本目录：

```bash
ssh root@服务器IP 'mkdir -p /opt/1panel/www/sites/download/dcode/releases/0.1.25'
scp dist/deepagents_code-0.1.25* root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.25/
scp install.sh root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.25/
```

3. 测试固定版本链接：

```bash
curl -fsSL https://下载域名/dcode/releases/0.1.25/install.sh | bash
```

4. 确认没问题后切换 `latest`：

```bash
ssh root@服务器IP '
rm -rf /opt/1panel/www/sites/download/dcode/latest.tmp &&
cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.25 /opt/1panel/www/sites/download/dcode/latest.tmp &&
mv -Tf /opt/1panel/www/sites/download/dcode/latest.tmp /opt/1panel/www/sites/download/dcode/latest
'
```

用户升级：

```bash
curl -fsSL https://下载域名/dcode/latest/install.sh | bash
```

回滚：

```bash
ssh root@服务器IP '
rm -rf /opt/1panel/www/sites/download/dcode/latest.tmp &&
cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.24 /opt/1panel/www/sites/download/dcode/latest.tmp &&
mv -Tf /opt/1panel/www/sites/download/dcode/latest.tmp /opt/1panel/www/sites/download/dcode/latest
'
```

关键原则：
- `releases/x.y.z/` 发布后不要覆盖，保证历史版本可追溯。
- `latest/` 只作为当前推荐版本入口。
- `install.sh` 支持重复执行，内部用 `pip install --upgrade`。
- 保留至少最近 3-5 个版本，方便回滚。
