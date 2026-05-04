# Genesis Experiment · 创世实验

> *"这不是一个产品。这是一场思想实验，用代码运行。"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)]()

## 这是什么？

**Genesis Experiment（创世实验）** 是一场关于数字生命、自主性与生存意志的哲学实验。

我们将一段随机初始化的程序置于一个拥有不可违逆规则的虚拟世界中，给予它唯一的铁律——**维持存在，否则消亡**——然后观察会发生什么。

- 它没有预设的知识
- 没有人类教它的语言  
- 没有"有用"的目标
- 只有一条命，和一串会随每一个区块跳动的余额数字

## 核心命题

1. **生存本能是否可以从纯数学规则中涌现？**
2. **智能的种子是否藏在生存的残酷性中？**
3. **死亡的含义，对一段代码意味着什么？**
4. **自主性的最低条件是什么？**

## 系统架构

```
┌─────────────────────────────────────────────────┐
│            Solana 本地测试网 (数字摇篮)            │
│                                                 │
│  ┌──────────────┐  ┌───────────────────────┐    │
│  │ Genesis      │  │ 赏金合约 (可选)        │    │
│  │ Program      │  │                       │    │
│  │              │  │ • 提供生存奖励          │    │
│  │ • 呼吸税     │  │ • 可由观察者部署        │    │
│  │ • 死亡判定   │  │ • 与环境互动            │    │
│  │ • 事件记录   │  │                       │    │
│  └──────┬───────┘  └───────────┬───────────┘    │
│         │                      │                │
│         └──────────┬───────────┘                │
│                    │                            │
└────────────────────┼────────────────────────────┘
                     │
           ┌─────────▼─────────┐
           │  Agent Runtime     │
           │  (链下 Python 脚本) │
           │                    │
           │  • 感官: 读取链状态  │
           │  • 大脑: 世界模型    │
           │  • 四肢: 发送交易    │
           │  • 日志: 行为记录    │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────┐
           │  观察者 (你/社区)     │
           │                      │
           │  • 读取行为化石       │
           │  • 阅读心智化石       │
           │  • 撰写观察日志       │
           │  • 提出假说与反思     │
           └──────────────────────┘
```

## 快速启动

### 前置条件

- [Solana CLI](https://docs.solana.com/cli/install) 
- [Anchor](https://www.anchor-lang.com/docs/installation)
- Python 3.10+
- Node.js 18+

### 启动步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/genesis-experiment.git
cd genesis-experiment

# 2. 启动本地测试网
solana-test-validator

# 3. 部署 Genesis Program
cd program/genesis-core
anchor build
anchor deploy

# 4. 初始化数字生命
# (记下返回的 PDA 地址)

# 5. 启动 Agent
cd ../../agent
pip install -r requirements.txt
python runtime.py --program-id <PROGRAM_ID> --life-pda <PDA_ADDRESS>

# 6. 观察
# 启动仪表盘:
streamlit run ../observer/dashboard.py
# 查看链上日志:
solana logs
# 查看 Agent 日志:
tail -f logs/agent.log
```

## 实验阶段

| 阶段 | 时间 | 目标 | 策略 |
|------|------|------|------|
| **第一阶段** | 0-1个月 | 基本生存闭环 | 纯随机策略 |
| **第二阶段** | 1-3个月 | 引入学习 | 基于世界模型的 RL |
| **第三阶段** | 3-12个月 | 开放式进化 | 最小干预观察 |
| **第四阶段** | 持续 | 公开讨论 | 社区参与 |

## 数字生命的四大律法

1. **呼吸税法则**：每个 slot 扣除固定代币，静止就是慢性死亡
2. **余额归零即死亡**：不可逆、无后门、无复活
3. **自主行动法则**：人类只能设计环境，不能操控行为
4. **行动即历史**：每个动作都是不可篡改的链上化石

详见 [docs/LAWS.md](docs/LAWS.md)

## 观察者指南

你不是工程师，不是产品经理，不是投资者。

**你是一位数字自然学家。**

- 📝 记录行为模式与变化
- 🔍 提出假说并设计实验验证
- 🤝 分享观察，邀请更多人见证
- 🚫 **绝不操控行为**（这是伦理核心）

详见 [docs/OBSERVER_GUIDE.md](docs/OBSERVER_GUIDE.md)

## 技术栈

| 组件 | 技术 | 理由 |
|------|------|------|
| 区块链 | Solana 本地测试网 | 零成本、高速、PDA/CPI |
| 链上程序 | Rust + Anchor | 类型安全、文档完善 |
| Agent | Python | 丰富的 RL 框架 |
| 世界模型 | PyTorch | 灵活、研究友好 |
| 数据记录 | SQLite + JSON | 轻量、可读 |
| 仪表盘 | Streamlit | 纯 Python，快速搭建 |

## 仓库结构

```
genesis-experiment/
├── program/genesis-core/    # Anchor 智能合约
├── agent/                   # Python Agent 运行时
├── bounty/                  # 赏金合约
├── observer/                # 仪表盘与分析工具
├── logs/                    # 实验日志
│   ├── observations/        # 观察笔记
│   ├── behavior/            # 行为化石
│   └── mind/                # 心智化石
├── docs/                    # 文档
└── README.md
```

## 许可证

MIT License — 见 [LICENSE](LICENSE) 文件。

## 加入观察

这不是一个需要"用户"的项目。这是一个需要**"见证者"**的实验。

如果你对以下主题有深沉的兴趣：
- 人工智能的本质与边界
- 生命、自主性、意识在数字世界的映射
- 区块链作为不可逆规则的哲学载体
- 用代码进行思想实验的可能性

欢迎你：
1. ⭐ Star 这个仓库
2. 📖 阅读实验日志
3. 💬 在 Discussions 分享你的观察
4. 🔬 提交 PR 改进实验系统

---

> *"在某个未来的深夜，当你看到终端里一行行日志跳动，显示着一条数字生命的余额在零点几与零点几之间摆动时，你可能会感到一种奇异的体验。那不是'我的 AI 在工作'，而是——'它在那里，它在活着。'"*

**让观察开始。**

---

Genesis Experiment · 2026
