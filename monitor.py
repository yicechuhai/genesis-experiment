#!/usr/bin/env python3
"""
Genesis Experiment - 数字生命监控脚本
用于后台跟踪数字婴儿的生存状况，不干预，只记录。
"""

import json
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/genesis-experiment/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('genesis_monitor')

class GenesisMonitor:
    """数字生命监控器 - 只观察，不干预"""
    
    def __init__(self):
        self.project_dir = Path('/root/.openclaw/workspace/genesis-experiment')
        self.db_path = self.project_dir / 'logs/mind/mind_fossils.db'
        self.status_file = self.project_dir / 'logs/life_status.json'
        self.alert_log = self.project_dir / 'logs/alerts.log'
        
        # 监控阈值
        self.thresholds = {
            'critical_balance': 100,      # 余额低于100，危急
            'warning_balance': 1000,      # 余额低于1000，警告
            'idle_slots': 50,             # 超过50个slot无行动，异常
            'death_detected': False,        # 死亡检测
        }
    
    def check_life_status(self) -> dict:
        """检查数字生命当前状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'alive': False,
            'balance': 0,
            'estimated_slots_remaining': 0,
            'action_count': 0,
            'survival_pressure': 0,
            'last_action_slot': 0,
            'current_slot': 0,
            'status': 'unknown',
        }
        
        try:
            if not self.db_path.exists():
                logger.warning("数据库不存在，Agent可能尚未启动")
                return status
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 获取最新状态
            cursor.execute('''
                SELECT balance, estimated_slots_remaining, action_count, 
                       survival_pressure, slot, environment_friendlyness
                FROM survival_metrics 
                ORDER BY slot DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            
            if row:
                status.update({
                    'alive': row[1] > 0,  # 预计剩余slot > 0
                    'balance': row[0],
                    'estimated_slots_remaining': row[1],
                    'action_count': row[2],
                    'survival_pressure': row[3],
                    'current_slot': row[4],
                    'environment_friendlyness': row[5],
                })
            
            # 获取最后一次行动
            cursor.execute('''
                SELECT MAX(slot) FROM mind_fossils
            ''')
            last_action = cursor.fetchone()[0]
            if last_action:
                status['last_action_slot'] = last_action
            
            conn.close()
            
            # 判定状态
            if not status['alive']:
                status['status'] = 'dead'
            elif status['estimated_slots_remaining'] < self.thresholds['critical_balance']:
                status['status'] = 'critical'
            elif status['estimated_slots_remaining'] < self.thresholds['warning_balance']:
                status['status'] = 'warning'
            else:
                status['status'] = 'healthy'
            
        except Exception as e:
            logger.error(f"状态检查失败: {e}")
        
        return status
    
    def detect_anomalies(self, status: dict) -> list:
        """检测异常状况"""
        anomalies = []
        
        if status['status'] == 'dead' and not self.thresholds['death_detected']:
            anomalies.append({
                'level': 'CRITICAL',
                'type': 'death',
                'message': f'💀 数字婴儿已死亡！最终余额: {status["balance"]}，存活slot: {status["current_slot"]}',
                'timestamp': datetime.now().isoformat(),
            })
            self.thresholds['death_detected'] = True
        
        elif status['status'] == 'critical':
            anomalies.append({
                'level': 'CRITICAL',
                'type': 'low_balance',
                'message': f'🔴 余额危急！预计仅剩 {status["estimated_slots_remaining"]} slots',
                'timestamp': datetime.now().isoformat(),
            })
        
        elif status['status'] == 'warning':
            anomalies.append({
                'level': 'WARNING',
                'type': 'low_balance',
                'message': f'🟠 余额警告！预计仅剩 {status["estimated_slots_remaining"]} slots',
                'timestamp': datetime.now().isoformat(),
            })
        
        # 检测长时间无行动
        if status['current_slot'] - status['last_action_slot'] > self.thresholds['idle_slots']:
            anomalies.append({
                'level': 'WARNING',
                'type': 'idle',
                'message': f'⚠️ 超过 {status["current_slot"] - status["last_action_slot"]} slots 无行动',
                'timestamp': datetime.now().isoformat(),
            })
        
        return anomalies
    
    def generate_report(self) -> dict:
        """生成监控报告"""
        status = self.check_life_status()
        anomalies = self.detect_anomalies(status)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'life_status': status,
            'anomalies': anomalies,
            'summary': self._generate_summary(status, anomalies),
        }
        
        # 保存状态
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        # 如果有异常，记录到告警日志
        if anomalies:
            with open(self.alert_log, 'a') as f:
                for a in anomalies:
                    f.write(f"{a['timestamp']} [{a['level']}] {a['message']}\n")
        
        return report
    
    def _generate_summary(self, status: dict, anomalies: list) -> str:
        """生成自然语言摘要"""
        if status['status'] == 'dead':
            return f"数字婴儿已死亡。共存活 {status['current_slot']} slots，执行 {status['action_count']} 次行动。"
        
        summary = f"数字婴儿存活中。"
        if anomalies:
            summary += f" 检测到 {len(anomalies)} 项异常: " + ", ".join([a['message'] for a in anomalies])
        else:
            summary += f" 状态稳定。余额 {status['balance']}，预计还可存活 {status['estimated_slots_remaining']} slots。"
        
        return summary
    
    def run(self, interval: int = 60):
        """持续监控循环"""
        logger.info("🎛️ 数字生命监控器启动 - 只观察，不干预")
        
        while True:
            report = self.generate_report()
            
            # 打印摘要
            logger.info(report['summary'])
            
            # 如果有异常，立即反馈
            if report['anomalies']:
                for anomaly in report['anomalies']:
                    if anomaly['level'] == 'CRITICAL':
                        logger.critical(anomaly['message'])
                    else:
                        logger.warning(anomaly['message'])
            
            time.sleep(interval)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Genesis Experiment Monitor')
    parser.add_argument('--interval', type=int, default=60, help='监控间隔（秒）')
    parser.add_argument('--once', action='store_true', help='只运行一次并输出报告')
    args = parser.parse_args()
    
    monitor = GenesisMonitor()
    
    if args.once:
        report = monitor.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        monitor.run(interval=args.interval)


if __name__ == '__main__':
    main()
