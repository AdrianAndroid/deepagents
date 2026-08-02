#!/bin/bash
# Generate migration report for zjcode feature migration
# Usage: generate-report.sh [output_dir]

set -e

OUTPUT_DIR="${1:-$HOME/.zjcode/tmp}"
mkdir -p "$OUTPUT_DIR"

echo "Generating migration report..."
echo "Output directory: $OUTPUT_DIR"

# 1. Commit list with details
echo "1. Generating commit list..."
git log --author="zhaojian" --author="ext_zhaojian03" --all \
  --format="%H|%s|%ai|%an" --no-merges > "$OUTPUT_DIR/commits.txt"
echo "   ✓ Saved to $OUTPUT_DIR/commits.txt"

# 2. Changed files statistics
echo "2. Generating file change statistics..."
git log --author="zhaojian" --author="ext_zhaojian03" --all \
  --name-only --format="" --no-merges | \
  grep -v "^$" | sort | uniq -c | sort -rn > "$OUTPUT_DIR/changed-files.txt"
echo "   ✓ Saved to $OUTPUT_DIR/changed-files.txt"

# 3. Generate comprehensive patch
echo "3. Generating comprehensive patch..."
if git diff main..learn -- libs/code/ > "$OUTPUT_DIR/zjcode-all-changes.patch" 2>/dev/null; then
  PATCH_SIZE=$(wc -l < "$OUTPUT_DIR/zjcode-all-changes.patch")
  echo "   ✓ Saved to $OUTPUT_DIR/zjcode-all-changes.patch ($PATCH_SIZE lines)"
else
  echo "   ⚠ Failed to generate patch (main..learn diff not available)"
fi

# 4. Generate feature-specific patches
echo "4. Generating feature-specific patches..."
mkdir -p "$OUTPUT_DIR/patches"

# Brand isolation patch
if git diff main..learn -- libs/code/deepagents_code/config.py \
  libs/code/deepagents_code/model_config.py \
  libs/code/deepagents_code/update_check.py \
  libs/code/pyproject.toml > "$OUTPUT_DIR/patches/brand-isolation.patch" 2>/dev/null; then
  echo "   ✓ brand-isolation.patch"
fi

# Clipboard feature patch
if git diff main..learn -- libs/code/deepagents_code/clipboard.py \
  libs/code/deepagents_code/media_utils.py > "$OUTPUT_DIR/patches/clipboard-feature.patch" 2>/dev/null; then
  echo "   ✓ clipboard-feature.patch"
fi

# Model selector patch
if git diff main..learn -- libs/code/deepagents_code/tui/widgets/model_selector.py \
  libs/code/deepagents_code/model_config.py > "$OUTPUT_DIR/patches/model-selector.patch" 2>/dev/null; then
  echo "   ✓ model-selector.patch"
fi

# Session tracking patch
if git diff main..learn -- libs/code/deepagents_code/turn_end_summary.py \
  libs/code/deepagents_code/tui/textual_adapter.py > "$OUTPUT_DIR/patches/session-tracking.patch" 2>/dev/null; then
  echo "   ✓ session-tracking.patch"
fi

# 5. Summary report
echo "5. Generating summary report..."
cat > "$OUTPUT_DIR/migration-summary.md" << EOF
# zjcode Migration Summary

Generated: $(date '+%Y-%m-%d %H:%M:%S')

## Statistics

- Total commits: $(wc -l < "$OUTPUT_DIR/commits.txt")
- Total changed files: $(wc -l < "$OUTPUT_DIR/changed-files.txt")
- Total patch size: $(wc -l < "$OUTPUT_DIR/zjcode-all-changes.patch" 2>/dev/null || echo 0) lines

## Commit List

See: commits.txt

## Changed Files (Top 20)

\`\`\`
$(head -20 "$OUTPUT_DIR/changed-files.txt")
\`\`\`

## Migration Patches

Available in: patches/
- brand-isolation.patch
- clipboard-feature.patch
- model-selector.patch
- session-tracking.patch

## Next Steps

1. Review patches in patches/ directory
2. Create migration branch from main
3. Apply patches in order
4. Resolve conflicts using conflict-examples.md
5. Run validation checks

EOF

echo "   ✓ Saved to $OUTPUT_DIR/migration-summary.md"

echo ""
echo "Migration report generation complete!"
echo "View summary: cat $OUTPUT_DIR/migration-summary.md"
