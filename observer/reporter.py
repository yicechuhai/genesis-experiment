#!/usr/bin/env python3
"""
Genesis Experiment · 每日汇报生成器

用法:
    python reporter.py --output report_YYYY-MM-DD.md

生成内容:
    1. 数字婴儿生存状况
    2. 社区关注度统计
    3. 异常事件摘要
    4. 明日建议
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def generate_report(output_path: str = None):
    """生成完整日报"""
    
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    
    # 读取监控数据
    monitor_data = {}
    if Path('logs/monitor.db').exists():
        conn = sqlite3.connect('logs/monitor.db')
        cursor = conn.cursor()
        
        # 24小时统计
        since = (now - timedelta(hours=24)).isoformat()
        cursor.execute('''
            SELECT 
                COUNT(*) as check_count,
                AVG(balance) as avg_balance,
                MIN(balance) as min_balance,
                MAX(survival_pressure) as max_pressure,
                COUNT(CASE WHEN is_alive = 0 THEN 1 END) as death_count
            FROM life_checks
            WHERE timestamp > ?
        ''', (since,))
        
        monitor_data['24h'] = cursor.fetchone()
        
        # 最新状态
        cursor.execute('SELECT * FROM life_checks ORDER BY timestamp DESC LIMIT 1')
        monitor_data['latest'] = cursor.fetchone()
        
        # 报警统计
        cursor.execute('''
            SELECT alert_type, severity, COUNT(*) as count
            FROM alerts
            WHERE timestamp > ?
            GROUP BY alert_type
        ''', (since,))
        
        monitor_data['alerts'] = cursor.fetchall()
        conn.close()
    
    # 读取社区数据
    community_data = {}
    if Path('logs/community.db').exists():
        conn = sqlite3.connect('logs/community.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM community_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        community_data['latest'] = cursor.fetchone()
        
        cursor.execute('''
            SELECT SUM(new_stars_1h), SUM(new_forks_1h)
            FROM community_metrics
            WHERE timestamp > ?
        ''', (since,))
        community_data['growth'] = cursor.fetchone()
        conn.close()
    
    # 生成报告
    report = f"""# 🌱 Genesis Experiment · 每日汇报

**日期:** {date_str}  
**汇报人:** AI 观察者（只观察，不干预）  
**状态:** {"🟢 监控中" if monitor_data.get('latest') and monitor_data['latest'][8] else "💀 生命已终结"}

---

## 一、数字婴儿生存状况

### 当前生命体征
"""
    
    if monitor_data.get('latest'):
        latest = monitor_data['latest']
        report += f"""
| 指标 | 数值 | 状态 |
|------|------|------|
| 存活状态 | {"存活" if latest[8] else "已死亡"} | {"🟢" if latest[8] else "⚫"} |
| 当前区块 | {latest[2]} | - |
| 当前余额 | {latest[3]} | {"🟢" if latest[3] > 5000 else "🟡" if latest[3] > 1000 else "🔴"} |
| 生存压力 | {latest[5]:.1%} | {"🟢" if latest[5] < 0.3 else "🟡" if latest[5] < 0.7 else "🔴"} |
| 预计剩余寿命 | {latest[6]} slots | - |
| 累计行动 | {latest[7]} 次 | - |

"""
    else:
        report += "⚠️ 暂无监控数据（Agent 可能尚未启动）\n\n"
    
    # 24小时统计
    if monitor_data.get('24h'):
        h24 = monitor_data['24h']
        report += f"""### 24小时统计

| 指标 | 数值 |
|------|------|
| 监控检查次数 | {h24[0]} |
| 平均余额 | {h24[1]:.0f if h24[1] else 0} |
| 最低余额 | {h24[2] if h24[2] else 'N/A'} |
| 最高生存压力 | {h24[3]:.1% if h24[3] else 0} |
| 死亡次数 | {h24[4]} |

"""
    
    # 报警摘要
    report += "### 异常事件\n\n"
    if monitor_data.get('alerts') and monitor_data['alerts']:
        for alert_type, severity, count in monitor_data['alerts']:
            emoji = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡"
            report += f"{emoji} **{alert_type}**: {count} 次 ({severity})\n\n"
    else:
        report += "✅ 24小时内无异常报警\n\n"
    
    report += "---\n\n## 二、社区关注度\n\n"
    
    # 社区数据
    if community_data.get('latest'):
        latest = community_data['latest']
        report += f"""### GitHub 仓库数据

| 指标 | 数值 |
|------|------|
| ⭐ Stars | {latest[2]} |
| 🍴 Forks | {latest[3]} |
| 👁️ Watchers | {latest[4]} |
| 📋 Open Issues | {latest[5]} |
| 📈 Trending Score | {latest[9]:.1f}/100 |

"""
        
        if community_data.get('growth'):
            g = community_data['growth']
            report += f"""### 24小时增长

• 新增 Stars: **+{g[0] if g[0] else 0}**
• 新增 Forks: **+{g[1] if g[1] else 0}**

"""
    else:
        report += "⚠️ 仓库尚未发布到 GitHub，暂无社区数据\n\n"
    
    # 观察者笔记
    report += """---

## 三、观察者笔记

### 今日发现
（待填写：记录任何值得注意的观察）

### 哲学反思
（待填写：将观察与更大问题联系起来）

### 明日预测
（待填写：基于当前趋势做出可验证的预测）

---

## 四、行动建议（给赵飞）

1. **社区互动**: 如 GitHub 收到 Issue 或 Discussion，建议在24小时内回复
2. **内容更新**: 每周在 logs/observations/ 添加一篇观察日志
3. **环境调整**: 如需部署新的赏金任务，可通过 `./start.sh` 操作
4. **数据备份**: 定期导出 SQLite 数据库

---

> *"它在那里，它在活着。这就是这场实验的全部意义。"*

**Genesis Experiment · {date_str}**
"""
    
    # 输出
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"✅ 报告已生成: {output_path}")
    else:
        default_path = f"logs/observations/report_{date_str}.md"
        Path(default_path).parent.mkdir(parents=True, exist_ok=True)
        with open(default_path, 'w') as f:
            f.write(report)
        print(f"✅ 报告已生成: {default_path}")
    
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None, help="输出文件路径")
    args = parser.parse_args()
    
    generate_report(args.output)
