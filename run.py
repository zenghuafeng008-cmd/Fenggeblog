import os, json, base64, hashlib, urllib.request, urllib.parse, re, time, glob, subprocess

PROXY = "http://127.0.0.1:20808"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))

CHANNELS = [
    {"name": "yunfeifei", "handle": "https://www.youtube.com/@yunfeifei-k5h"},
    {"name": "lingdujieshuo", "handle": "https://www.youtube.com/@lingdujieshuo"},
]
BASE = r"H:/workspace/01_项目/P09_YoutubeAutoBlog"
os.makedirs(BASE + "/articles", exist_ok=True)
os.makedirs(BASE + "/logs", exist_ok=True)

SECRET_FILE = BASE + "/.secrets.json"
GH_TOKEN = MINIMAX_KEY = MINIMAX_GROUP = ""
if os.path.exists(SECRET_FILE):
    sec = json.load(open(SECRET_FILE))
    GH_TOKEN = sec.get("github_token", "")
    MINIMAX_KEY = sec.get("minimax_key", "")
    MINIMAX_GROUP = sec.get("minimax_group", "")

LOG_FILE = BASE + "/logs/run_" + time.strftime("%Y%m%d") + ".log"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = ts + "  " + msg
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with OPENER.open(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"HTTP GET error: {e}")
        return ""

def http_post(url, data, headers=None):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST")
    try:
        with OPENER.open(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        log(f"HTTP POST error: {e}")
        return {}

def gh_put_file(path, content, msg):
    url = f"https://api.github.com/repos/zenghuafeng008-cmd/Fenggeblog/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    existing = None
    try:
        req = urllib.request.Request(url, headers=headers)
        with OPENER.open(req, timeout=30) as r:
            existing = json.loads(r.read().decode())
    except:
        pass
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload = {"message": msg, "content": encoded, "branch": "main"}
    if existing and "sha" in existing:
        payload["sha"] = existing["sha"]
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    try:
        with OPENER.open(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        log(f"GitHub PUT error: {e}")
        return {}

def get_latest_video(handle):
    log(f"Checking channel: {handle}")
    cmd = ["python", "-m", "yt_dlp", "--proxy", PROXY, "--flat-playlist", "--print", "title,url,upload_date", handle]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        output = result.stdout
        videos = []
        for line in output.split("\n"):
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
        log(f"  Found {len(videos)} videos")
        return videos[0] if videos else None
    except Exception as e:
        log(f"  Error: {e}")
        return None

def get_subtitle(url):
    log("  Extracting subtitle...")
    tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "yt_sub_" + hashlib.md5(str(time.time()).encode()).hexdigest()[:8])
    cmd = ["python", "-m", "yt_dlp", "--proxy", PROXY, "--skip-download", "--write-auto-sub",
           "--sub-lang", "zh-Hans,zh-Hant,en", "-o", tmp, url]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        vtt_files = glob.glob(os.path.join(os.environ.get("TEMP", "/tmp"), "*.vtt"))
        recent = [f for f in vtt_files if os.path.getmtime(f) > time.time() - 300]
        if recent:
            with open(recent[0], "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\r?\n", "\n", text).strip()
            os.remove(recent[0])
            return text
    except Exception as e:
        log(f"  Subtitle error: {e}")
    return None

def minimax_generate(prompt):
    if not MINIMAX_KEY:
        log("  MINIMAX_API_KEY not set")
        return None
    try:
        url = f"https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId={MINIMAX_GROUP}"
        headers = {"Authorization": f"Bearer {MINIMAX_KEY}", "Content-Type": "application/json"}
        data = {"model": "MiniMax/Abab6.5s", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2048}
        resp = http_post(url, data, headers)
        if resp and "choices" in resp:
            return resp["choices"][0]["message"]["content"]
        else:
            log(f"  MiniMax unexpected response: {resp}")
    except Exception as e:
        log(f"  MiniMax error: {e}")
    return None

def build_article(vtitle, vurl, sub, ch):
    sub_short = sub[:2000] if len(sub) > 2000 else sub
    prompt = f"""你是一位专业AI科技资讯博主。请根据油管视频内容，写一篇中文原创图文文章。

视频标题：{vtitle}
视频链接：{vurl}
频道：{ch}

字幕/内容：
{sub_short}

要求：
1. 标题吸引人，含关键词
2. 结构清晰：引言 + 3-5个小标题 + 总结
3. 从视频提炼核心观点，结合AI科技/家居装修获客领域做延伸分析
4. 原创表达，符合SEO
5. 末尾加：来源：视频字幕整理 | 原视频：{vurl} + 本文由AI辅助创作
6. 直接输出Markdown格式文章，不要任何前言

现在开始写文章："""
    return minimax_generate(prompt)

def save_article(title, body, ch, vurl):
    date = time.strftime("%Y-%m-%d")
    slug = f"{date}_{ch}_article.md"
    fpath = os.path.join(BASE, "articles", slug)
    fm = f"---\ntitle: {title}\ndate: {date}\nauthor: FenggeBlog\nsource: {vurl}\nchannel: {ch}\ntags: [YouTube, AI, 原创]\n---\n\n"
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(fm + body)
    log(f"  Saved: {slug}")
    return fpath

def push_to_github(file_path, ch):
    if not GH_TOKEN:
        log("  GH_TOKEN not set, skip")
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        fname = os.path.basename(file_path)
        repo_path = f"articles/{fname}"
        msg = f"Auto: add article from {time.strftime('%Y-%m-%d')} - {ch}"
        result = gh_put_file(repo_path, content, msg)
        if result and "content" in result:
            log(f"  Pushed: {repo_path}")
            print(f"  GitHub: {result['content']['path']}")
        else:
            log(f"  Push failed: {result}")
    except Exception as e:
        log(f"  GitHub push error: {e}")

log("========== FenggeBlog Auto Task Started ==========")
log(f"Date: {time.strftime('%Y-%m-%d %H:%M')}")

for ch in CHANNELS:
    log(f"Processing channel: {ch['name']}")
    video = get_latest_video(ch["handle"])
    if not video or not video.get("url"):
        log("  No video, skip")
        continue
    title = video.get("title", "YouTube Video")
    url = video["url"]
    log(f"  Title: {title}")
    log(f"  URL: {url}")
    sub = get_subtitle(url)
    if sub:
        log(f"  Subtitle OK: {len(sub)} chars")
    else:
        log("  No subtitle")
        sub = "[无可用字幕]"
    article = build_article(title, url, sub, ch["name"])
    if article:
        fpath = save_article(title, article, ch["name"], url)
        push_to_github(fpath, ch["name"])

log("========== COMPLETE ==========")
