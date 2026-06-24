# -*- coding: utf-8 -*-
"""凤鸽博客 - 统一文章生成器 v3 (URL-safe)"""
import os, re, json, time, urllib.parse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.resolve()
ARTICLES_DIR = BASE_DIR / "articles"
CATEGORIES = ["AI资讯", "AI工具", "AI评测", "本地部署", "工具教程"]

def make_safe_filename(title, date_str):
    """生成URL-safe的文件名"""
    # 替换特殊字符为连字符
    safe = re.sub(r'[^\w\u4e00-\u9fff-]', '-', title)
    safe = re.sub(r'-+', '-', safe)  # 多个连字符合并
    safe = safe.strip('-')[:50]  # 限制长度
    filename = f"{date_str}_{safe}.html"
    return filename

def md_to_html(text):
    parts = []
    headings = []
    for line in text.split("\n"):
        if not line.strip():
            parts.append("")
            continue
        m = re.match(r'^## (.+)$', line.strip())
        if m:
            title = m.group(1)
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '-', title)[:30]
            parts.append(f'<h2 id="h-{anchor}">{title}</h2>')
            headings.append((title, anchor))
            continue
        m = re.match(r'^### (.+)$', line.strip())
        if m:
            parts.append(f'<h3>{m.group(1)}</h3>')
            continue
        m = re.match(r'^[-*] (.+)$', line.strip())
        if m:
            parts.append(f'<li>{m.group(1)}</li>')
            continue
        m = re.match(r'^> (.+)$', line.strip())
        if m:
            parts.append(f'<blockquote>{m.group(1)}</blockquote>')
            continue
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
        line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
        line = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<img src="\2" alt="\1">', line)
        parts.append(f'<p>{line}</p>')
    html = '\n'.join(parts)
    html = re.sub(r'<p><img', '<img', html)
    html = re.sub(r'/></p>', '/>', html)
    return html, headings

def generate_toc(headings):
    return '\n'.join([f'<li><a href="#h-{a}">{t}</a></li>' for t, a in headings])

def calculate_reading_time(text):
    return max(1, round(len(text) / 2 / 400))

def generate_article_html(title, source_url, content_md, channel, category, date_str):
    template_path = BASE_DIR / "src" / "templates" / "article.html"
    template = open(template_path, encoding="utf-8").read()
    
    content_html, headings = md_to_html(content_md)
    toc_html = generate_toc(headings) if headings else ""
    reading_time = calculate_reading_time(content_md)
    display_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}" if len(date_str) == 8 else date_str
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    filename = make_safe_filename(title, date_str)
    
    vars_dict = {
        "title": title,
        "url": f"https://0746.qzz.cn/articles/{filename}",
        "canonical_url": f"https://0746.qzz.cn/articles/{filename}",
        "description": f"{title}。了解更多AI科技资讯、工具教程。",
        "author": channel,
        "category": category,
        "cat_slug": category.lower(),
        "published_time": now,
        "modified_time": now,
        "updated_time": now,
        "publish_date": display_date,
        "reading_time": f"{reading_time} 分钟",
        "source_url": source_url,
        "source_name": source_url.split('/')[-1] if source_url else "网络",
        "toc_items": toc_html,
        "content": content_html,
        "og_image": "https://0746.qzz.cn/og-image.png",
        "prev_url": "#",
        "prev_title": "没有了",
        "next_url": "#",
        "next_title": "已经是最后一篇",
        "related_articles": "<li style='color:var(--text-muted)'>暂无相关文章</li>",
        "no_prev": "disabled",
        "no_next": "disabled"
    }
    
    for key, val in vars_dict.items():
        template = template.replace("{{" + key + "}}", str(val))
    return template, filename

