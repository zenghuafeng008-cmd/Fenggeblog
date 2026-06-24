# -*- coding: utf-8 -*-
"""增强版HTML生成器 - 对标freedidi.com"""
import re
from datetime import datetime

def md_to_html(md_text):
    """Markdown转HTML"""
    parts = []
    for line in md_text.split("\n"):
        m = re.match(r'^### (.+)$', line)
        if m:
            parts.append(f'<h3>{m.group(1)}</h3>'); continue
        m = re.match(r'^## (.+)$', line)
        if m:
            hid = re.sub(r'[^\w\u4e00-\u9fff-]', '-', m.group(1))[:30]
            parts.append(f'<h2 id="h-{hid}">{m.group(1)}</h2>'); continue
        m = re.match(r'^# (.+)$', line)
        if m:
            parts.append(f'<h1>{m.group(1)}</h1>'); continue
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
        line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
        line = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<img src="\2" alt="\1">', line)
        m = re.match(r'^> (.+)$', line)
        if m:
            parts.append(f'<blockquote>{m.group(1)}</blockquote>'); continue
        m = re.match(r'^[-*] (.+)$', line)
        if m:
            parts.append(f'<li>{m.group(1)}</li>'); continue
        if not line.strip():
            parts.append('<br>')
        else:
            parts.append(f'<p>{line}</p>')
    html = '\n'.join(parts)
    html = re.sub(r'<p><img', '<img', html)
    html = re.sub(r'/></p>', '/>', html)
    return html

def generate_toc(md_text):
    """从Markdown生成目录"""
    items = []
    for line in md_text.split("\n"):
        m = re.match(r'^## (.+)$', line)
        if m:
            title = m.group(1)
            hid = re.sub(r'[^\w\u4e00-\u9fff-]', '-', title)[:30]
            items.append(f'<li><a href="#h-{hid}">{title}</a></li>')
    return '\n'.join(items)

def calculate_reading_time(text):
    """计算阅读时间"""
    words = len(text) / 2  # 中文字符
    minutes = max(1, round(words / 400))
    return f"{minutes} 分钟"

def make_article_html(title, url, channel, category, content_md, date_str, 
                      source_url=None, related=None, prev_article=None, next_article=None):
    """生成完整文章HTML"""
    content_html = md_to_html(content_md)
    toc_items = generate_toc(content_md)
    reading_time = calculate_reading_time(content_md)
    
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    publish_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    # 格式化日期显示
    display_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    # 相关文章
    related_html = ""
    if related:
        related_items = []
        for r in related[:5]:
            r_date = r.get('date', '')[:10] if r.get('date') else ''
            related_items.append(f'<li><a href="{r["url"]}">{r["title"]}</a><span>{r_date}</span></li>')
        related_html = '\n'.join(related_items)
    else:
        related_html = '<li style="color:var(--text-muted)">暂无相关文章</li>'
    
    # 上一篇/下一篇
    prev_html = ""
    next_html = ""
    if prev_article:
        prev_html = f'<a href="{prev_article["url"]}" class="nav-link prev"><span>← 上一篇</span><span class="nav-title">{prev_article["title"]}</span></a>'
    else:
        prev_html = '<span class="nav-link prev disabled"><span>← 上一篇</span><span class="nav-title">没有了</span></span>'
    
    if next_article:
        next_html = f'<a href="{next_article["url"]}" class="nav-link next"><span>下一篇 →</span><span class="nav-title">{next_article["title"]}</span></a>'
    else:
        next_html = '<span class="nav-link next disabled"><span>没有了</span><span class="nav-title">已经是最后一篇</span></span>'
    
    # 分类slug
    cat_slug = category.lower()
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN" prefix="og: https://ogp.me/ns#">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="follow, index, max-snippet:-1, max-video-preview:-1, max-image-preview:large"/>
    <link rel="canonical" href="{url}"/>
    
    <title>{title} - 凤鸽博客</title>
    <meta name="description" content="{title}。了解更多AI科技资讯、工具教程。"/>
    
    <meta property="og:locale" content="zh_CN"/>
    <meta property="og:type" content="article"/>
    <meta property="og:title" content="{title}"/>
    <meta property="og:description" content="{title}。了解更多AI科技资讯、工具教程。"/>
    <meta property="og:url" content="{url}"/>
    <meta property="og:site_name" content="凤鸽博客"/>
    <meta property="og:updated_time" content="{now}"/>
    <meta property="article:published_time" content="{now}"/>
    <meta property="article:modified_time" content="{now}"/>
    <meta property="article:section" content="{category}"/>
    
    <meta name="twitter:card" content="summary_large_image"/>
    <meta name="twitter:title" content="{title}"/>
    <meta name="twitter:description" content="{title}。"/>
    <meta name="twitter:label1" content="Written by"/>
    <meta name="twitter:data1" content="{channel}"/>
    <meta name="twitter:label2" content="Time to read"/>
    <meta name="twitter:data2" content="{reading_time}"/>
    
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": "{title}",
        "datePublished": "{now}",
        "dateModified": "{now}",
        "articleSection": "{category}",
        "author": {{"@type": "Person", "name": "{channel}"}},
        "publisher": {{"@type": "Organization", "name": "凤鸽博客", "url": "https://0746.qzz.cn"}},
        "description": "{title}。",
        "inLanguage": "zh-Hans",
        "mainEntityOfPage": {{"@type": "WebPage", "@id": "{url}"}}
    }}
    </script>
    
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <nav class="breadcrumb">
        <div class="breadcrumb-inner">
            <a href="/">首页</a>
            <span class="separator">›</span>
            <a href="/category/{cat_slug}">{category}</a>
            <span class="separator">›</span>
            <span class="current">{title}</span>
        </div>
    </nav>
    
    <article class="article-container">
        <header class="article-header">
            <h1 class="article-title">{title}</h1>
            <div class="article-meta">
                <span class="category-tag">{category}</span>
                <span>👤 {channel}</span>
                <span>📅 {display_date}</span>
                <span>⏱️ {reading_time}</span>
            </div>
            <div class="article-source">来源：<a href="{source_url or url}" target="_blank">{source_url or url}</a></div>
        </header>
        
        <nav class="toc">
            <div class="toc-title">📑 文章目录</div>
            <ol>{toc_items}</ol>
        </nav>
        
        <div class="article-body">
            {content_html}
        </div>
        
        <footer class="article-footer">
            <div class="article-tags">
                <span class="tag-label">标签：</span>
                <span class="article-tag">{category}</span>
            </div>
            
            <div class="share-bar">
                <span>分享到：</span>
                <button class="share-btn wx" onclick="alert('请截图分享到微信')">微信</button>
                <button class="share-btn wb" onclick="window.open('https://service.weibo.com/share/share.php?url='+encodeURIComponent(location.href),'_blank')">微博</button>
                <button class="share-btn" onclick="navigator.clipboard.writeText(location.href).then(()=>alert('链接已复制'))">复制链接</button>
            </div>
            
            <nav class="article-nav">
                {prev_html}
                {next_html}
            </nav>
            
            <section class="related-articles">
                <h3>📌 相关推荐</h3>
                <ul>
                    {related_html}
                </ul>
            </section>
            
            <a href="/" class="back-link">← 返回首页</a>
        </footer>
    </article>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        // 目录高亮
        const tocLinks = document.querySelectorAll('.toc a');
        const headings = document.querySelectorAll('.article-body h2');
        if (tocLinks.length < 2) document.querySelector('.toc').style.display = 'none';
    }});
    </script>
</body>
</html>'''
