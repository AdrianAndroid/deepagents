#!/bin/bash
set -euo pipefail

# ========== 自定义配置区 ==========
ENV_NAME="deepagents"
PYTHON_VER="3.12"
PYPI_HOST="8.152.204.58:48080"          # 私有 pypiserver (Simple Index + 上传)
PYPI_USER="admin"
PYPI_PWD="admin"
PKG_NAME="deepagents-code"              # 主程序包名
SDK_NAME="deepagents"                   # SDK 包名（用于版本检查的发布时间）
SDK_FALLBACK_VERSION="0.7.0a3"         # 私有源暂无 SDK 时的占位版本

# 静态站（40080，托管 install.sh 与 JSON API 镜像，免认证）部署目标
DEPLOY_REMOTE="root@8.152.204.58:/opt/1panel/www/sites/8.152.204.58/index/"
DEPLOY_SSH_PORT="${SSH_PORT:-22}"
# ===================================

PYPI_REPO_URL="http://${PYPI_HOST}"
SIMPLE_URL_AUTH="http://${PYPI_USER}:${PYPI_PWD}@${PYPI_HOST}/simple"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"
WEB_DIR="${SCRIPT_DIR}/../../web"
PYPI_JSON_DIR="${WEB_DIR}/pypi"

# ---------- 1. 准备 conda / uv 环境 ----------
source "$(conda info --base)/etc/profile.d/conda.sh"

if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "未检测到conda环境 ${ENV_NAME}，开始创建 Python ${PYTHON_VER} 环境..."
    conda create -n "${ENV_NAME}" python=${PYTHON_VER} -y
fi
conda activate "${ENV_NAME}"

if ! command -v uv &> /dev/null; then
    echo "未检测到uv，执行pip安装uv..."
    pip install uv
fi

uv pip install twine

# ---------- 2. 构建并上传 ----------
# 注意：uv build 没有 --clean，需要手动清理 dist/
rm -rf "${DIST_DIR}"
uv build

echo "开始上传包至仓库：${PYPI_REPO_URL}"
twine upload \
    --repository-url "${PYPI_REPO_URL}" \
    --username "${PYPI_USER}" \
    --password "${PYPI_PWD}" \
    dist/*

echo "🎉 构建+上传私有PyPI完成！"

# ---------- 3. 生成 Warehouse JSON API 适配文件 ----------
# pypiserver 只提供 PEP 503 Simple Index，没有 /pypi/<pkg>/json（Warehouse JSON API）。
# deepagents-code 的内置版本检查请求的是 JSON API，因此这里从私有源的 Simple Index
# 读取“当前仍存在的所有版本”重新生成静态 JSON（删除旧版本后再次运行即可同步删除），
# 写入 web/pypi/，随后一并部署到 40080 静态站（免认证）。
echo "生成 JSON API 适配文件到 ${PYPI_JSON_DIR}/ ..."
PKG_NAME="${PKG_NAME}" \
SDK_NAME="${SDK_NAME}" \
SDK_FALLBACK_VERSION="${SDK_FALLBACK_VERSION}" \
SIMPLE_URL_AUTH="${SIMPLE_URL_AUTH}" \
PYPI_JSON_DIR="${PYPI_JSON_DIR}" \
python3 - <<'PYEOF'
import base64
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

PKG_NAME = os.environ["PKG_NAME"]
SDK_NAME = os.environ["SDK_NAME"]
SDK_FALLBACK = os.environ["SDK_FALLBACK_VERSION"]
SIMPLE_URL = os.environ["SIMPLE_URL_AUTH"]
OUT_DIR = Path(os.environ["PYPI_JSON_DIR"])

WHEEL_RE = re.compile(r"^(?P<name>.+?)-(?P<version>\d[^-]*?)(?:-.*)?\.whl$")
SDIST_RE = re.compile(r"^(?P<name>.+?)-(?P<version>\d[^-]*?)\.tar\.gz$")
HREF_RE = re.compile(r">([^<>]+\.(?:whl|tar\.gz))<")


def parse_version(filename):
    for pattern in (WHEEL_RE, SDIST_RE):
        m = pattern.match(filename)
        if m:
            return m.group("version")
    return None


def is_prerelease(v):
    return bool(re.search(r"(a|b|rc|dev|alpha|beta)", v, re.IGNORECASE))


def version_key(v):
    rel = re.match(r"^(\d+(?:\.\d+)*)", v)
    parts = tuple(int(p) for p in rel.group(1).split(".")) if rel else ()
    return (parts, not is_prerelease(v), v)


def split_auth(url):
    parts = urlsplit(url)
    if not parts.username:
        return url, None
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    clean = urlunsplit(
        (parts.scheme, host, parts.path, parts.query, parts.fragment)
    )
    raw = f"{parts.username}:{parts.password or ''}".encode()
    return clean, "Basic " + base64.b64encode(raw).decode()


def fetch_versions(package):
    base, auth = split_auth(SIMPLE_URL)
    url = f"{base.rstrip('/')}/{package}/"
    req = urllib.request.Request(url)
    if auth:
        req.add_header("Authorization", auth)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] 读取 Simple Index 失败 {url}: {exc}", file=sys.stderr)
        return set()
    return {v for f in HREF_RE.findall(html) if (v := parse_version(f))}


def now_iso():
    return (
        dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def build_payload(versions):
    ordered = sorted(versions, key=version_key)
    stable = [v for v in ordered if not is_prerelease(v)]
    latest = stable[-1] if stable else (ordered[-1] if ordered else "0.0.0")
    ts = now_iso()
    releases = {v: [{"upload_time_iso_8601": ts}] for v in ordered}
    return {"info": {"version": latest, "requires_dist": []}, "releases": releases}


def write_json(package, payload):
    out = OUT_DIR / package
    out.mkdir(parents=True, exist_ok=True)
    (out / "json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"[ok] {out / 'json'} "
        f"(latest={payload['info']['version']}, "
        f"versions={list(payload['releases'])})"
    )


# 主程序：严格以私有源当前状态为准（删除旧版本会被同步）
pkg_versions = fetch_versions(PKG_NAME)
if not pkg_versions:
    print(f"[error] 私有源未找到 {PKG_NAME} 的任何版本", file=sys.stderr)
    sys.exit(1)
write_json(PKG_NAME, build_payload(pkg_versions))

# SDK：私有源可能没有，退回占位版本，避免版本检查端点 404
sdk_versions = fetch_versions(SDK_NAME) or {SDK_FALLBACK}
write_json(SDK_NAME, build_payload(sdk_versions))
PYEOF

# ---------- 4. 部署静态站（含 pypi/*/json） ----------
echo "部署 ${WEB_DIR} 到 ${DEPLOY_REMOTE} ..."
rsync -avz --delete \
    --exclude 'run-deploy.sh' \
    --exclude 'run-serve.sh' \
    --exclude '.DS_Store' \
    --exclude '.git' \
    -e "ssh -p ${DEPLOY_SSH_PORT}" \
    "${WEB_DIR}/" "${DEPLOY_REMOTE}"

echo "✅ 全部完成：构建 → 上传(48080) → 生成JSON → 部署静态站(40080)"
