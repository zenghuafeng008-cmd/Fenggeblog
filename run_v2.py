import os, json, base64, hashlib, urllib.request, re, time, glob, subprocess, random
PROXY = "http://127.0.0.1:20808"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
CHANNELS = [
    {"Name": "yunfeifei", "handle": "https://www.youtube.com/@yunfeifei-k5h"},
    {"Name": "lingdujieshuo", "handle": "https://www.youtube.com/@lingdujieshuo"},
]
BASE = r"H:/workspace/01_项目/P09_YoutubeAutoBlog"
ARTICLES_HTML_DIR = BASE + "/html_articles"
os.makedirs(BASE+"/articles", exist_ok=True)
os.makedirs(BASE+"/logs", exist_ok=True)
os.makedirs(ARTICLES_HTML_DIR, exist_ok=True)

SECRET_FILE = BASE+"/.secrets.json"
GH_TOKEN = MINIMAX_KEY = ""
if os.path.exists(SECRET_FILE):
    sec = json.load(open(SECRET_FILE, encoding='utf-8-sig'))
    GH_TOKEN = sec.get("github_token","")
    MINIMAX_KEY = sec.get("minimax_key","")

LOG_FILE = BASE+"/logs/run_"+time.strftime("%Y%m%d")+".log"

CATEGORIES = ["AI资讯","AI工具","AI评测","本地部署","工具教程"]
AD_PLACEHOLDER = "<div class=\"ad-inline\"><span>广告位招商中 | 联系：zenghuafeng008@gmail.com</span></div>"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = ts+"  "+msg
    print(line)
    with open(LOG_FILE,"a",encoding="utf-8") as f: f.write(line+"\n")

def gh_get(path):
    url = f"https://api.github.com/repos/zenghuafeng008-cmd/Fenggeblog/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with OPENER.open(req, timeout=30) as r: return json.loads(r.read().decode())
    except: return None

def gh_put_file(path, content, msg):
    url = f"https://api.github.com/repos/zenghuafeng008-cmd/Fenggeblog/contents/{path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    existing = gh_get(path)
    sha = existing.get("sha") if existing else None
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload = {"message": msg, "content": encoded, "branch": "main"}
    if sha: payload["sha"] = sha
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    try:
        with OPENER.open(req, timeout=30) as r: return json.loads(r.read().decode())
    except Exception as e:
        log(f"GitHub PUT error: {e}")
        return {}

def get_latest_videos(handle, limit=5):
    log(f"Checking: {handle}")
    cmd = ["python","-m","yt_dlp","--proxy",PROXY,"--flat-playlist","--print","title,url,upload_date",handle]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        videos = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if re.match(r"^https?://", line): videos.append({"url": line})
            elif re.match(r"^\d{8}$", line):
                if videos: videos[-1]["date"] = line
            elif len(line)>3 and not line.startswith("["):
                if videos and "title" not in videos[-1]: videos[-1]["title"] = line
                elif not videos: videos = [{"title": line, "url": ""}]
        log(f"  Found {len(videos)} videos")
        return videos[:limit]
    except Exception as e:
        log(f"  Error: {e}")
        return []

def get_subtitle(url):
    log("  Extracting subtitle...")
    tmp = os.path.join(os.environ.get("TEMP","/tmp"), "yt_"+hashlib.md5(str(time.time()).encode()).hexdigest()[:8])
    cmd = ["python","-m","yt_dlp","--proxy",PROXY,"--skip-download","--write-auto-sub","--sub-lang","zh-Hans,zh-Hant,en","-o",tmp,url]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        vtt_files = glob.glob(os.path.join(os.environ.get("TEMP","/tmp"),"*.vtt"))
        recent = [f for f in vtt_files if os.path.getmtime(f) > time.time()-300]
        if recent:
            with open(recent[0],"r",encoding="utf-8",errors="replace") as f: text = f.read()
            text = re.sub(r"<[^>]+>","",text)
            text = re.sub(r"\r?\n","\n",text).strip()
            os.remove(recent[0])
            return text
    except Exception as e: log(f"  Subtitle error: {e}")
    return None

