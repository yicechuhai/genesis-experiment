import json
import logging
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GenesisMonitor:
    """
    数字婴儿监控器
    
    职责：
    1. 持续跟踪数字婴儿的生存状态
    2. 检测异常并报警
    3. 生成定期报告
    4. 绝不干预——纯观察
    """
    
    def __init__(
        self,
        rpc_url: str = "http://localhost:8899",
        life_pda: Optional[str] = None,
        check_interval: int = 60,  # 检查间隔（秒）
    ):
        self.rpc_url = rpc_url
        self.life_pda = life_pda
        self.check_interval = check_interval
        
        # 历史数据
        self.balance_history: List[Dict] = []
        self.max_history = 10000
        
        # 状态标记
        self.is_alive = True
        self.last_alert_time = None
        self.alert_cooldown = 300  # 报警冷却（秒）
        
        # 数据库
        self._init_db()
        
        logger.info(f"🔍 监控器启动 | RPC: {rpc_url} | 检查间隔: {check_interval}s")
    
    def _init_db(self):
        """初始化监控数据库"""
        db_path = Path('logs/monitor.db')
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS life_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                slot INTEGER,
                balance INTEGER,
                projected_balance INTEGER,
                survival_pressure REAL,
                estimated_slots_remaining INTEGER,
                action_count INTEGER,
                is_alive INTEGER,
                note TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                acknowledged INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
    
    def check_life_status(self) -> Optional[Dict]:
        """检查数字婴儿当前状态"""
        try:
            # 这里简化处理，实际应从链上读取
            # 模拟从 Agent 日志数据库读取
            
            agent_db = Path('logs/mind/mind_fossils.db')
            if not agent_db.exists():
                logger.warning("⚠️ 未检测到 Agent 数据库，等待 Agent 启动...")
                return None
            
            agent_conn = sqlite3.connect(str(agent_db))
            cursor = agent_conn.cursor()
            
            # 获取最新状态
            cursor.execute('''
                SELECT slot, balance, estimated_slots_remaining, 
                       action_count, survival_pressure
                FROM survival_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            agent_conn.close()
            
            if not row:
                return None
            
            slot, balance, est_slots, actions, pressure = row
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'slot': slot,
                'balance': balance,
                'estimated_slots_remaining': est_slots,
                'action_count': actions,
                'survival_pressure': pressure,
                'is_alive': balance > 0 and est_slots > 0,
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ 检查状态失败: {e}")
            return None
    
    def detect_anomalies(self, current: Dict, previous: Optional[Dict]) -> List[Dict]:
        """检测异常状态"""
        alerts = []
        
        if not current['is_alive']:
            alerts.append({
                'type': 'DEATH',
                'severity': 'CRITICAL',
                'message': f'💀 数字婴儿已死亡！最终区块: {current["slot"]}，总行动: {current["action_count"]}'
            })
            self.is_alive = False
            return alerts
        
        # 濒死警告
        if current['survival_pressure'] > 0.9:
            alerts.append({
                'type': 'NEAR_DEATH',
                'severity': 'HIGH',
                'message': f'🔴 危急！生存压力 {current["survival_pressure"]:.1%}，预计剩余 {current["estimated_slots_remaining"]} slots'
            })
        elif current['survival_pressure'] > 0.7:
            alerts.append({
                'type': 'WARNING',
                'severity': 'MEDIUM',
                'message': f'🟠 警告！生存压力 {current["survival_pressure"]:.1%}，余额: {current["balance"]}'
            })
        
        # 行为停滞检测
        if previous and current['action_count'] == previous['action_count']:
            alerts.append({
                'type': 'STALL',
                'severity': 'MEDIUM',
                'message': f'⚠️ 行动停滞！已 {self.check_interval} 秒无新行动'
            })
        
        # 余额骤降检测
        if previous:
            balance_drop = previous['balance'] - current['balance']
            if balance_drop > previous['balance'] * 0.5:  # 骤降50%
                alerts.append({
                    'type': 'RAPID_DECLINE',
                    'severity': 'HIGH',
                    'message': f'📉 余额骤降！从 {previous["balance"]} 降至 {current["balance"]} (-{balance_drop})'
                })
        
        return alerts
    
    def record_check(self, status: Dict):
        """记录检查结果"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO life_checks 
            (timestamp, slot, balance, projected_balance, survival_pressure,
             estimated_slots_remaining, action_count, is_alive, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            status['timestamp'],
            status['slot'],
            status['balance'],
            status['balance'],  # 简化
            status['survival_pressure'],
            status['estimated_slots_remaining'],
            status['action_count'],
            1 if status['is_alive'] else 0,
            ''
        ))
        self.conn.commit()
    
    def record_alerts(self, alerts: List[Dict]):
        """记录报警"""
        cursor = self.conn.cursor()
        for alert in alerts:
            cursor.execute('''
                INSERT INTO alerts (timestamp, alert_type, severity, message)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                alert['type'],
                alert['severity'],
                alert['message']
            ))
        self.conn.commit()
    
    def generate_report(self, hours: int = 24) -> str:
        """生成周期性报告"""
        cursor = self.conn.cursor()
        
        # 获取时间段内的统计
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as check_count,
                AVG(balance) as avg_balance,
                MIN(balance) as min_balance,
                MAX(survival_pressure) as max_pressure,
                COUNT(DISTINCT slot) as active_slots
            FROM life_checks
            WHERE timestamp > ?
        ''', (since,))
        
        stats = cursor.fetchone()
        
        # 获取报警统计
        cursor.execute('''
            SELECT alert_type, severity, COUNT(*) as count
            FROM alerts
            WHERE timestamp > ?
            GROUP BY alert_type, severity
        ''', (since,))
        
        alerts_summary = cursor.fetchall()
        
        # 获取最新状态
        cursor.execute('''
            SELECT * FROM life_checks
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        
        latest = cursor.fetchone()
        
        # 生成报告文本
        report = f"""
╔════════════════════════════════════════════════════════════╗
║     🌱 Genesis Experiment · 数字婴儿生存报告              ║
║     生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
╚════════════════════════════════════════════════════════════╝

【生命体征快照】
{"💀 状态: 已死亡" if latest and not latest[8] else "🟢 状态: 存活"}
{"" if not latest else f"区块: {latest[2]} | 余额: {latest[3]} | 行动: {latest[7]}"}
{"" if not latest else f"生存压力: {latest[5]:.1%} | 预计剩余: {latest[6]} slots"}

【{hours}小时统计】
• 检查次数: {stats[0] if stats else 0}
• 平均余额: {stats[1]:.0f if stats and stats[1] else 0}
• 最低余额: {stats[2] if stats else 'N/A'}
• 最高压力: {stats[3]:.1% if stats and stats[3] else 0}

【报警记录】
"""
        
        if alerts_summary:
            for alert_type, severity, count in alerts_summary:
                emoji = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡"
                report += f"{emoji} {alert_type}: {count}次 ({severity})\n"
        else:
            report += "✅ 无异常报警\n"
        
        report += """
【观察者备注】
• 监控模式: 只观察，不干预
• 检查间隔: 每60秒
• 数据来源: Agent 日志 + 链上事件

════════════════════════════════════════════════════════════
"""
        
        return report
    
    def run(self):
        """监控主循环"""
        logger.info("🔍 监控循环启动...")
        
        previous_status = None
        
        try:
            while True:
                current = self.check_life_status()
                
                if current:
                    self.record_check(current)
                    self.balance_history.append(current)
                    
                    if len(self.balance_history) > self.max_history:
                        self.balance_history = self.balance_history[-self.max_history//2:]
                    
                    # 检测异常
                    alerts = self.detect_anomalies(current, previous_status)
                    if alerts:
                        self.record_alerts(alerts)
                        for alert in alerts:
                            logger.warning(alert['message'])
                    
                    # 常规日志
                    logger.info(
                        f"💗 生命体征 | Slot: {current['slot']} | "
                        f"余额: {current['balance']} | "
                        f"压力: {current['survival_pressure']:.1%} | "
                        f"行动: {current['action_count']}"
                    )
                    
                    previous_status = current
                    
                    # 如果已死亡，停止监控（或继续记录化石）
                    if not current['is_alive']:
                        logger.info("💀 生命已终结。监控器进入化石记录模式。")
                        # 可以选择继续运行以记录环境变化
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 监控器收到停止信号")
        finally:
            self.conn.close()
            logger.info("🔚 监控器已关闭")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--life-pda", default=None)
    args = parser.parse_args()
    
    monitor = GenesisMonitor(
        check_interval=args.interval,
        life_pda=args.life_pda,
    )
    monitor.run()
