import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/community.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CommunityTracker:
    """
    社区关注度跟踪器
    
    职责：
    1. 跟踪 GitHub 仓库的 Stars / Forks / Watchers
    2. 监控 Issues 和 Discussions 活跃度
    3. 定期生成社区健康度报告
    4. 检测异常关注波动（如被大型社区推荐）
    """
    
    def __init__(
        self,
        repo_owner: str = "zhaofei",
        repo_name: str = "genesis-experiment",
        github_token: Optional[str] = None,
        check_interval: int = 3600,  # 每小时检查一次
    ):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.check_interval = check_interval
        self.api_base = "https://api.github.com"
        
        self._init_db()
        
        logger.info(f"📊 社区跟踪器启动 | 仓库: {repo_owner}/{repo_name}")
    
    def _init_db(self):
        """初始化数据库"""
        db_path = Path('logs/community.db')
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                stars INTEGER,
                forks INTEGER,
                watchers INTEGER,
                open_issues INTEGER,
                open_discussions INTEGER,
                new_stars_1h INTEGER,
                new_forks_1h INTEGER,
                trending_score REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id INTEGER,
                timestamp TEXT,
                title TEXT,
                author TEXT,
                state TEXT,
                comments_count INTEGER,
                labels TEXT,
                url TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discussions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_id INTEGER,
                timestamp TEXT,
                title TEXT,
                author TEXT,
                state TEXT,
                comments_count INTEGER,
                category TEXT,
                url TEXT
            )
        ''')
        
        self.conn.commit()
    
    def _github_api(self, endpoint: str) -> Optional[Dict]:
        """调用 GitHub API"""
        url = f"{self.api_base}/{endpoint}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Genesis-Experiment-Tracker"
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                logger.warning(f"⚠️ 仓库不存在或尚未公开: {endpoint}")
                return None
            else:
                logger.error(f"❌ API 错误 {resp.status_code}: {endpoint}")
                return None
        except Exception as e:
            logger.error(f"❌ API 调用失败: {e}")
            return None
    
    def fetch_repo_stats(self) -> Optional[Dict]:
        """获取仓库基础统计"""
        data = self._github_api(f"repos/{self.repo_owner}/{self.repo_name}")
        if not data:
            return None
        
        return {
            'stars': data.get('stargazers_count', 0),
            'forks': data.get('forks_count', 0),
            'watchers': data.get('watchers_count', 0),
            'open_issues': data.get('open_issues_count', 0),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
        }
    
    def fetch_issues(self, state: str = "open", per_page: int = 10) -> List[Dict]:
        """获取 Issues"""
        data = self._github_api(
            f"repos/{self.repo_owner}/{self.repo_name}/issues?state={state}&per_page={per_page}"
        )
        if not data:
            return []
        
        issues = []
        for item in data:
            if 'pull_request' in item:  # 排除 PR
                continue
            issues.append({
                'id': item['id'],
                'title': item['title'],
                'author': item['user']['login'],
                'state': item['state'],
                'comments': item['comments'],
                'labels': [l['name'] for l in item['labels']],
                'url': item['html_url'],
                'created_at': item['created_at'],
            })
        return issues
    
    def calculate_trending_score(
        self,
        current: Dict,
        previous: Optional[Dict]
    ) -> float:
        """计算趋势得分（0-100）"""
        if not previous:
            return 0.0
        
        # 综合指标：star增长、issue活跃度、fork增长
        star_growth = current['stars'] - previous['stars']
        fork_growth = current['forks'] - previous['forks']
        issue_activity = current['open_issues'] - previous['open_issues']
        
        # 归一化得分
        score = (
            min(star_growth * 10, 50) +      # 每新增1 star = 10分，上限50
            min(fork_growth * 20, 30) +      # 每新增1 fork = 20分，上限30
            min(issue_activity * 5, 20)      # 每新增1 issue = 5分，上限20
        )
        
        return min(score, 100.0)
    
    def record_metrics(self, stats: Dict, trending_score: float):
        """记录指标"""
        cursor = self.conn.cursor()
        
        # 计算增量
        cursor.execute('''
            SELECT stars, forks FROM community_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        prev = cursor.fetchone()
        
        new_stars = stats['stars'] - (prev[0] if prev else stats['stars'])
        new_forks = stats['forks'] - (prev[1] if prev else stats['forks'])
        
        cursor.execute('''
            INSERT INTO community_metrics
            (timestamp, stars, forks, watchers, open_issues, open_discussions,
             new_stars_1h, new_forks_1h, trending_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            stats['stars'],
            stats['forks'],
            stats['watchers'],
            stats['open_issues'],
            0,  # 简化
            new_stars,
            new_forks,
            trending_score,
        ))
        self.conn.commit()
    
    def generate_community_report(self, hours: int = 24) -> str:
        """生成社区报告"""
        cursor = self.conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # 最新数据
        cursor.execute('''
            SELECT * FROM community_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        latest = cursor.fetchone()
        
        # 时间段内的增长
        cursor.execute('''
            SELECT 
                SUM(new_stars_1h) as total_new_stars,
                SUM(new_forks_1h) as total_new_forks,
                AVG(trending_score) as avg_trending
            FROM community_metrics
            WHERE timestamp > ?
        ''', (since,))
        
        growth = cursor.fetchone()
        
        # 获取活跃 issues
        issues = self.fetch_issues(state="open", per_page=5)
        
        report = f"""
╔════════════════════════════════════════════════════════════╗
║     📊 Genesis Experiment · 社区关注度报告                ║
║     生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
║     仓库: {self.repo_owner}/{self.repo_name}                              ║
╚════════════════════════════════════════════════════════════╝

【当前数据】
{"" if not latest else f"⭐ Stars: {latest[2]} | 🍴 Forks: {latest[3]} | 👁️ Watchers: {latest[4]}"}
{"" if not latest else f"📋 Open Issues: {latest[5]} | 📈 Trending Score: {latest[9]:.1f}"}

【{hours}小时增长】
• 新增 Stars: +{growth[0] if growth else 0}
• 新增 Forks: +{growth[1] if growth else 0}
• 平均热度: {growth[2]:.1f if growth and growth[2] else 0}/100

【最新 Issues】
"""
        
        if issues:
            for issue in issues[:5]:
                report += f"• #{issue['id']} {issue['title']} by {issue['author']} ({issue['comments']} comments)\n"
        else:
            report += "暂无活跃 Issues\n"
        
        # 社区健康度评估
        health = "🟢 健康" if (growth[0] if growth else 0) > 0 else "🟡 稳定" if latest and latest[2] > 0 else "⚪ 冷启动"
        report += f"""
【社区健康度】
{health}

════════════════════════════════════════════════════════════
"""
        
        return report
    
    def run(self):
        """社区跟踪主循环"""
        logger.info("📊 社区跟踪循环启动...")
        
        previous_stats = None
        
        try:
            while True:
                stats = self.fetch_repo_stats()
                
                if stats:
                    trending = self.calculate_trending_score(stats, previous_stats)
                    self.record_metrics(stats, trending)
                    
                    logger.info(
                        f"📈 社区数据 | ⭐ {stats['stars']} | "
                        f"🍴 {stats['forks']} | 👁️ {stats['watchers']} | "
                        f"📈 {trending:.1f}"
                    )
                    
                    # 高热度报警
                    if trending > 50:
                        logger.warning(f"🔥 热度飙升！Trending Score: {trending:.1f}")
                    
                    previous_stats = stats
                else:
                    logger.info("⏳ 仓库尚未公开或无法访问，等待中...")
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 社区跟踪器收到停止信号")
        finally:
            self.conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="zhaofei")
    parser.add_argument("--repo", default="genesis-experiment")
    parser.add_argument("--token", default=None)
    parser.add_argument("--interval", type=int, default=3600)
    args = parser.parse_args()
    
    tracker = CommunityTracker(
        repo_owner=args.owner,
        repo_name=args.repo,
        github_token=args.token,
        check_interval=args.interval,
    )
    tracker.run()
