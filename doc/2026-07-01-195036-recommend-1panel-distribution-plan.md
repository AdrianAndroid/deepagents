# Recommend 1Panel Distribution Plan

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

- Time: 2026-07-01T19:50:36+08:00
- Project: deepagents

## Prompt

用户希望将 dcode 二次开发版本通过 1Panel 做成分发平台，并提供了《dcode二次开发版本分发与1Panel部署指南》草稿，包含私有 PyPI、静态下载站、私有 Docker 仓库、SaaS 化服务端四种方案。

## AI Response

这个方向可行。建议先采用“静态文件下载站 + install.sh”的方案，最快上线、维护成本最低；等团队需要 `pip install` 体验时，再补私有 PyPI 源。

推荐落地结构：

```text
/opt/1panel/www/sites/download/
├── dcode/
│   ├── latest/
│   │   ├── deepagents_code-0.1.24-py3-none-any.whl
│   │   ├── deepagents_code-0.1.24.tar.gz
│   │   └── install.sh
│   └── releases/
│       └── 0.1.24/
│           ├── deepagents_code-0.1.24-py3-none-any.whl
│           ├── deepagents_code-0.1.24.tar.gz
│           └── install.sh
```

上传：

```bash
scp libs/code/dist/deepagents_code-0.1.24* root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
scp install.sh root@服务器IP:/opt/1panel/www/sites/download/dcode/releases/0.1.24/
```

服务器同步 latest：

```bash
rm -rf /opt/1panel/www/sites/download/dcode/latest
cp -R /opt/1panel/www/sites/download/dcode/releases/0.1.24 /opt/1panel/www/sites/download/dcode/latest
```

用户安装：

```bash
curl -fsSL https://你的下载域名/dcode/latest/install.sh | bash
```

这套方案后续可以平滑升级到私有 PyPI 或 Docker 镜像仓库。
