#!/bin/bash
# zjcode 品牌完整性检查脚本
# 每次合并 main 分支后运行

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 检查 zjcode 品牌定制完整性...${NC}"
echo ""

ERRORS=0
WARNINGS=0

# 检查 1: zjcode 目录存在
if [ ! -d "libs/code/zjcode" ]; then
    echo -e "${RED}❌ 严重: zjcode 目录不存在！${NC}"
    echo "   恢复命令: git checkout HEAD -- libs/code/zjcode/"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ zjcode 目录存在${NC}"
fi

# 检查 2: 关键品牌文件
for file in "zjcode/brand.py" "zjcode/patches.py" "zjcode/mcp_trust.py" "zjcode/todo_list_prompt.md" "zjcode/__init__.py"; do
    if [ ! -f "libs/code/$file" ]; then
        echo -e "${RED}❌ 丢失: $file${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# 检查 3: __init__.py 中的钩子
grep -q "zjcode" libs/code/deepagents_code/__init__.py
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  警告: __init__.py 中可能缺少 zjcode 钩子${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ __init__.py 钩子存在${NC}"
fi

# 检查 4: DISTRIBUTION_NAME 常量
grep -q 'DISTRIBUTION_NAME.*zjcode' libs/code/zjcode/brand.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ brand.py 中 DISTRIBUTION_NAME 不是 zjcode${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ brand.py 中 DISTRIBUTION_NAME = zjcode${NC}"
fi

# 检查 5: 确认上游文件已恢复为默认值
grep -q 'CONFIG_DOTDIR.*\.deepagents' libs/code/deepagents_code/_constants.py
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  警告: _constants.py 中 CONFIG_DOTDIR 可能未恢复为上游默认值${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ _constants.py 已恢复上游默认值${NC}"
fi

# 检查 6: 确认上游不再有 mcp_trust.py
if [ -f "libs/code/deepagents_code/mcp_trust.py" ]; then
    echo -e "${YELLOW}⚠️  警告: deepagents_code/mcp_trust.py 应该已被移动到 zjcode/ 目录${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ mcp_trust.py 已迁移到 zjcode/ 目录${NC}"
fi

echo ""
echo "==================== 汇总 ===================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有品牌定制检查通过！${NC}"
    echo -e "${GREEN}   下次合并 main 分支应该几乎没有冲突${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  通过，但有 $WARNINGS 个警告${NC}"
    exit 0
else
    echo -e "${RED}❌ 发现 $ERRORS 个错误, $WARNINGS 个警告${NC}"
    echo ""
    echo "修复建议："
    echo "1. 确保 git checkout 时保留 zjcode/ 目录"
    echo "2. 检查 __init__.py 中的补丁钩子"
    exit 1
fi
