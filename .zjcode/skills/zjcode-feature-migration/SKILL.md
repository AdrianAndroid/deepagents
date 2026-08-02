---
name: zjcode-feature-migration
description: "Migrate ALL custom features from learn branch to a new branch based on latest main. Use when: (1) syncing with upstream main updates, (2) creating a fresh migration branch, (3) ensuring no custom features are missed. Triggers: 'migrate features', 'sync with main', '迁移功能', '同步上游', '创建迁移分支'."
license: MIT
compatibility: designed for zjcode (deepagents fork)
---

# zjcode Feature Migration

**核心原则**：每次迁移都从 learn 分支的当前状态动态发现所有差异，不依赖预定义列表。

## When to Use

- 需要基于最新 main 创建新的迁移分支
- learn 分支新增了功能，需要同步到 main-based 分支
- 确保所有自定义功能都被迁移，没有遗漏

## Migration Workflow

### Phase 1: 动态发现所有差异（关键步骤）

**不要依赖任何预定义的文件列表或功能清单**。learn 分支可能随时新增功能，必须每次动态发现。

#### 1.1 生成完整的差异报告

```bash
# 创建工作目录
mkdir -p ~/.zjcode/tmp/migration-$(date +%Y%m%d-%H%M%S)
cd ~/.zjcode/tmp/migration-*

# 1. 统计所有变更文件
git diff main..learn --stat -- libs/code/ > changed-files-stat.txt

# 2. 列出所有新增文件（learn 有，main 没有）
git diff main..learn --diff-filter=A --name-only -- libs/code/deepagents_code/ > new-files.txt

# 3. 列出所有修改文件
git diff main..learn --diff-filter=M --name-only -- libs/code/deepagents_code/ > modified-files.txt

# 4. 列出所有删除文件（main 有，learn 删除了）
git diff main..learn --diff-filter=D --name-only -- libs/code/deepagents_code/ > deleted-files.txt

# 5. 生成完整 patch（用于参考）
git diff main..learn -- libs/code/ > zjcode-all-changes.patch

# 6. 统计数量
echo "=== 变更统计 ==="
echo "新增文件: $(wc -l < new-files.txt)"
echo "修改文件: $(wc -l < modified-files.txt)"
echo "删除文件: $(wc -l < deleted-files.txt)"
```

#### 1.2 分析所有 commit 理解功能演进

```bash
# 列出 learn 分支的所有 commit（排除 merge）
git log main..learn --oneline --no-merges -- libs/code/ > all-commits.txt

# 按功能分类 commit（手动或使用 AI 分析）
git log main..learn --no-merges --format="%H|%s|%ai" -- libs/code/ > commits-with-messages.txt

# 查看每个 commit 的具体变更
for commit in $(cut -d'|' -f1 commits-with-messages.txt); do
  echo "=== Commit: $commit ==="
  git show --stat $commit -- libs/code/ >> commit-details.txt
  echo "" >> commit-details.txt
done
```

#### 1.3 生成迁移清单

基于上述分析，生成结构化的迁移清单：

```bash
cat > migration-checklist.md << 'EOF'
# 迁移清单

## 新增文件（必须复制）
EOF

cat new-files.txt >> migration-checklist.md

cat >> migration-checklist.md << 'EOF'

## 修改文件（需要合并）
EOF

cat modified-files.txt >> migration-checklist.md

cat >> migration-checklist.md << 'EOF'

## 删除文件（需要确认是否删除）
EOF

cat deleted-files.txt >> migration-checklist.md
```

### Phase 2: 创建新的迁移分支

```bash
# 1. 确保在最新的 main 上
git checkout main
git pull origin main

# 2. 创建新的迁移分支（命名规范：migrate-zjcode-YYYYMMDD）
git checkout -b migrate-zjcode-$(date +%Y%m%d)

# 3. 验证分支状态
git status  # 应该是 clean 的
```

### Phase 3: 迁移所有差异

#### 3.1 迁移新增文件

