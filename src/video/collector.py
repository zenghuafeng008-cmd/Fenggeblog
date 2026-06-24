# -*- coding: utf-8 -*-
"""视频采集增强模块 - 支持更多平台和格式"""
import os, re, subprocess, hashlib, time, glob, json
from pathlib import Path

def get_latest_videos(handle, limit=5, proxy=None):
    """获取频道最新视频列表"""
    proxy = proxy or "http://127.0.0.1:20808"
    cmd = ["python", "-m", "yt_dlp", "--proxy", proxy, "--flat-playlist", "--print", "title,url,upload_date", handle]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        videos = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if re.match(r"^https?://", line):
                videos.append({"url": line})
            elif re.match(r"^\d{8}$", line):
                if videos:
                    videos[-1]["date"] = line
            elif len(line) > 3 and not line.startswith("["):
                if videos and "title" not in videos[-1]:
                    videos[-1]["title"] = line
                elif not videos:
                    videos = [{"title": line, "url": ""}]
        return videos[:limit]
    except Exception as e:
        return []

def get_video_info(url, proxy=None):
    """获取视频详细信息"""
    proxy = proxy or "http://127.0.0.1:20808"
    cmd = [
        "python", "-m", "yt_dlp", "--proxy", proxy,
        "--dump-json", "--no-playlist", url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.stdout:
            return json.loads(result.stdout)
    except Exception as e:
        pass
    return None

def get_subtitle(url, proxy=None, languages=None):
    """提取视频字幕 - 增强版"""
    proxy = proxy or "http://127.0.0.1:20808"
    languages = languages or ["zh-Hans", "zh-Hant", "en", "zh-CN", "zh-TW"]
    lang_str = ",".join(languages)
    
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "yt_" + hashlib.md5(str(time.time()).encode()).hexdigest()[:8])
    cmd = [
        "python", "-m", "yt_dlp", "--proxy", proxy,
        "--skip-download", "--write-auto-sub",
        "--sub-lang", lang_str, "-o", tmp, url
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        vtt_files = glob.glob(os.path.join(os.environ.get("TEMP", "/tmp"), "*.vtt"))
        recent = [f for f in vtt_files if os.path.getmtime(f) > time.time() - 300]
        
        for vtt_file in sorted(recent, key=os.path.getmtime, reverse=True):
            with open(vtt_file, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\r?\n", "\n", text).strip()
            os.remove(vtt_file)
            if len(text) > 50:  # 确保有实质内容
                return text
    except Exception as e:
        pass
    return None

def download_video(url, output_dir, proxy=None, quality="best"):
    """下载视频"""
    proxy = proxy or "http://127.0.0.1:20808"
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "python", "-m", "yt_dlp", "--proxy", proxy,
        "-f", f"best[height<={quality}]" if quality.isdigit() else "best",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        return False

# 平台检测
def detect_platform(url):
    """检测视频平台"""
    platforms = {
        "youtube": r"youtube\.com|youtu\.be",
        "bilibili": r"bilibili\.com|b23\.tv",
        "douyin": r"douyin\.com",
        "xiaohongshu": r"xiaohongshu\.com",
        "twitter": r"twitter\.com|x\.com",
        "微博": r"weibo\.com",
    }
    for name, pattern in platforms.items():
        if re.search(pattern, url, re.I):
            return name
    return "unknown"
