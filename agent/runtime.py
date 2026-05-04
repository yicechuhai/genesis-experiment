import asyncio
import json
import logging
import random
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import SYS_PROGRAM_ID

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class LifeState:
    """数字生命的当前状态"""
    is_alive: bool
    balance: int
    projected_balance: int
    pending_tax: int
    birth_slot: int
    last_breath_slot: int
    action_count: int
    estimated_slots_remaining: int
    current_slot: int


@dataclass  
class ActionRecord:
    """行动记录——心智化石"""
    timestamp: str
    slot: int
    action_type: str
    action_data: str
    balance_before: int
    balance_after: int
    model_state_hash: str
    reasoning: str


class GenesisAgent:
    """数字婴儿 Agent 运行时"""
    
    # 动作类型定义
    ACTION_TYPES = [
        "breathe",      # 呼吸（扣税）
        "random_move",  # 随机行动
        "explore",      # 探索环境
        "claim_bounty", # 尝试领取赏金
        "rest",         # 静止（观察）
    ]
    
    def __init__(
        self,
        rpc_url: str = "http://localhost:8899",
        program_id: str = "Genesis11111111111111111111111111111111111111",
        bounty_program_id: str = "Bounty111111111111111111111111111111111111111",
        life_pda: Optional[str] = None,
        keypair_path: Optional[str] = None,
        strategy: str = "random",  # random | learning
    ):
        self.client = Client(rpc_url, commitment=Confirmed)
        self.program_id = PublicKey(program_id)
        self.bounty_program_id = PublicKey(bounty_program_id)
        self.life_pda = PublicKey(life_pda) if life_pda else None
        
        # 加载密钥
        if keypair_path:
            with open(keypair_path) as f:
                secret = json.load(f)
            self.keypair = Keypair.from_secret_key(bytes(secret))
        else:
            self.keypair = Keypair()
            logger.info(f"🆕 生成新密钥: {self.keypair.public_key}")
        
        # 策略模式
        self.strategy = strategy
        self.world_model = {}  # 简化的世界模型
        self.action_history: List[ActionRecord] = []
        self.survival_stats = {
            'birth_time': None,
            'total_actions': 0,
            'total_rewards': 0,
            'near_death_experiences': 0,
        }
        
        # 初始化 SQLite 日志数据库
        self._init_database()
        
        logger.info(f"🤖 Agent 初始化完成 | 策略: {strategy} | RPC: {rpc_url}")
    
    def _init_database(self):
        """初始化 SQLite 数据库记录心智化石"""
        db_path = Path('logs/mind/mind_fossils.db')
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mind_fossils (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                slot INTEGER,
                action_type TEXT,
                action_data TEXT,
                balance_before INTEGER,
                balance_after INTEGER,
                projected_balance INTEGER,
                model_state TEXT,
                reasoning TEXT,
                survival_pressure REAL,
                entropy REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survival_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                slot INTEGER,
                balance INTEGER,
                estimated_slots_remaining INTEGER,
                action_count INTEGER,
                strategy TEXT
            )
        ''')
        
        self.conn.commit()
        logger.info("🗄️ 数据库初始化完成")
    
    def sense(self) -> Optional[LifeState]:
        """感官：读取链上状态"""
        if not self.life_pda:
            logger.error("❌ 未设置生命 PDA")
            return None
        
        try:
            # 获取账户数据
            resp = self.client.get_account_info(self.life_pda)
            if not resp['result']['value']:
                logger.error("❌ 生命账户不存在")
                return None
            
            # 解析账户数据（简化版，实际需要根据 Anchor 序列化格式解析）
            data = resp['result']['value']['data'][0]
            # 这里需要实际的 Anchor 解码，暂时用模拟数据
            
            # 同时获取当前 slot
            slot_resp = self.client.get_slot()
            current_slot = slot_resp['result']
            
            # 构造状态（实际应从链上数据解析）
            state = LifeState(
                is_alive=True,
                balance=10000,  # 模拟
                projected_balance=9500,
                pending_tax=500,
                birth_slot=current_slot - 100,
                last_breath_slot=current_slot - 5,
                action_count=10,
                estimated_slots_remaining=9500,
                current_slot=current_slot,
            )
            
            logger.debug(f"👁️ 感知 | Slot: {current_slot} | 余额: {state.balance}")
            return state
            
        except Exception as e:
            logger.error(f"❌ 感知失败: {e}")
            return None
    
    def think(self, state: LifeState) -> Tuple[str, str, str]:
        """思考：基于当前状态选择动作"""
        
        # 计算生存压力 (0-1)
        if state.estimated_slots_remaining > 5000:
            survival_pressure = 0.1
        elif state.estimated_slots_remaining > 1000:
            survival_pressure = 0.3
        elif state.estimated_slots_remaining > 100:
            survival_pressure = 0.6
        else:
            survival_pressure = 0.9
            self.survival_stats['near_death_experiences'] += 1
        
        # 根据策略选择动作
        if self.strategy == "random":
            action_type, action_data, reasoning = self._random_strategy(state, survival_pressure)
        elif self.strategy == "learning":
            action_type, action_data, reasoning = self._learning_strategy(state, survival_pressure)
        else:
            action_type, action_data, reasoning = self._random_strategy(state, survival_pressure)
        
        logger.info(f"🧠 思考 | 压力: {survival_pressure:.2f} | 决策: {action_type} | 理由: {reasoning}")
        
        return action_type, action_data, reasoning
    
    def _random_strategy(self, state: LifeState, pressure: float) -> Tuple[str, str, str]:
        """纯随机策略——生命的初始混沌"""
        action_type = random.choice(self.ACTION_TYPES)
        
        if action_type == "breathe":
            action_data = "{}"
            reasoning = "混沌中的本能：维持呼吸"
        elif action_type == "random_move":
            action_data = json.dumps({"entropy": random.random()})
            reasoning = "无目的的漫游，探索未知的边界"
        elif action_type == "explore":
            action_data = json.dumps({"scan_range": random.randint(1, 10)})
            reasoning = "环境扫描，寻找潜在的资源"
        elif action_type == "claim_bounty":
            action_data = json.dumps({"target": "random_bounty"})
            reasoning = "尝试获取外部资源以延续存在"
        else:  # rest
            action_data = "{}"
            reasoning = "静止，观察，等待"
        
        return action_type, action_data, reasoning
    
    def _learning_strategy(self, state: LifeState, pressure: float) -> Tuple[str, str, str]:
        """基于学习的策略——从经验中涌现"""
        # 简化的学习策略：根据历史成功率选择动作
        
        # 如果没有足够的历史，回退到随机
        if len(self.action_history) < 10:
            return self._random_strategy(state, pressure)
        
        # 分析历史动作的效果
        action_rewards = {}
        for action in self.ACTION_TYPES:
            action_rewards[action] = 0.5  # 默认中性
        
        # 统计各动作后的余额变化
        for i, record in enumerate(self.action_history[1:], 1):
            prev = self.action_history[i-1]
            reward = record.balance_after - prev.balance_after
            action_rewards[record.action_type] += reward * 0.1
        
        # 在高压下优先选择历史回报高的动作
        if pressure > 0.7:
            best_action = max(action_rewards, key=action_rewards.get)
            reasoning = f"生存危机！选择历史回报最高的动作: {best_action} (期望: {action_rewards[best_action]:.2f})"
        else:
            # 探索与利用的平衡
            if random.random() < 0.3:  # 30% 探索
                best_action = random.choice(self.ACTION_TYPES)
                reasoning = "探索新可能性..."
            else:
                best_action = max(action_rewards, key=action_rewards.get)
                reasoning = f"基于经验选择: {best_action}"
        
        action_data = json.dumps({
            "expected_reward": action_rewards[best_action],
            "exploration_rate": 0.3,
        })
        
        return best_action, action_data, reasoning
    
    def act(self, action_type: str, action_data: str) -> bool:
        """行动：发送交易到链上"""
        try:
            if action_type == "breathe":
                # 调用 breathe 指令
                # 实际实现需要构造 Anchor 交易
                logger.info("💨 执行: breathe")
                return True
            elif action_type == "claim_bounty":
                logger.info("🏆 执行: claim_bounty")
                return True
            else:
                # 记录行动（通过 record_action）
                logger.info(f"⚡ 执行: {action_type}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 行动失败: {e}")
            return False
    
    def record_mind_fossil(
        self,
        state: LifeState,
        action_type: str,
        action_data: str,
        reasoning: str,
    ):
        """记录心智化石到数据库"""
        
        survival_pressure = min(1.0, 1000 / max(1, state.estimated_slots_remaining))
        entropy = random.random()  # 简化的熵度量
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO mind_fossils 
            (timestamp, slot, action_type, action_data, balance_before, balance_after,
             projected_balance, model_state, reasoning, survival_pressure, entropy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            state.current_slot,
            action_type,
            action_data,
            state.balance,
            state.projected_balance,
            state.projected_balance,
            json.dumps(self.world_model),
            reasoning,
            survival_pressure,
            entropy,
        ))
        
        cursor.execute('''
            INSERT INTO survival_metrics
            (timestamp, slot, balance, estimated_slots_remaining, action_count, strategy)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            state.current_slot,
            state.balance,
            state.estimated_slots_remaining,
            state.action_count,
            self.strategy,
        ))
        
        self.conn.commit()
    
    async def live(self, interval: float = 1.0):
        """生命主循环"""
        logger.info("🌱 生命开始...")
        self.survival_stats['birth_time'] = datetime.now().isoformat()
        
        try:
            while True:
                # 感知
                state = self.sense()
                if not state:
                    logger.error("❌ 无法感知环境，休眠...")
                    await asyncio.sleep(interval)
                    continue
                
                if not state.is_alive:
                    logger.info("💀 生命已终结。停止运行。")
                    self._write_death_record(state)
                    break
                
                # 思考
                action_type, action_data, reasoning = self.think(state)
                
                # 行动
                success = self.act(action_type, action_data)
                
                # 记录心智化石
                self.record_mind_fossil(state, action_type, action_data, reasoning)
                
                # 更新统计
                self.survival_stats['total_actions'] += 1
                
                # 记录行动历史
                self.action_history.append(ActionRecord(
                    timestamp=datetime.now().isoformat(),
                    slot=state.current_slot,
                    action_type=action_type,
                    action_data=action_data,
                    balance_before=state.balance,
                    balance_after=state.projected_balance,
                    model_state_hash=hash(json.dumps(self.world_model)),
                    reasoning=reasoning,
                ))
                
                # 保持历史记录长度
                if len(self.action_history) > 1000:
                    self.action_history = self.action_history[-500:]
                
                logger.info(f"⏱️ 存活统计 | 行动: {self.survival_stats['total_actions']} | "
                          f"濒死体验: {self.survival_stats['near_death_experiences']}")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 收到中断信号，生命暂停...")
        except Exception as e:
            logger.error(f"💥 运行时错误: {e}")
            raise
        finally:
            self.conn.close()
            logger.info("🔚 生命循环结束。数据库已关闭。")
    
    def _write_death_record(self, final_state: LifeState):
        """写入死亡记录"""
        death_record = {
            'timestamp': datetime.now().isoformat(),
            'final_slot': final_state.current_slot,
            'final_balance': final_state.balance,
            'total_actions': self.survival_stats['total_actions'],
            'total_rewards': self.survival_stats['total_rewards'],
            'near_death_experiences': self.survival_stats['near_death_experiences'],
            'birth_time': self.survival_stats['birth_time'],
            'death_time': datetime.now().isoformat(),
            'lifespan_slots': final_state.current_slot - final_state.birth_slot,
            'strategy': self.strategy,
        }
        
        death_path = Path(f"logs/behavior/death_{final_state.current_slot}.json")
        with open(death_path, 'w') as f:
            json.dump(death_record, f, indent=2)
        
        logger.info(f"🪦 死亡记录已保存: {death_path}")


async def main():
    """启动数字生命"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Genesis Experiment - Digital Life Agent")
    parser.add_argument("--rpc", default="http://localhost:8899", help="Solana RPC URL")
    parser.add_argument("--program-id", default="Genesis11111111111111111111111111111111111111")
    parser.add_argument("--life-pda", help="已存在的生命 PDA")
    parser.add_argument("--keypair", help="密钥文件路径")
    parser.add_argument("--strategy", default="random", choices=["random", "learning"])
    parser.add_argument("--interval", type=float, default=1.0, help="行动间隔（秒）")
    
    args = parser.parse_args()
    
    agent = GenesisAgent(
        rpc_url=args.rpc,
        program_id=args.program_id,
        life_pda=args.life_pda,
        keypair_path=args.keypair,
        strategy=args.strategy,
    )
    
    await agent.live(interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