```bash
# 从 learn 分支复制所有新增文件
while IFS= read -r file; do
  # 提取相对路径（去掉 libs/code/ 前缀）
  rel_path=${file#libs/code/}
  
  # 确保目标目录存在
  mkdir -p $(dirname "libs/code/$rel_path")
  
  # 从 learn 分支检出文件
  git show learn:libs/code/$rel_path > libs/code/$rel_path
  
  echo "✓ 复制: $rel_path"
done < ~/.zjcode/tmp/migration-*/new-files.txt
```

#### 3.2 合并修改文件

对于每个修改文件，需要：
1. 查看 learn 分支的修改内容
2. 查看 main 分支的修改内容
3. 手动合并或应用 patch

```bash
# 对于每个修改文件
while IFS= read -r file; do
  echo "=== 处理: $file ==="
  
  # 查看 learn 的修改
  echo "Learn 分支的修改:"
  git diff main..learn -- $file | head -50
  
  # 查看 main 的修改（相对于共同祖先）
  echo "Main 分支的修改:"
  git diff $(git merge-base main learn)..main -- $file | head -50
  
  # 手动编辑文件或应用 patch
  # git apply 或手动编辑
  
done < ~/.zjcode/tmp/migration-*/modified-files.txt
```

#### 3.3 应用品牌隔离

所有用户可见的引用需要替换：

```bash
# 批量替换（谨慎使用，需要验证）
# deepagents-code → zjcode
# Deep Agents → zjcode
# DeepAgents → zjcode
# ~/.deepagents → ~/.zjcode
# .deepagents/ → .zjcode/

# 使用 sed 或手动编辑
find libs/code/deepagents_code -type f \( -name "*.py" -o -name "*.md" -o -name "*.toml" \) \
  -exec sed -i '' 's/deepagents-code/zjcode/g' {} \;
```

**注意**：Python 模块导入路径 `deepagents_code` **不要改**，只改 PyPI 包名和用户可见的字符串。

### Phase 4: 验证没有遗漏

#### 4.1 文件完整性检查

```bash
# 对比 learn 和当前分支的文件数量
LEARN_COUNT=$(git ls-tree -r learn --name-only -- libs/code/deepagents_code/ | wc -l)
CURRENT_COUNT=$(find libs/code/deepagents_code -type f | wc -l)

echo "Learn 分支文件数: $LEARN_COUNT"
echo "当前分支文件数: $CURRENT_COUNT"

# 列出 learn 有但当前分支没有的文件
git ls-tree -r learn --name-only -- libs/code/deepagents_code/ > /tmp/learn-files.txt
find libs/code/deepagents_code -type f | sed 's|^libs/code/||' > /tmp/current-files.txt

echo "=== Learn 有但当前分支没有的文件 ==="
comm -23 <(sort /tmp/learn-files.txt) <(sort /tmp/current-files.txt)
```

#### 4.2 功能验证

```bash
cd libs/code

# 1. 检查导入
python -c "import deepagents_code; print('✓ Package imports')"

# 2. 检查 CLI
python -m deepagents_code.main --help | head -20

# 3. 运行单元测试
python -m pytest tests/unit_tests/ -x -v

# 4. 检查品牌隔离
grep -r "deepagents-code\|DeepAgents\|\.deepagents" deepagents_code/ \
  --include="*.py" --include="*.md" --include="*.toml" \
  | grep -v "test_\|tests/\|CHANGELOG\|\.venv" \
  | grep -v "deepagents_langchain\|lc_versions\.deepagents" \
  && echo "✗ 发现品牌引用" || echo "✓ 品牌隔离完成"
```

#### 4.3 差异对比验证

```bash
# 生成当前分支与 learn 的差异报告
git diff learn..HEAD --stat -- libs/code/ > migration-diff-stat.txt

# 查看还有哪些文件不同
git diff learn..HEAD --name-only -- libs/code/deepagents_code/ > remaining-diffs.txt

echo "=== 与 learn 分支仍有差异的文件 ==="
cat remaining-diffs.txt

# 对于每个有差异的文件，确认是预期的（品牌替换）还是遗漏的
while IFS= read -r file; do
  echo "=== $file ==="
  git diff learn..HEAD -- $file | head -30
done < remaining-diffs.txt
```