def generate_articles_html(articles):
    articles_json = json.dumps(articles, ensure_ascii=False)
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文章列表 - 凤鸽博客</title>
    <meta name="description" content="凤鸽博客全部文章列表"/>
    <meta name="robots" content="follow, index"/>
    <link rel="stylesheet" href="style.css">
    <style>
        .filter-bar { display: flex; gap: 10px; margin-bottom: 30px; flex-wrap: wrap; }
        .filter-btn { background: var(--bg-tertiary); border: 1px solid var(--border-default); border-radius: var(--radius-pill); padding: 8px 16px; color: var(--text-tertiary); font-size: 14px; cursor: pointer; transition: all 0.2s; }
        .filter-btn:hover, .filter-btn.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
        .page-title { font-size: 28px; font-weight: 700; color: var(--text-primary); margin-bottom: 25px; }
    </style>
</head>
<body>
    <header class="site-header">
        <div class="header-inner">
            <a href="/" class="logo">🐦 凤鸽博客</a>
            <nav class="main-nav">
                <a href="/">首页</a>
                <a href="/articles.html" class="active">文章</a>
                <a href="/about.html">关于</a>
            </nav>
        </div>
    </header>
    <main class="home-container">
        <h1 class="page-title">📚 全部文章</h1>
        <div class="filter-bar">
            <button class="filter-btn active" data-category="all">全部</button>
            <button class="filter-btn" data-category="AI资讯">AI资讯</button>
            <button class="filter-btn" data-category="AI工具">AI工具</button>
            <button class="filter-btn" data-category="AI评测">AI评测</button>
            <button class="filter-btn" data-category="本地部署">本地部署</button>
            <button class="filter-btn" data-category="工具教程">工具教程</button>
        </div>
        <div style="margin-bottom:20px;color:var(--text-muted);font-size:14px;">共 <span id="total-count">0</span> 篇文章</div>
        <div class="article-grid" id="article-grid"></div>
        <div id="loading" style="text-align:center;padding:40px;color:var(--text-muted);">加载中...</div>
    </main>
    <footer class="site-footer">
        <div class="footer-inner">
            <div class="footer-brand"><span class="logo">🐦 凤鸽博客</span><p>专注AI科技资讯与实用工具教程</p></div>
        </div>
        <div class="footer-bottom"><p>© 2026 凤鸽博客</p></div>
    </footer>
    <script>
    var ARTICLES = ARTICLES_DATA_PLACEHOLDER;
    function renderArticles(articles) {
        var grid = document.getElementById("article-grid");
        var loading = document.getElementById("loading");
        var totalCount = document.getElementById("total-count");
        loading.style.display = "none";
        totalCount.textContent = articles.length;
        if (articles.length === 0) {
            grid.innerHTML = "<p style='color:var(--text-muted);text-align:center;padding:40px;'>暂无文章</p>";
            return;
        }
        grid.innerHTML = articles.map(function(art) {
            return "<article class='article-card' data-category='" + art.category + "'>" +
                "<div class='card-content'>" +
                "<span class='card-category'>" + art.category + "</span>" +
                "<h3 class='card-title'><a href='" + art.url + "'>" + art.title + "</a></h3>" +
                "<div class='card-meta'><span>📅 " + art.date + "</span><span>📚 " + art.category + "</span></div>" +
                "</div></article>";
        }).join("");
    }
    function filterCategory(category) {
        document.querySelectorAll(".filter-btn").forEach(function(btn) {
            btn.classList.remove("active");
            if (btn.dataset.category === category) btn.classList.add("active");
        });
        var filtered = category === "all" ? ARTICLES : ARTICLES.filter(function(a) { return a.category === category; });
        renderArticles(filtered);
    }
    document.querySelectorAll(".filter-btn").forEach(function(btn) {
        btn.addEventListener("click", function() { filterCategory(this.dataset.category); });
    });
    var urlParams = new URLSearchParams(window.location.search);
    var category = urlParams.get("category") || "all";
    renderArticles(ARTICLES);
    if (category !== "all") filterCategory(category);
    </script>
