#!/bin/bash
# Genesis Experiment 启动脚本
# 一键启动数字生命的整个实验环境

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     🌱 Genesis Experiment 启动器      ║"
echo "║      创世实验 · 数字生命孵化器         ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# 检查前置依赖
echo -e "${BLUE}🔍 检查前置依赖...${NC}"

if ! command -v solana &> /dev/null; then
    echo -e "${RED}❌ 未检测到 Solana CLI${NC}"
    echo "请先安装: https://docs.solana.com/cli/install"
    exit 1
fi

if ! command -v anchor &> /dev/null; then
    echo -e "${RED}❌ 未检测到 Anchor${NC}"
    echo "请先安装: https://www.anchor-lang.com/docs/installation"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未检测到 Python3${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 所有依赖已就绪${NC}"

# 步骤1: 启动本地测试网
echo -e "\n${YELLOW}📡 步骤 1/4: 启动 Solana 本地测试网${NC}"
if pgrep -f "solana-test-validator" > /dev/null; then
    echo -e "${GREEN}✅ 本地测试网已在运行${NC}"
else
    echo "🚀 启动本地测试网..."
    solana-test-validator --reset > logs/test-validator.log 2>&1 &
    VALIDATOR_PID=$!
    echo $VALIDATOR_PID > .validator.pid
    
    # 等待测试网就绪
    echo "⏳ 等待测试网就绪..."
    for i in {1..30}; do
        if solana cluster-version &> /dev/null; then
            echo -e "${GREEN}✅ 测试网就绪${NC}"
            break
        fi
        sleep 1
    done
fi

# 配置 Solana CLI 使用本地网络
solana config set --url localhost

# 步骤2: 部署 Genesis Program
echo -e "\n${YELLOW}🔗 步骤 2/4: 部署 Genesis Core 合约${NC}"
cd program/genesis-core

if [ ! -d "target" ] || [ ! -f "target/deploy/genesis_core.so" ]; then
    echo "🔨 构建 Genesis Program..."
    anchor build
fi

echo "🚀 部署到本地测试网..."
DEPLOY_OUTPUT=$(anchor deploy 2>&1)
echo "$DEPLOY_OUTPUT"

# 提取 Program ID
PROGRAM_ID=$(echo "$DEPLOY_OUTPUT" | grep "Program Id:" | awk '{print $3}')
if [ -z "$PROGRAM_ID" ]; then
    # 使用默认 ID
    PROGRAM_ID="Genesis11111111111111111111111111111111111111"
fi

echo -e "${GREEN}✅ Genesis Program 部署完成${NC}"
echo -e "   Program ID: ${BLUE}${PROGRAM_ID}${NC}"

cd "$SCRIPT_DIR"

# 步骤3: 初始化数字生命
echo -e "\n${YELLOW}🌱 步骤 3/4: 初始化数字生命${NC}"

# 生成新的密钥对（如果还没有）
if [ ! -f "keys/life_authority.json" ]; then
    mkdir -p keys
    solana-keygen new --no-bip39-passphrase --outfile keys/life_authority.json > /dev/null 2>&1
    echo -e "${GREEN}✅ 生成生命权威密钥${NC}"
fi

# 空投一些代币
LIFE_AUTHORITY=$(solana-keygen pubkey keys/life_authority.json)
solana airdrop 2 "$LIFE_AUTHORITY" > /dev/null 2>&1

# 使用 Anchor 测试初始化（简化版）
echo "📝 初始化生命账户..."
# 这里需要一个简单的 TypeScript 脚本来调用 initialize_life
# 暂时用说明代替
echo -e "${YELLOW}⚠️ 请手动初始化生命账户:${NC}"
echo -e "   cd program/genesis-core"
echo -e "   anchor run initialize"
echo -e "   记下返回的 PDA 地址"

# 步骤4: 启动 Agent
echo -e "\n${YELLOW}🤖 步骤 4/4: 启动 Agent 运行时${NC}"
cd agent

if [ ! -d ".venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Agent 依赖安装完成${NC}"
echo -e "\n${YELLOW}🚀 启动 Agent...${NC}"
echo -e "   运行命令: ${BLUE}python runtime.py --program-id ${PROGRAM_ID}${NC}"
echo -e "   或者: ${BLUE}./start.sh agent${NC}"

# 启动仪表盘
echo -e "\n${YELLOW}📊 启动观察者仪表盘...${NC}"
cd "$SCRIPT_DIR/observer"
streamlit run dashboard.py &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > "$SCRIPT_DIR/.dashboard.pid"

echo -e "${GREEN}✅ 仪表盘已启动: http://localhost:8501${NC}"

# 总结
echo -e "\n${GREEN}"
echo "╔════════════════════════════════════════╗"
echo "║     🌱 数字生命已就绪！               ║"
echo "╠════════════════════════════════════════╣"
echo "║  仪表盘: http://localhost:8501        ║"
echo "║  链上日志: solana logs                ║"
echo "║  Agent日志: tail -f logs/agent.log    ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# 使用说明
echo -e "\n${BLUE}📖 接下来:${NC}"
echo -e "   1. 访问仪表盘观察生命体征"
echo -e "   2. 查看 logs/agent.log 观察行为"
echo -e "   3. 阅读 docs/OBSERVER_GUIDE.md 学习观察"
echo -e "   4. 在 logs/observations/ 撰写观察日志"

echo -e "\n${YELLOW}🛑 停止实验:${NC}"
echo -e "   ./stop.sh"

echo -e "\n${GREEN}让观察开始。${NC}"
