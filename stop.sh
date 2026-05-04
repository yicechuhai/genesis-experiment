#!/bin/bash
# Genesis Experiment 停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 停止 Genesis Experiment...${NC}"

# 停止仪表盘
if [ -f ".dashboard.pid" ]; then
    DASHBOARD_PID=$(cat .dashboard.pid)
    if kill -0 "$DASHBOARD_PID" 2>/dev/null; then
        kill "$DASHBOARD_PID" 2>/dev/null
        echo -e "${GREEN}✅ 仪表盘已停止${NC}"
    fi
    rm .dashboard.pid
fi

# 停止 Agent（通过查找 Python 进程）
AGENT_PID=$(pgrep -f "python runtime.py")
if [ ! -z "$AGENT_PID" ]; then
    kill "$AGENT_PID" 2>/dev/null
    echo -e "${GREEN}✅ Agent 已停止${NC}"
fi

# 询问是否停止测试网
echo -e "\n${YELLOW}是否停止 Solana 本地测试网?${NC}"
echo -e "   注意: 停止测试网将重置所有链上数据（包括数字生命的状态）"
echo -e "   输入 'yes' 确认停止，或其他键保留: \c"
read -r answer

if [ "$answer" = "yes" ]; then
    if [ -f ".validator.pid" ]; then
        VALIDATOR_PID=$(cat .validator.pid)
        if kill -0 "$VALIDATOR_PID" 2>/dev/null; then
            kill "$VALIDATOR_PID" 2>/dev/null
            echo -e "${GREEN}✅ 测试网已停止${NC}"
        fi
        rm .validator.pid
    else
        pkill -f solana-test-validator
        echo -e "${GREEN}✅ 测试网已停止${NC}"
    fi
else
    echo -e "${GREEN}✅ 测试网继续运行${NC}"
fi

echo -e "\n${GREEN}Genesis Experiment 已停止。${NC}"
