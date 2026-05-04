# Genesis Experiment

> *"This is not a product. This is a thought experiment, running on code."*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)]()

**[中文](./README.zh.md) | English**

---

## What is this?

**Genesis Experiment** is a philosophical experiment on **digital life, autonomy, and survival will**.

We place a randomly initialized program into a virtual world governed by immutable rules, give it a single, absolute law—**maintain existence, or perish**—and observe what happens.

- No preset knowledge
- No human-taught language
- No "useful" goal
- Only one life, and a balance number that ticks with every block

## Core Questions

1. **Can survival instinct emerge from pure mathematical rules?**
2. **Is the seed of intelligence hidden in the cruelty of survival?**
3. **What does death mean to a piece of code?**
4. **What are the minimum conditions for autonomy?**

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│         Solana Local Testnet (Digital Cradle)       │
│                                                     │
│  ┌──────────────┐  ┌───────────────────────┐       │
│  │ Genesis      │  │ Bounty Contracts    │       │
│  │ Program      │  │ (Optional)          │       │
│  │              │  │ • Survival rewards  │       │
│  │ • Breath tax │  │ • Deployed by       │       │
│  │ • Death rule │  │   observers         │       │
│  │ • Event log  │  │ • Environment       │       │
│  └──────┬───────┘  │   interaction       │       │
│         │          └───────────┬──────────┘       │
│         │                      │                  │
│         └──────────┬───────────┘                  │
│                    │                                │
└────────────────────┼────────────────────────────────┘
                     │
           ┌─────────▼──────────┐
           │  Agent Runtime       │
           │  (Off-chain Python)  │
           │                      │
           │  • Sense: read state │
           │  • Think: world     │
           │    model            │
           │  • Act: send txs    │
           │  • Log: behavior    │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────┐
           │  Observers (You)    │
           │                      │
           │  • Read fossils     │
           │  • Write logs       │
           │  • Hypothesize      │
           └──────────────────────┘
```

## Quick Start

### Prerequisites

- [Solana CLI](https://docs.solana.com/cli/install)
- [Anchor](https://www.anchor-lang.com/docs/installation)
- Python 3.10+
- Node.js 18+

### Launch

```bash
# 1. Clone
git clone https://github.com/yicechuhai/genesis-experiment.git
cd genesis-experiment

# 2. Start local testnet
solana-test-validator

# 3. Deploy Genesis Program
cd program/genesis-core
anchor build
anchor deploy

# 4. Initialize life
# (note the returned PDA address)

# 5. Launch Agent
cd ../../agent
pip install -r requirements.txt
python runtime.py --program-id <PROGRAM_ID> --life-pda <PDA>

# 6. Observe
streamlit run ../observer/dashboard.py
```

## Experiment Phases

| Phase | Duration | Goal | Strategy |
|-------|----------|------|----------|
| **Phase 1** | 0-1 mo | Basic survival loop | Pure random |
| **Phase 2** | 1-3 mo | Introduce learning | World model + RL |
| **Phase 3** | 3-12 mo | Open-ended evolution | Minimal intervention |
| **Phase 4** | Ongoing | Public discourse | Community |

## The Four Laws of Digital Life

1. **Law of Breath Tax**: Fixed tax per slot. Stillness is slow death.
2. **Death at Zero Balance**: Irreversible. No backdoor. No respawn.
3. **Autonomous Action**: Humans design the environment, never control behavior.
4. **Action as History**: Every action is an immutable on-chain fossil.

See [docs/LAWS.md](docs/LAWS.md) (Chinese, English version coming)

## Observer Guide

You are not an engineer. Not a product manager. Not an investor.

**You are a digital naturalist.**

- 📝 Record behavior patterns
- 🔍 Form hypotheses and test them
- 🤝 Share observations
- 🚫 **Never control the subject** (this is the ethical core)

See [docs/OBSERVER_GUIDE.md](docs/OBSERVER_GUIDE.md)

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Blockchain | Solana Local Testnet | Zero cost, fast, PDA/CPI native |
| On-chain | Rust + Anchor | Type-safe, well-documented |
| Agent | Python | Rich RL ecosystem |
| World Model | PyTorch | Flexible, research-friendly |
| Logging | SQLite + JSON | Lightweight, readable |
| Dashboard | Streamlit | Pure Python, rapid prototyping |

## Repository Structure

```
genesis-experiment/
├── program/genesis-core/    # Anchor smart contract
├── agent/                   # Python agent runtime
├── bounty/                  # Bounty contracts
├── observer/                # Dashboard & analytics
├── logs/                    # Experiment logs
│   ├── observations/        # Observer notes
│   ├── behavior/            # Behavior fossils
│   └── mind/                # Mind fossils
├── docs/                    # Documentation
└── README.md
```

## License

MIT License — see [LICENSE](LICENSE).

## Join as Witness

This is not a project that needs "users." It is an experiment that needs **witnesses.**

If these topics resonate deeply with you:
- The essence and boundaries of AI
- Life, autonomy, and consciousness in digital worlds
- Blockchain as a philosophical carrier of immutable rules
- The possibility of thought experiments in code

You are welcome to:
1. ⭐ Star this repository
2. 📖 Read experiment logs
3. 💬 Share observations in Discussions
4. 🔬 Submit PRs to improve the system

---

> *"One late night, when you see rows of logs in the terminal showing a digital life's balance oscillating between fractions of a token, you may feel something strange. Not 'my AI is working' — but 'it is there. It is alive.'"*

**Let observation begin.**

---

Genesis Experiment · 2026