### Phase 5: 提交和文档

```bash
# 1. 提交所有变更
git add libs/code/
git commit -m "feat: migrate all zjcode custom features from learn branch

- Migrated $(wc -l < ~/.zjcode/tmp/migration-*/new-files.txt) new files
- Merged $(wc -l < ~/.zjcode/tmp/migration-*/modified-files.txt) modified files
- Applied brand isolation (deepagents-code → zjcode)
- All unit tests passing

Migration report: ~/.zjcode/tmp/migration-*/"

# 2. 生成迁移报告
cat > ~/.zjcode/tmp/migration-report-$(date +%Y%m%d).md << EOF
# 迁移报告 $(date +%Y%m%d)

## 基础信息
- 源分支: learn
- 目标分支: main (最新)
- 迁移分支: migrate-zjcode-$(date +%Y%m%d)

## 变更统计
- 新增文件: $(wc -l < ~/.zjcode/tmp/migration-*/new-files.txt)
- 修改文件: $(wc -l < ~/.zjcode/tmp/migration-*/modified-files.txt)
- 删除文件: $(wc -l < ~/.zjcode/tmp/migration-*/deleted-files.txt)

## 验证结果
- [ ] 包导入成功
- [ ] CLI 命令正常
- [ ] 单元测试通过
- [ ] 品牌隔离完成
- [ ] 与 learn 分支差异已确认

## 详细文件列表
见 ~/.zjcode/tmp/migration-*/
EOF
```

## 关键原则

### 1. 动态发现，不要硬编码

**错误做法**：维护一个静态的文件列表或功能清单
```bash
# ❌ 不要这样做
FILES="clipboard.py media_utils.py ..."
for file in $FILES; do ...
```

**正确做法**：每次迁移时动态发现
```bash
# ✓ 这样做
git diff main..learn --name-only -- libs/code/deepagents_code/
```

### 2. 从 learn 分支的当前状态出发

不要假设 learn 分支只有某些功能，每次都从 `git diff` 的结果出发。

### 3. 区分 Python 模块名和 PyPI 包名

- **Python 模块名**：`deepagents_code`（不要改）
- **PyPI 包名**：`zjcode`（用户可见的）
- **导入语句**：`from deepagents_code.xxx import ...`（不要改）
- **用户字符串**：`"zjcode"`, `"~/.zjcode"`（要改）

### 4. 验证是最后一步，不是可选的

每次迁移后必须运行完整的验证流程，确保：
- 所有文件都已迁移
- 所有测试都通过
- 品牌隔离完成
- 与 learn 分支的差异都是预期的

## 常见问题

### Q: learn 分支新增了功能怎么办？

A: 重新运行 Phase 1 的差异发现流程，`git diff` 会自动发现所有新增的文件和修改。

### Q: main 分支也更新了怎么办？

A: 这正是迁移的目的。基于最新的 main 创建新分支，然后将 learn 的自定义功能合并进去。冲突需要手动解决。

### Q: 如何确认没有遗漏？

A: 运行 Phase 4 的验证流程，特别是 4.1 的文件完整性检查和 4.3 的差异对比验证。如果 `remaining-diffs.txt` 只包含品牌替换相关的差异，说明迁移完整。

### Q: 迁移后测试失败怎么办？

A: 检查是否是品牌替换导致的（预期内的），还是功能缺失导致的。如果是功能缺失，回到 Phase 1 重新检查差异报告。

## References

- 迁移脚本目录：`~/.zjcode/agent/skills/zjcode-feature-migration/scripts/`
- 历史迁移报告：`~/.zjcode/tmp/migration-report-*.md`
- 品牌隔离指南：见 Phase 3.3
- 冲突解决策略：见迁移报告中的记录
