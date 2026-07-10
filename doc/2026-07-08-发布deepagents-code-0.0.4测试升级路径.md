# 2026-07-08 发布 deepagents-code 0.0.4 到私有源(测试脚本升级路径)

---
✨ ✨ ✨ ✨ ✨ ✨ 【 NEW SESSION 】 ✨ ✨ ✨ ✨ ✨ ✨
---

### 轮次 1 - 从 0.0.3 → 0.0.4,复现 install.sh 升级路径

**用户目标**
- 想要测试之前改过的 `web/install.sh` 在"用户本地已经装了 0.0.3、私有源出了 0.0.4"场景下是否真的能升级
- 因此先把 `libs/code` 版本 bump 到 0.0.4,再发布到私有源

**改动**
- `libs/code/pyproject.toml` : `version = "0.0.3"` → `"0.0.4"`
- `libs/code/deepagents_code/_version.py` : `__version__ = "0.0.3"` → `"0.0.4"`
- (`bump-version.py` 里有个 typo `read_pyproject_version6`,导致该脚本跑不通,本轮走手工改; 后续要修 bump-version.py)

**发布流程 = 直接跑 `run-build-upload.sh`**
- 自动做 4 件事:
  1. `uv build` 生成 `dist/deepagents_code-0.0.4-py3-none-any.whl` + `.tar.gz`
  2. `twine upload` 到私有源 `http://8.152.204.58:48080`
  3. 读 Simple Index 重新生成 `web/pypi/deepagents-code/json`(Warehouse JSON API 兼容格式,`info.version=0.0.4`)
  4. `rsync` 整个 `web/` 到 `root@8.152.204.58:/opt/1panel/www/sites/8.152.204.58/index/`

**校验**
```bash
curl -fsS http://admin:admin@8.152.204.58:48080/simple/deepagents-code/ | grep -oE 'deepagents[_-]code-[0-9]+\.[0-9]+\.[0-9]+' | sort -u
# -> 0.0.1 / 0.0.2 / 0.0.3 / 0.0.4

curl -fsS http://8.152.204.58:40080/pypi/deepagents-code/json | jq '.info.version, (.releases|keys)'
# -> "0.0.4"
# -> ["0.0.1","0.0.2","0.0.3","0.0.4"]
```

**用户侧测试步骤(Ubuntu)**
```bash
# 清污染缓存(之前误装过公共 PyPI 版本残留的)
rm -f ~/.deepagents/.state/latest_version.json ~/.deepagents/.state/update_state.json
# 关掉 dcode 内置 auto-update(它不认私有源,会踩坑)
export DEEPAGENTS_CODE_AUTO_UPDATE=0
# 跑 install.sh
curl -fsSL http://8.152.204.58:40080/install.sh | bash
# 期望日志出现:
#   [install] resolved latest private version: 0.0.4
#   [install] detected deepagents-code v0.0.3; installing deepagents-code==0.0.4...
#   [install] deepagents-code upgraded: v0.0.3 -> v0.0.4
dcode --version   # 期望 0.0.4
```

**关键结论**
- `install.sh` 本身不用改,升级路径已由上一轮的"resolve最新私有版 → pin `==X.Y.Z` → unsafe-best-match → prerelease=allow"承载
- 版本 bump + 发布 + JSON API 刷新 + 静态站部署全部在 `run-build-upload.sh` 一站式完成,不用手动 rsync `web/`

**TODO**
- `libs/code/bump-version.py` 第 198 行调用了不存在的 `read_pyproject_version`(应为 `read_pyproject_version6` 或者把 `6` 那个 typo 改掉),后续修一下让 bump 命令能用
- dcode 内置的 auto-update 走的升级命令没带私有源 index url、没带 `unsafe-best-match`、没带 `--prerelease=allow`,私有源用户实际上只能靠 `install.sh` 升级。要么在 dcode 侧扩展升级命令支持环境变量注入 index url,要么固定关闭 auto-update 走脚本升级
