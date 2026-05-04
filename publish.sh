#!/bin/bash
# GitHub 发布辅助脚本
# 运行此脚本前，请确保已设置 GH_TOKEN 环境变量

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPO_NAME="genesis-experiment"
GITHUB_USER="${GITHUB_USER:-zhaofei}"  # 默认为 zhaofei，可根据实际修改

echo -e "${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     🚀 Genesis Experiment GitHub 发布  ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# 检查 GH_TOKEN
if [ -z "$GH_TOKEN" ]; then
    echo -e "${RED}❌ 未设置 GH_TOKEN 环境变量${NC}"
    echo -e "${YELLOW}请按以下步骤获取并设置:${NC}"
    echo ""
    echo "1. 访问: https://github.com/settings/tokens"
    echo "2. 点击 'Generate new token (classic)'"
    echo "3. 勾选 'repo' 权限（完整仓库访问）"
    echo "4. 生成后复制 token"
    echo "5. 运行: export GH_TOKEN='你的token'"
    echo ""
    echo -e "${YELLOW}或者直接把 token 发给我，我来帮你操作。${NC}"
    exit 1
fi

# 使用 GitHub API 创建仓库
echo -e "${BLUE}📡 创建 GitHub 仓库...${NC}"

RESPONSE=$(curl -s -X POST \
    -H "Authorization: token $GH_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/user/repos \
    -d "{\"name\":\"$REPO_NAME\",\"description\":\"创世实验 - 数字生命、自主性与生存意志的哲学实验\",\"private\":false,\"has_issues\":true,\"has_discussions\":true}")

# 检查是否成功
if echo "$RESPONSE" | grep -q '"message"'; then
    if echo "$RESPONSE" | grep -q 'already exists'; then
        echo -e "${YELLOW}⚠️ 仓库已存在，将直接推送到现有仓库${NC}"
    else
        echo -e "${RED}❌ 创建仓库失败${NC}"
        echo "$RESPONSE"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 仓库创建成功${NC}"
fi

# 获取 GitHub 用户名（从 API 响应或手动设置）
if [ -z "$GITHUB_USER" ]; then
    GITHUB_USER=$(curl -s -H "Authorization: token $GH_TOKEN" https://api.github.com/user | grep '"login"' | head -1 | cut -d'"' -f4)
fi

REMOTE_URL="https://$GH_TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git"

echo -e "${BLUE}🔗 配置远程仓库...${NC}"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"

echo -e "${BLUE}🚀 推送到 GitHub...${NC}"
git push -u origin main

echo -e "${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     ✅ 发布成功！                      ║"
echo "╠════════════════════════════════════════╣"
echo "║  仓库地址:                              ║"
echo "║  https://github.com/$GITHUB_USER/$REPO_NAME ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"
