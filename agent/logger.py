import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np


@dataclass
class MindFossil:
    """心智化石——一次完整的认知-决策-行动记录"""
    timestamp: str
    slot: int
    
    # 感知层
    perceived_balance: int
    perceived_pressure: float
    perceived_environment: str
    
    # 认知层
    world_model_state: str  # 序列化的世界模型
    predicted_outcomes: Dict[str, float]
    
    # 决策层
    selected_action: str
    action_confidence: float
    alternatives_considered: List[str]
    reasoning: str
    
    # 执行层
    action_data: str
    execution_result: bool
    
    # 结果层
    actual_reward: float
    new_balance: int
    surprise: float  # 预测与实际的差异


class FossilLogger:
    """心智化石记录器
    
    将数字婴儿的每一刻"思维过程"记录下来，
    形成可供后人研究的"心智化石"。
    """
    
    def __init__(self, db_path: str = "logs/mind/mind_fossils.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_tables()
        
        self.logger = logging.getLogger(__name__)
    
    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        # 心智化石主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mind_fossils (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                slot INTEGER,
                perceived_balance INTEGER,
                perceived_pressure REAL,
                perceived_environment TEXT,
                world_model_state TEXT,
                predicted_outcomes TEXT,
                selected_action TEXT,
                action_confidence REAL,
                alternatives_considered TEXT,
                reasoning TEXT,
                action_data TEXT,
                execution_result INTEGER,
                actual_reward REAL,
                new_balance INTEGER,
                surprise REAL
            )
        ''')
        
        # 生存指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survival_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                slot INTEGER,
                balance INTEGER,
                projected_balance INTEGER,
                estimated_slots_remaining INTEGER,
                action_count INTEGER,
                strategy TEXT,
                survival_pressure REAL,
                environment_friendlyness REAL
            )
        ''')
        
        # 行为模式表（聚合统计）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                window_start TEXT,
                window_end TEXT,
                action_type TEXT,
                frequency INTEGER,
                avg_reward REAL,
                success_rate REAL
            )
        ''')
        
        self.conn.commit()
    
    def record_mind_fossil(self, fossil: MindFossil):
        """记录一次完整的心智化石"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO mind_fossils (
                timestamp, slot, perceived_balance, perceived_pressure,
                perceived_environment, world_model_state, predicted_outcomes,
                selected_action, action_confidence, alternatives_considered,
                reasoning, action_data, execution_result, actual_reward,
                new_balance, surprise
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fossil.timestamp,
            fossil.slot,
            fossil.perceived_balance,
            fossil.perceived_pressure,
            fossil.perceived_environment,
            fossil.world_model_state,
            json.dumps(fossil.predicted_outcomes),
            fossil.selected_action,
            fossil.action_confidence,
            json.dumps(fossil.alternatives_considered),
            fossil.reasoning,
            fossil.action_data,
            1 if fossil.execution_result else 0,
            fossil.actual_reward,
            fossil.new_balance,
            fossil.surprise,
        ))
        
        self.conn.commit()
    
    def record_survival_metrics(
        self,
        slot: int,
        balance: int,
        projected_balance: int,
        estimated_slots_remaining: int,
        action_count: int,
        strategy: str,
        survival_pressure: float,
        environment_friendlyness: float,
    ):
        """记录生存指标"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO survival_metrics (
                timestamp, slot, balance, projected_balance,
                estimated_slots_remaining, action_count, strategy,
                survival_pressure, environment_friendlyness
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            slot,
            balance,
            projected_balance,
            estimated_slots_remaining,
            action_count,
            strategy,
            survival_pressure,
            environment_friendlyness,
        ))
        
        self.conn.commit()
    
    def analyze_behavior_patterns(
        self,
        window_minutes: int = 60
    ) -> List[Dict]:
        """分析最近的行为模式"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT 
                selected_action,
                COUNT(*) as frequency,
                AVG(actual_reward) as avg_reward,
                AVG(CASE WHEN execution_result = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(surprise) as avg_surprise
            FROM mind_fossils
            WHERE timestamp > datetime('now', ?)
            GROUP BY selected_action
        ''', (f'-{window_minutes} minutes',))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                'action_type': row[0],
                'frequency': row[1],
                'avg_reward': row[2],
                'success_rate': row[3],
                'avg_surprise': row[4],
            })
        
        return patterns
    
    def get_life_trajectory(self) -> List[Dict]:
        """获取生命轨迹（用于可视化）"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT slot, balance, survival_pressure, selected_action, actual_reward
            FROM survival_metrics
            JOIN mind_fossils ON survival_metrics.slot = mind_fossils.slot
            ORDER BY survival_metrics.slot
        ''')
        
        trajectory = []
        for row in cursor.fetchall():
            trajectory.append({
                'slot': row[0],
                'balance': row[1],
                'survival_pressure': row[2],
                'action': row[3],
                'reward': row[4],
            })
        
        return trajectory
    
    def export_mind_fossils(self, output_path: str):
        """导出所有心智化石为 JSON"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT * FROM mind_fossils ORDER BY slot')
        
        fossils = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            fossil = dict(zip(columns, row))
            # 解析 JSON 字段
            for key in ['predicted_outcomes', 'alternatives_considered']:
                if key in fossil and fossil[key]:
                    try:
                        fossil[key] = json.loads(fossil[key])
                    except:
                        pass
            fossils.append(fossil)
        
        with open(output_path, 'w') as f:
            json.dump(fossils, f, indent=2, default=str)
        
        self.logger.info(f"🪨 已导出 {len(fossils)} 条心智化石: {output_path}")
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
