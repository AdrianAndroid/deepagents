#!/bin/bash
# Check brand consistency in zjcode
# Usage: check-brand.sh [directory]

set -e

CHECK_DIR="${1:-libs/code}"

if [ ! -d "$CHECK_DIR" ]; then
  echo "Error: Directory $CHECK_DIR does not exist"
  exit 1
fi

echo "Checking brand consistency in $CHECK_DIR..."
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FOUND=0

# Check 1: deepagents-code references
echo "1. Checking for 'deepagents-code' references..."
RESULTS=$(grep -r "deepagents-code" "$CHECK_DIR" \
  --include="*.py" --include="*.md" --include="*.toml" \
  2>/dev/null | \
  grep -v "test_\|tests/\|CHANGELOG\|uv\.lock\|\.venv\|upstream\|original" || true)

if [ -n "$RESULTS" ]; then
  echo -e "${RED}✗ Found 'deepagents-code' references:${NC}"
  echo "$RESULTS"
  FOUND=1
else
  echo -e "${GREEN}✓ No 'deepagents-code' references found${NC}"
fi
echo ""

# Check 2: DeepAgents references
echo "2. Checking for 'DeepAgents' references..."
RESULTS=$(grep -r "DeepAgents\|Deep Agents" "$CHECK_DIR" \
  --include="*.py" --include="*.md" --include="*.toml" \
  2>/dev/null | \
  grep -v "test_\|tests/\|CHANGELOG\|uv\.lock\|\.venv\|upstream\|original" || true)

if [ -n "$RESULTS" ]; then
  echo -e "${RED}✗ Found 'DeepAgents' references:${NC}"
  echo "$RESULTS"
  FOUND=1
else
  echo -e "${GREEN}✓ No 'DeepAgents' references found${NC}"
fi
echo ""

# Check 3: .deepagents path references
echo "3. Checking for '.deepagents' path references..."
RESULTS=$(grep -r "\.deepagents" "$CHECK_DIR" \
  --include="*.py" --include="*.md" --include="*.toml" \
  2>/dev/null | \
  grep -v "test_\|tests/\|CHANGELOG\|uv\.lock\|\.venv\|upstream\|original" | \
  grep -v "deepagents_langchain\|lc_versions\.deepagents" || true)

if [ -n "$RESULTS" ]; then
  echo -e "${RED}✗ Found '.deepagents' path references:${NC}"
  echo "$RESULTS"
  FOUND=1
else
  echo -e "${GREEN}✓ No '.deepagents' path references found${NC}"
fi
echo ""

# Check 4: Distribution name references
echo "4. Checking for distribution name references..."
RESULTS=$(grep -r "distribution(\"deepagents-code\")\|pkg_version(\"deepagents-code\")" "$CHECK_DIR" \
  --include="*.py" \
  2>/dev/null || true)

if [ -n "$RESULTS" ]; then
  echo -e "${RED}✗ Found old distribution name references:${NC}"
  echo "$RESULTS"
  FOUND=1
else
  echo -e "${GREEN}✓ No old distribution name references found${NC}"
fi
echo ""

# Summary
echo "========================================"
if [ $FOUND -eq 0 ]; then
  echo -e "${GREEN}✓ All brand checks passed!${NC}"
  exit 0
else
  echo -e "${RED}✗ Brand consistency check failed${NC}"
  echo ""
  echo "To fix these issues:"
  echo "1. Replace 'deepagents-code' with 'zjcode'"
  echo "2. Replace 'Deep Agents' with 'zjcode'"
  echo "3. Replace '.deepagents' with '.zjcode'"
  echo "4. Update distribution names to 'zjcode'"
  echo ""
  echo "Note: Keep 'deepagents_code' as the Python package name"
  echo "Note: Keep internal SDK references like 'deepagents_langchain_project'"
  exit 1
fi
