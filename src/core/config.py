# -*- coding: utf-8 -*-
"""核心配置模块"""
import os, json, time
from pathlib import Path

BASE = Path(__file__).parent.parent.parent.resolve()
SECRET_FILE = BASE / ".secrets.json"

# 代理配置
PROXY = "http://127.0.0.1:20808"

# 目录配置
ARTICLES_DIR = BASE / "articles"
HTML_DIR = BASE / "html_articles"
RAW_DIR = BASE / "raw_transcripts"
LOGS_DIR = BASE / "logs"

# GitHub配置
REPO_OWNER = "zenghuafeng008-cmd"
REPO_NAME = "Fenggeblog"
BRANCH = "main"

# MiniMax配置
MINIMAX_ENDPOINT = "https://api.minimax.chat/v1"
MODEL = "abab6.5s-chat"
MAX_TOKENS = 3000

# 分类
CATEGORIES = ["AI资讯", "AI工具", "AI评测", "本地部署", "工具教程"]

# 广告占位符
AD_INLINE = '<div class="ad-inline"><span>广告位招商中 | 联系：zenghuafeng008@gmail.com</span></div>'

def ensure_dirs():
    """确保必要目录存在"""
    for d in [ARTICLES_DIR, HTML_DIR, RAW_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def load_secrets():
    """���载密钥配置"""
    if not SECRET_FILE.exists():
        return {}, None, None
    sec = json.load(open(SECRET_FILE, encoding="utf-8-sig"))
    return sec, sec.get("github_token", ""), sec.get("minimax_key", "")

def get_log_file():
    return LOGS_DIR / f"run_{time.strftime('%Y%m%d')}.log"

class Logger:
    def __init__(self, log_file=None):
        self.log_file = log_file or get_log_file()
    
    def log(self, msg):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts}  {msg}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

ensure_dirs()
