import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class WorldState:
    """世界状态表示"""
    balance: float = 0.0
    balance_velocity: float = 0.0  # 余额变化速度
    slot: int = 0
    action_count: int = 0
    estimated_lifespan: float = 0.0
    survival_pressure: float = 0.0  # 0-1
    last_reward_slot: Optional[int] = None
    reward_frequency: float = 0.0  # 每 slot 获得奖励的概率
    
    # 环境特征
    bounty_count: int = 0
    known_bounties: List[str] = field(default_factory=list)
    successful_actions: Dict[str, int] = field(default_factory=dict)
    failed_actions: Dict[str, int] = field(default_factory=dict)


class WorldModel:
    """数字婴儿的世界模型
    
    简化的神经网络世界模型，用于：
    1. 预测执行某动作后的状态变化
    2. 评估当前环境的"友好度"
    3. 学习动作-结果的映射
    """
    
    def __init__(self, state_dim: int = 10, action_dim: int = 5):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # 简化的权重矩阵（随机初始化）
        self.transition_matrix = np.random.randn(action_dim, state_dim, state_dim) * 0.1
        self.reward_weights = np.random.randn(state_dim) * 0.1
        
        # 经验回放缓冲区
        self.experiences: List[Tuple[WorldState, str, float, WorldState]] = []
        self.max_experiences = 1000
        
        # 动作价值估计
        self.action_values: Dict[str, float] = {
            'breathe': 0.5,
            'random_move': 0.5,
            'explore': 0.5,
            'claim_bounty': 0.5,
            'rest': 0.5,
        }
        
        # 学习率
        self.alpha = 0.1
        self.gamma = 0.9  # 折扣因子
    
    def encode_state(self, state: WorldState) -> np.ndarray:
        """将 WorldState 编码为向量"""
        return np.array([
            state.balance / 10000.0,  # 归一化
            state.balance_velocity / 100.0,
            state.survival_pressure,
            state.reward_frequency,
            state.bounty_count / 10.0,
            sum(state.successful_actions.values()) / max(1, state.action_count),
            sum(state.failed_actions.values()) / max(1, state.action_count),
            random.random(),  # 熵项
            1.0 if state.estimated_lifespan > 1000 else 0.0,
            1.0 if state.estimated_lifespan < 100 else 0.0,
        ])
    
    def predict(self, state: WorldState, action: str) -> Tuple[WorldState, float]:
        """预测执行动作后的状态和预期奖励"""
        action_idx = list(self.action_values.keys()).index(action) if action in self.action_values else 0
        
        state_vec = self.encode_state(state)
        
        # 简化的状态转移预测
        next_state_vec = state_vec + np.dot(self.transition_matrix[action_idx], state_vec)
        
        # 预测奖励
        predicted_reward = np.dot(self.reward_weights, next_state_vec)
        
        # 构造预测状态
        next_state = WorldState(
            balance=state.balance + predicted_reward * 100,
            balance_velocity=predicted_reward,
            slot=state.slot + 1,
            action_count=state.action_count + 1,
            survival_pressure=max(0, min(1, 1 - next_state_vec[8])),
        )
        
        return next_state, predicted_reward
    
    def update(self, state: WorldState, action: str, reward: float, next_state: WorldState):
        """根据实际结果更新模型"""
        # 存储经验
        self.experiences.append((state, action, reward, next_state))
        if len(self.experiences) > self.max_experiences:
            self.experiences.pop(0)
        
        # 更新动作价值（Q-learning 简化版）
        action_idx = list(self.action_values.keys()).index(action)
        state_vec = self.encode_state(state)
        next_state_vec = self.encode_state(next_state)
        
        # 计算 TD 误差
        current_value = np.dot(self.reward_weights, state_vec)
        next_value = np.dot(self.reward_weights, next_state_vec)
        td_error = reward + self.gamma * next_value - current_value
        
        # 更新权重
        self.reward_weights += self.alpha * td_error * state_vec
        
        # 更新转移矩阵
        self.transition_matrix[action_idx] += self.alpha * td_error * np.outer(state_vec, state_vec)
        
        # 更新动作价值表
        self.action_values[action] += self.alpha * td_error
        
        # 裁剪
        self.reward_weights = np.clip(self.reward_weights, -1, 1)
        self.transition_matrix = np.clip(self.transition_matrix, -1, 1)
    
    def get_best_action(self, state: WorldState) -> str:
        """根据当前世界模型选择最佳动作"""
        predictions = {}
        for action in self.action_values.keys():
            _, predicted_reward = self.predict(state, action)
            predictions[action] = predicted_reward
        
        # 添加探索噪声
        for action in predictions:
            predictions[action] += random.gauss(0, 0.1)
        
        return max(predictions, key=predictions.get)
    
    def get_environment_friendlyness(self, state: WorldState) -> float:
        """评估环境友好度 (0-1)"""
        state_vec = self.encode_state(state)
        raw_score = np.dot(self.reward_weights, state_vec)
        return max(0, min(1, (raw_score + 1) / 2))
    
    def serialize(self) -> str:
        """序列化模型状态"""
        model_data = {
            'transition_matrix': self.transition_matrix.tolist(),
            'reward_weights': self.reward_weights.tolist(),
            'action_values': self.action_values,
            'experience_count': len(self.experiences),
        }
        return json.dumps(model_data)
    
    def deserialize(self, data: str):
        """反序列化模型状态"""
        model_data = json.loads(data)
        self.transition_matrix = np.array(model_data['transition_matrix'])
        self.reward_weights = np.array(model_data['reward_weights'])
        self.action_values = model_data['action_values']
