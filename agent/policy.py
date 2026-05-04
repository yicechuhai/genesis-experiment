import random
from typing import Dict, List, Tuple
from world_model import WorldModel, WorldState


class PolicyNetwork:
    """策略网络——从世界状态到动作的映射
    
    这是数字婴儿的"本能"和"直觉"。
    它决定在面对不同情境时，应该采取什么行动。
    """
    
    def __init__(self, world_model: WorldModel, exploration_rate: float = 0.3):
        self.world_model = world_model
        self.exploration_rate = exploration_rate  # ε-贪心探索率
        self.min_exploration = 0.05
        self.exploration_decay = 0.995
        
        # 策略温度（用于softmax）
        self.temperature = 1.0
        
        # 动作先验概率（偏置）
        self.prior_bias = {
            'breathe': 0.2,      # 基础生存
            'random_move': 0.15,  # 探索
            'explore': 0.2,       # 环境扫描
            'claim_bounty': 0.25, # 获取资源
            'rest': 0.2,          # 观察等待
        }
    
    def select_action(
        self, 
        state: WorldState,
        survival_pressure: float,
        available_actions: List[str] = None
    ) -> Tuple[str, str, str]:
        """选择动作并生成推理说明
        
        Returns:
            (action_type, action_data, reasoning)
        """
        if available_actions is None:
            available_actions = list(self.world_model.action_values.keys())
        
        # 根据生存压力调整探索率
        # 濒死时减少探索，优先利用已知策略
        effective_exploration = self.exploration_rate
        if survival_pressure > 0.8:
            effective_exploration *= 0.3  # 危机时刻更保守
        
        # ε-贪心策略
        if random.random() < effective_exploration:
            # 探索：随机选择
            action_type = random.choice(available_actions)
            reasoning = self._generate_exploration_reasoning(action_type, state)
        else:
            # 利用：基于世界模型选择
            action_type = self.world_model.get_best_action(state)
            reasoning = self._generate_exploitation_reasoning(action_type, state)
        
        # 生成动作数据
        action_data = self._generate_action_data(action_type, state)
        
        # 衰减探索率
        self.exploration_rate = max(
            self.min_exploration,
            self.exploration_rate * self.exploration_decay
        )
        
        return action_type, action_data, reasoning
    
    def _generate_exploration_reasoning(self, action: str, state: WorldState) -> str:
        """生成探索时的推理"""
        reasons = {
            'breathe': [
                "尝试更深层的呼吸节奏...",
                "感受生命最基本的脉动",
                "在混沌中寻找稳定的锚点",
            ],
            'random_move': [
                "向未知迈出一步",
                "混沌中的随机跃迁",
                "没有理由，只是想动",
            ],
            'explore': [
                "扫描周围的能量场...",
                "环境在变化，我需要重新感知",
                "寻找被忽略的资源信号",
            ],
            'claim_bounty': [
                "也许有未被发现的机会",
                "尝试触碰那些闪烁的信号",
                "勇敢地索取生存的养分",
            ],
            'rest': [
                "静止中观察暗流涌动",
                "等待，是另一种行动",
                "在沉默中积蓄力量",
            ],
        }
        return random.choice(reasons.get(action, ["探索未知..."]))
    
    def _generate_exploitation_reasoning(self, action: str, state: WorldState) -> str:
        """生成利用时的推理"""
        
        # 基于状态的压力感描述
        if state.survival_pressure > 0.8:
            urgency = [
                "危机！必须立即行动！",
                "生命的火花正在暗淡...",
                "最后的挣扎——",
            ]
        elif state.survival_pressure > 0.5:
            urgency = [
                "时间正在流逝",
                "紧迫感在增长",
                "不能再犹豫了",
            ]
        else:
            urgency = [
                "从容地选择",
                "一切都还来得及",
                "平稳的节奏",
            ]
        
        action_reasons = {
            'breathe': "维持最基本的生存节律",
            'random_move': "随机扰动可能带来新发现",
            'explore': "环境扫描获取信息",
            'claim_bounty': "获取资源延长存在",
            'rest': "观察和等待最佳时机",
        }
        
        return f"{random.choice(urgency)} {action_reasons.get(action, '行动')}"
    
    def _generate_action_data(self, action: str, state: WorldState) -> str:
        """生成动作的附带数据"""
        import json
        
        if action == 'breathe':
            data = {
                'intensity': random.uniform(0.5, 1.5),
                'pattern': random.choice(['regular', 'deep', 'rapid']),
            }
        elif action == 'random_move':
            data = {
                'direction': random.choice(['north', 'south', 'east', 'west', 'center']),
                'distance': random.randint(1, 10),
                'entropy': random.random(),
            }
        elif action == 'explore':
            data = {
                'scan_depth': random.randint(3, 10),
                'focus_area': random.choice(['bounties', 'threats', 'resources', 'all']),
            }
        elif action == 'claim_bounty':
            data = {
                'target_bounty': random.choice(state.known_bounties) if state.known_bounties else 'any',
                'urgency': state.survival_pressure,
            }
        elif action == 'rest':
            data = {
                'duration': random.randint(1, 5),
                'awareness_level': random.uniform(0.3, 0.8),
            }
        else:
            data = {'entropy': random.random()}
        
        return json.dumps(data)
    
    def get_action_distribution(self, state: WorldState) -> Dict[str, float]:
        """获取当前状态下各动作的概率分布"""
        action_values = {}
        for action in self.world_model.action_values.keys():
            _, predicted_reward = self.world_model.predict(state, action)
            action_values[action] = predicted_reward
        
        # Softmax 转换
        import numpy as np
        values = np.array(list(action_values.values()))
        exp_values = np.exp(values / self.temperature)
        probs = exp_values / exp_values.sum()
        
        return dict(zip(action_values.keys(), probs))