</body>
</html>'''.replace("ARTICLES_DATA_PLACEHOLDER", articles_json)

def generate_index_html():
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>凤鸽博客 - AI科技资讯 | 免费工具教程</title>
    <meta name="description" content="凤鸽博客专注分享AI科技资讯、免费工具与教程"/>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header class="site-header">
        <div class="header-inner">
            <a href="/" class="logo">🐦 凤鸽博客</a>
            <nav class="main-nav">
                <a href="/" class="active">首页</a>
                <a href="/articles.html">文章</a>
                <a href="/about.html">关于</a>
            </nav>
        </div>
    </header>
    <section class="hero">
        <h1>🐦 凤鸽博客</h1>
        <p>专注分享AI科技资讯、免费工具与实用教程</p>
        <div class="stats-bar">
            <div class="stat-item"><div class="stat-value" id="count">--</div><div class="stat-label">篇文章</div></div>
            <div class="stat-item"><div class="stat-value" id="lastUpdate">--</div><div class="stat-label">最后更新</div></div>
        </div>
    </section>
    <main class="home-container">
        <nav class="category-nav">
            <a href="/articles.html" class="category-btn active">全部</a>
            <a href="/articles.html?category=AI资讯" class="category-btn">AI资讯</a>
            <a href="/articles.html?category=AI工具" class="category-btn">AI工具</a>
            <a href="/articles.html?category=AI评测" class="category-btn">AI评测</a>
            <a href="/articles.html?category=本地部署" class="category-btn">本地部署</a>
            <a href="/articles.html?category=工具教程" class="category-btn">工具教程</a>
        </nav>
        <section class="all-articles">
            <h2 class="section-title">📚 最新文章</h2>
            <div class="article-grid" id="latest-articles">
                <p style="color:var(--text-muted);text-align:center;padding:40px;">正在加载文章...</p>
            </div>
        </section>
    </main>
    <footer class="site-footer">
        <div class="footer-inner">
            <div class="footer-brand"><span class="logo">🐦 凤鸽博客</span><p>专注AI科技资讯与实用工具教程</p></div>
            <div class="footer-links">
                <div class="link-group"><h4>分类</h4><a href="/articles.html?category=AI资讯">AI资讯</a><a href="/articles.html?category=AI工具">AI工具</a></div>
                <div class="link-group"><h4>资源</h4><a href="/sitemap.xml">网站地图</a></div>
            </div>
        </div>
        <div class="footer-bottom"><p>© 2026 凤鸽博客</p></div>
    </footer>
    <script>
    fetch("/articles/stats.json").then(r=>r.json()).then(function(data) {
        document.getElementById("count").textContent = data.count || 0;
        document.getElementById("lastUpdate").textContent = data.lastUpdate || "-";
    }).catch(function(){});
    </script>
</body>
</html>'''

def run():
    print("=== 凤鸽博客生成器 v3 (URL-safe) ===")
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = BASE_DIR / "articles"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    articles = []
    for f in ARTICLES_DIR.glob("*.md"):
        name = f.stem
        parts = name.split("_", 1)
        if len(parts) == 2:
            date_str = parts[0]
            title = parts[1].replace("-", " ")
            articles.append({
                "title": title,
                "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
                "date_str": date_str,
                "category": "AI工具",
                "source_url": "",
                "file": f
            })
    
    articles.sort(key=lambda x: x.get("date_str", ""), reverse=True)
    
    generated = []
    for i, art in enumerate(articles):
        try:
            content = open(art["file"], encoding="utf-8").read()
            html, filename = generate_article_html(
                art["title"], art.get("source_url", ""), content,
                "凤鸽", art["category"], art["date_str"]
            )
            output_path = output_dir / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  Generated: articles/{filename}")
            generated.append({
                "title": art["title"],
                "date": art["date"],
                "category": art["category"],
                "url": f"/articles/{filename}"
            })
        except Exception as e:
            print(f"  Error: {art['title']} - {e}")
    
    stats = {
        "count": len(generated),
        "lastUpdate": generated[0]["date"] if generated else None,
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(output_dir / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    with open(BASE_DIR / "articles.html", "w", encoding="utf-8") as f:
        f.write(generate_articles_html(generated))
    
    with open(BASE_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(generate_index_html())
    
    print(f"\n完成！共 {len(generated)} 篇文章")
    return generated, stats

if __name__ == "__main__":
    run()
