# -*- coding: utf-8 -*-
"""监控与日志模块"""
import os, json, time
from datetime import datetime, timedelta
from pathlib import Path

class Monitor:
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.log_dir / "stats.json"
        self.errors_file = self.log_dir / "errors.json"
        self.load_stats()
    
    def load_stats(self):
        if self.stats_file.exists():
            with open(self.stats_file, encoding="utf-8") as f:
                self.stats = json.load(f)
        else:
            self.stats = {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "articles_generated": 0,
                "errors": [],
                "last_run": None,
                "daily_stats": {}
            }
    
    def save_stats(self):
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def log_run(self, success, articles_count=0, error=None):
        self.stats["total_runs"] += 1
        if success:
            self.stats["successful_runs"] += 1
            self.stats["articles_generated"] += articles_count
        else:
            self.stats["failed_runs"] += 1
            if error:
                self.stats["errors"].append({
                    "time": datetime.now().isoformat(),
                    "error": str(error)
                })
                # 只保留最近20条错误
                self.stats["errors"] = self.stats["errors"][-20:]
        
        self.stats["last_run"] = datetime.now().isoformat()
        self.save_stats()
    
    def get_daily_stats(self, days=7):
        stats = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_stat = self.stats["daily_stats"].get(date, {
                "runs": 0, "articles": 0, "errors": 0
            })
            stats.append({"date": date, **day_stat})
        return stats
    
    def get_summary(self):
        return {
            "total_runs": self.stats["total_runs"],
            "success_rate": round(
                self.stats["successful_runs"] / max(1, self.stats["total_runs"]) * 100, 1
            ),
            "articles_generated": self.stats["articles_generated"],
            "last_run": self.stats["last_run"],
            "recent_errors": self.stats["errors"][-5:]
        }

def send_alert(message, webhook_url=None):
    """发送告警通知"""
    if not webhook_url:
        return False
    
    try:
        import urllib.request
        data = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception as e:
        print(f"Alert failed: {e}")
        return False

def check_health():
    """健康检查"""
    checks = {
        "yt_dlp": False,
        "python": False,
        "network": False
    }
    
    import subprocess
    try:
        result = subprocess.run(["python", "-m", "yt_dlp", "--version"],
                               capture_output=True, timeout=10)
        checks["yt_dlp"] = result.returncode == 0
    except:
        pass
    
    try:
        result = subprocess.run(["python", "--version"],
                               capture_output=True, timeout=10)
        checks["python"] = result.returncode == 0
    except:
        pass
    
    return checks
