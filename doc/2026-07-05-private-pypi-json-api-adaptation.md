# 私有 PyPI 源适配 dcode 版本检查 (JSON API 镜像方案)

## 背景与需求

`deepagents-code`(dcode)内置版本检查请求 Warehouse JSON API:
- `https://pypi.org/pypi/deepagents-code/json`(主程序，`_version.py:PYPI_URL`)
- `https://pypi.org/pypi/deepagents/json`(SDK 发布时间，`_version.py:SDK_PYPI_URL`)

私有源 `8.152.204.58:48080` 是 `pypiserver`，**只提供 PEP 503 Simple Index，没有 JSON API**(实测 `/pypi/<pkg>/json` 返回 404)。

用户诉求：**不改动版本检查的请求逻辑，只让私有仓库适配现有逻辑**，允许改 `_version.py` 里的 URL 常量。

## 关键结论

- `update_check.py` 只解析这几个字段：`info.version`(str)、`releases`(dict: 版本->文件列表)、`info.requires_dist`、`releases[<ver>][0].upload_time_iso_8601`。
- 私有 pypiserver 无法生成 JSON API，但项目有一个 **1panel 静态站(端口 40080)**，托管 install.sh。把 JSON **静态文件**放到那里即可，且免认证(`requests.get` 只带 User-Agent，不带认证)。
- HTTP 明文可用，`requests` 不强制 HTTPS。
- editable 安装下自动更新始终禁用(`is_auto_update_enabled` 对 editable 返回 False)，改 URL 后仅影响"有新版可用"提示，不会自动下载 re-exec。

## 实施内容

### 1. 新增 `web/gen-pypi-json.py`(JSON API 生成器)
- 纯标准库；从私有 Simple Index(48080) + 本地 `dist/` 合并所有历史版本。
- 处理 `user:pass@host` 认证(urllib 不认内嵌认证，改为拆出 Basic Auth 头)。
- 输出 `web/pypi/<package>/json`，结构兼容 Warehouse 子集。

### 2. `web/pypi/` 测试 JSON(已生成并验证)
- `web/pypi/deepagents-code/json` — 含 0.0.1 / 0.0.2(从 48080 抓取)。
- `web/pypi/deepagents/json` — SDK 占位(0.7.0a3，私有源暂无 SDK)。
- 用 dcode 相同解析逻辑校验通过。

### 3. `libs/code/run-build-upload.sh`
- `twine upload` 之后自动调用 `gen-pypi-json.py`，把 JSON 写入 `web/pypi/`。
- 为生成脚本补上 Basic 认证 URL。
- 提示随后运行 `web/run-deploy.sh` 同步到 40080 静态站。

### 4. `libs/code/deepagents_code/_version.py`
- `PYPI_URL` / `SDK_PYPI_URL` 改为环境变量可覆盖，默认指向 `http://8.152.204.58:40080/pypi/.../json`。
- 环境变量 `DEEPAGENTS_CODE_PYPI_URL` / `DEEPAGENTS_CODE_SDK_PYPI_URL` 可切回公网 PyPI。
- **请求逻辑完全未动**，只改 URL 常量。

### 5. 登记新环境变量(drift 测试要求)
- `_env_vars.py`：新增 `PYPI_URL`、`SDK_PYPI_URL` 常量(字母序)，`_version.py` 改为 import 常量(禁止裸字面量)。
- `config_manifest.py`：加入 `NON_OPTION_ENV_VARS`(非用户配置项，仅内部镜像 URL)。

### 6. `web/index.html`
- 新增"版本检查镜像(JSON API)"章节，说明两个 JSON 地址、生成/同步流程、环境变量切回公网的方式、editable 下自动更新禁用的说明。
- 原"常见问题"编号 5->6。

## 验证结果
- `test_env_vars.py` 17 passed；`test_config_manifest.py` + `test_env_vars.py` 123 passed。
- 全量相关测试 817 passed(修复 manifest 后)。
- `_version.py` / `_env_vars.py` / `config_manifest.py` ruff 全通过。
- 导入烟测通过，`update_check.PYPI_URL` 已指向私有地址。
- `run-build-upload.sh` bash 语法检查通过。

## 后续 TODO
- 运行 `web/run-deploy.sh` 把 `web/pypi/` 同步到 40080 静态站(当前 40080 仍 404，deploy 后生效)。
- 确认 40080 静态站对 `/pypi/*/json` 无 Basic Auth。
- 若私有源日后上传 `deepagents` SDK，`gen-pypi-json.py` 可同样生成其 JSON。

## 数据流
```
run-build-upload.sh:
  uv build -> dist/*.whl
  ├─ twine upload -> 48080 pypiserver (安装, /simple/)
  └─ gen-pypi-json.py -> web/pypi/*/json (版本检查)
run-deploy.sh:
  rsync web/ -> 40080 静态站 (含 pypi/*/json, 免认证)
dcode:
  PYPI_URL -> 40080/pypi/.../json (版本检查, HTTP)
  install  -> 48080/simple/ (下载)
```
