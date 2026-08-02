# Migration Workflow Reference

## Detailed Steps

### 1. Pre-Migration Analysis

```bash
# 1.1 确认当前分支状态
git status
git branch

# 1.2 查看自定义提交
git log --author="zhaojian" --author="ext_zhaojian03" --all --oneline --no-merges

# 1.3 统计变更文件
git log --author="zhaojian" --author="ext_zhaojian03" --all --name-only --format="" --no-merges | sort | uniq -c | sort -rn

# 1.4 识别关键变更区域
git diff main..learn --stat -- libs/code/deepagents_code/
```

### 2. Branch Setup

```bash
# 2.1 更新 main 到最新
git checkout main
git pull origin main

# 2.2 创建迁移分支
git checkout -b migrate-zjcode-features main

# 2.3 验证分支基础
git log --oneline -5  # Should show main branch commits
```

### 3. Patch Application Strategy

#### Order of Application

1. **Brand isolation patches** (foundation)
   - Path constants (`.deepagents` → `.zjcode`)
   - Package names (`deepagents-code` → `zjcode`)
   - UI strings and banners

2. **Configuration changes**
   - Config file paths
   - Environment variables
   - Default settings

3. **New features**
   - Clipboard/image handling
   - Model selector enhancements
   - Custom provider support
   - Session end status tracking

4. **Bug fixes**
   - Platform-specific fixes (Windows)
   - Edge case handling
   - Error message improvements

5. **Test updates**
   - Unit test adjustments
   - Snapshot updates

#### Applying Patches

```bash
# Apply single patch
git apply path/to/patch.patch

# Apply with conflict detection
git apply --check path/to/patch.patch  # Dry run
git apply path/to/patch.patch          # Actual apply

# Apply with 3-way merge (better conflict resolution)
git apply --3way path/to/patch.patch
```

### 4. Conflict Resolution

#### Common Conflict Types

**Type 1: Import Path Conflicts**
```python
# Conflict: Both branches added imports
<<<<<<< HEAD
from deepagents_code.new_upstream_module import NewFeature
=======
from deepagents_code.custom_feature import CustomFeature
>>>>>>> migrate-zjcode-features

# Resolution: Keep both
from deepagents_code.new_upstream_module import NewFeature
from deepagents_code.custom_feature import CustomFeature
```

**Type 2: Function Signature Conflicts**
```python
# Conflict: Upstream changed signature, custom added parameter
<<<<<<< HEAD
def process_config(config_path: Path) -> Config:
=======
def process_config(config_path: Path, use_custom: bool = True) -> Config:
>>>>>>> migrate-zjcode-features

# Resolution: Merge signatures (prefer upstream base, add custom params)
def process_config(config_path: Path, use_custom: bool = True) -> Config:
```

**Type 3: Path Constant Conflicts**
```python
# Conflict: Both changed paths
<<<<<<< HEAD
CONFIG_DIR = Path.home() / ".deepagents" / "config"
=======
CONFIG_DIR = Path.home() / ".zjcode" / "config"
>>>>>>> migrate-zjcode-features

# Resolution: Always use .zjcode
CONFIG_DIR = Path.home() / ".zjcode" / "config"
```

### 5. Post-Migration Validation

```bash
# 5.1 Syntax check
python -m py_compile libs/code/deepagents_code/**/*.py

# 5.2 Import check
cd libs/code
python -c "import deepagents_code; print('✓ Import OK')"

# 5.3 Brand consistency check
bash ~/.zjcode/agent/skills/zjcode-feature-migration/scripts/check-brand.sh

# 5.4 Run tests
cd libs/code
uv run pytest tests/unit_tests/ -x -v

# 5.5 Integration test
uv run python -m deepagents_code.main --help
```

## Migration Checklist

- [ ] Main branch updated to latest
- [ ] Migration branch created from main
- [ ] Brand isolation patches applied
- [ ] Configuration patches applied
- [ ] Feature patches applied
- [ ] Bug fix patches applied
- [ ] Test patches applied
- [ ] All conflicts resolved
- [ ] Import checks pass
- [ ] Brand consistency verified
- [ ] Unit tests pass
- [ ] CLI commands work
- [ ] Migration report generated

## Rollback Procedure

If migration fails:

```bash
# 1. Abort current migration
git apply --abort  # If in middle of apply
git reset --hard HEAD

# 2. Return to clean state
git checkout main
git branch -D migrate-zjcode-features

# 3. Start over with new branch
git checkout -b migrate-zjcode-features-retry main
```