def minimax(prompt):
    if not MINIMAX_KEY: log("  MINIMAX_KEY not set"); return None
    try:
        url = "https://api.minimax.chat/v1/chat/completions"
        headers = {"Authorization": f"Bearer {MINIMAX_KEY}", "Content-Type": "application/json"}
        data = {"model": "abab6.5s-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500}
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with OPENER.open(req, timeout=120) as r: resp = json.loads(r.read().decode("utf-8"))
        if resp and "choices" in resp: return resp["choices"][0]["message"]["content"]
        log(f"  MiniMax: {str(resp)[:100]}")
    except Exception as e: log(f"  MiniMax error: {e}")
    return None

def generate_seo_article(video_title, video_url, subtitle, channel):
    sub_short = subtitle[:2500] if len(subtitle)>2500 else subtitle
    prompt = f"""你是一位资深AI科技内容创作者，擅长SEO软文写作。

视频信息：
标题：{video_title}
链接：{video_url}
频道：{channel}

字幕内容：
{sub_short}

请生成一篇SEO优化的深度图文文章，要求：

【文章结构】
1. 吸引人的SEO标题（含主关键词，控制在60字内）
2. 导语（100字，引出话题，制造阅读期待）
3. 核心内容（4-6个小标题，每个小标题下2-3段，每段150-200字）
4. 总结（100字，含行动召唤）
5. 相关文章推荐（2-3条，用###分隔）

【SEO要求】
- 主关键词在标题、第一个小标题、meta description中出现
- 关键词密度2-3%（自然分布，不要堆砌）
- 使用H2/H3标签结构
- 文章字数1500-2500字
- 每段简短有力，适合移动端阅读

【内容质量】
- 结合视频核心观点延伸分析
- 加入行业洞察和实操建议
- 观点独特，不做泛泛而谈
- 原文照抄字幕是大忌，必须深度加工

【广告位】
在文章第三个小标题结尾处插入占位符：<div class="ad-inline"><span>广告位招商中 | 联系：zenghuafeng008@gmail.com</span></div>

【末尾】
末尾注明：来源：视频字幕整理 | 原视频：{video_url} | 本文由AI辅助创作

输出格式：直接输出文章内容，用## H2标题、### H3标题区分层级。输出纯Markdown。"""
    return minimax(prompt)

def build_article_html(title, content_md, video_url, channel, category, date_str, views="1.2K"):
    slug = re.sub(r'[^\w\u4e00-\u9fa5]+','-',title)[:50]
    slug = re.sub(r'-+','-',slug).strip('-')
    filename = f"{date_str.replace('-','')}_{slug}.html"
    excerpt = re.sub(r'[#*>\[\]]','',content_md[:200]).strip()
    
    article_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | FenggeBlog</title>
<meta name="description" content="{excerpt}">
<meta name="keywords" content="{channel}, AI教程, 科技资讯, 工具评测">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://0746.qzz.io/articles/{filename}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{excerpt}">
<meta property="og:type" content="article">
<meta property="article:published_time" content="{date_str}T09:00:00+08:00">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<header>
<div class="container header-inner">
<div class="logo">Fengge<span>Blog</span></div>
<nav>
<a href="../index.html">首页</a>
<a href="../articles.html" class="active">文章</a>
<a href="../videos.html">视频</a>
<a href="../about.html">关于</a>
<a href="../contact.html">联系</a>
</nav>
</div>
</header>

<div class="container article-container">
<div class="article-header">
<div class="article-meta">
<span class="category-tag">{category}</span>
<span>{date_str}</span>
<span>👁 {views}</span>
<span>{channel}</span>
</div>
<h1 class="article-title">{title}</h1>
<div class="article-source">来源：<a href="{video_url}" target="_blank">YouTube视频</a> | 本文由AI辅助创作</div>
</div>

<div class="article-body">
{content_md}
</div>

<div class="article-footer">
<div class="article-tags">
<span class="tag">AI教程</span>
<span class="tag">{channel}</span>
<span class="tag">科技资讯</span>
</div>
<div class="article-nav">
<a href="../articles.html" class="back-link">← 返回文章列表</a>
</div>
</div>

<div class="ad-banner">📢 <strong>广告位招商中</strong> | 日均 5000+ 精准 AI 受众（联系：zenghuafeng008@gmail.com）</div>
</div>

<footer>
<div class="container">
<div class="footer-links">
<a href="../index.html">首页</a>
<a href="../articles.html">文章</a>
<a href="../videos.html">视频</a>
<a href="../about.html">关于</a>
<a href="../contact.html">联系</a>
</div>
<p>&copy; 2026 <a href="../index.html">FenggeBlog</a> | AI 前沿资讯</p>
</div>
</body>
</html>'''
    return filename, article_html

def update_articles_html(new_card_html):
    log("  Updating articles.html...")
    articles_path = "articles.html"
    existing = gh_get(articles_path)
    if not existing:
        log("  articles.html not found, creating new")
        return False
    content_b64 = existing.get("content","")
    content = base64.b64decode(content_b64).decode("utf-8")
    sha = existing.get("sha")
    
    # Find insertion point: after first <article class="article-card"> and before </div> of grid
    card = f'''<article class="article-card">
{new_card_html}
</article>'''
    # Insert after the grid opening div
    import_text = '<!-- AUTO_INSERT -->'
    if import_text not in content:
        # Find the first </article> card and insert after it
        pattern = r'(<div style="display:grid[^>]*>)(.*?)(</div>\s*</div>\s*<footer>)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            grid_start = match.group(1)
            grid_rest = match.group(2)
            grid_end = match.group(3)
            content = grid_start + new_card_html + grid_rest + grid_end
        else:
            log("  Could not find grid insertion point")
            return False
    sha = existing.get("sha")
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    payload = {"message": f"Auto: add new article {time.strftime('%Y-%m-%d')}", "content": encoded, "branch": "main", "sha": sha}
    body = json.dumps(payload).encode()
    url = f"https://api.github.com/repos/zenghuafeng008-cmd/Fenggeblog/contents/{articles_path}"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    try:
        with OPENER.open(req, timeout=30) as r: result = json.loads(r.read().decode())
        log(f"  articles.html updated OK")
        return True
    except Exception as e:
        log(f"  articles.html update error: {e}")
        return False

def make_card(category, date_str, views, title, excerpt, article_filename):
    return f'''<div class="card-meta"><span class="category">{category}</span><span>{date_str}</span><span>👁 {views}</span></div>
<h2 class="card-title" style="font-size:17px"><a href="articles/{article_filename}" style="color:inherit;text-decoration:none">{title}</a></h2>
<p class="card-excerpt">{excerpt}</p>
<div class="card-footer">
<a href="articles/{article_filename}" class="read-more">阅读全文 →</a>
<span class="video-badge">🎬 视频</span>
</div>'''

log("========== START: v2.0 ==========")
log(f"Date: {time.strftime('%Y-%m-%d %H:%M')}")

for ch in CHANNELS:
    log(f"Processing: {ch["Name"]}")
    videos = get_latest_videos(ch["handle"], limit=2)
    if not videos:
        log("  No videos, skip")
        continue
    
    video = videos[0]
    title = video.get("title","YouTube Video")
    url = video.get("url","")
    date_str = video.get("date","")
    if date_str: date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    else: date_str = time.strftime("%Y-%m-%d")
    log(f"  Title: {title}")
    log(f"  URL: {url}")
    
    sub = get_subtitle(url)
    if sub:
        log(f"  Subtitle OK: {len(sub)} chars")
    else:
        sub = "[无可用字幕，视频内容待整理]"
        log("  No subtitle")
    
    category = random.choice(CATEGORIES)
    views = random.choice(["1.5K","2.1K","3.2K","4.8K","5.6K","980","1.2K"])
    
    content_md = generate_seo_article(title, url, sub, ch["Name"])
    if not content_md:
        log("  Article generation failed, skip")
        continue
    
    filename, article_html = build_article_html(title, content_md, url, ch["Name"], category, date_str, views)
    excerpt = re.sub(r'[#*>\[\]!]','',content_md[:150]).strip()
    excerpt = excerpt[:120]+"..." if len(excerpt)>120 else excerpt
    
    # Save locally
    fpath = os.path.join(ARTICLES_HTML_DIR, filename)
    with open(fpath,"w",encoding="utf-8") as f: f.write(article_html)
    log(f"  Saved: {filename}")
    
    # Push to GitHub
    msg = f"Auto: add article {title[:30]}..."
    result = gh_put_file(f"articles/{filename}", article_html, msg)
    if result and "content" in result:
        log(f"  GitHub OK: articles/{filename}")
        # Update articles.html with new card
        card_html = make_card(category, date_str, views, title, excerpt, filename)
        update_articles_html(card_html)
    else:
        log(f"  GitHub push failed: {str(result)[:100]}")
    
    # Also save markdown
    md_path = os.path.join(BASE,"articles",filename.replace(".html",".md"))
    with open(md_path,"w",encoding="utf-8") as f: f.write(f"# {title}\n\n来源：{url}\n\n{content_md}\n")
    log(f"  Markdown saved: {os.path.basename(md_path)}")

log("========== COMPLETE v2.0 ==========")