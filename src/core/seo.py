# -*- coding: utf-8 -*-
"""SEO优化模块"""
import os, re, json, time
from datetime import datetime
from pathlib import Path

def generate_sitemap(articles_dir, base_url="https://0746.qzz.cn"):
    """生成sitemap.xml"""
    articles = []
    
    if os.path.exists(articles_dir):
        for f in os.listdir(articles_dir):
            if f.endswith(".html"):
                filepath = os.path.join(articles_dir, f)
                mtime = os.path.getmtime(filepath)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
                articles.append({
                    "url": f"{base_url}/html_articles/{f}",
                    "date": date_str,
                    "priority": "0.8" if "AI" in f else "0.6"
                })
    
    urls = []
    for art in articles:
        urls.append(f'''  <url>
    <loc>{art['url']}</loc>
    <lastmod>{art['date']}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{art['priority']}</priority>
  </url>''')
    
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
{chr(10).join(urls)}
</urlset>'''
    
    return sitemap

def generate_robots_txt(base_url="https://0746.qzz.cn"):
    """生成robots.txt"""
    return f'''User-agent: *
Allow: /
Disallow: /logs/
Disallow: /__pycache__/
Disallow: /.git/

Sitemap: {base_url}/sitemap.xml'''

def generate_json_ld_article(title, description, url, author, date, category):
    """生成文章JSON-LD结构化数据"""
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": url,
        "author": {
            "@type": "Person",
            "name": author
        },
        "publisher": {
            "@type": "Organization",
            "name": "凤鸽博客",
            "url": "https://0746.qzz.cn",
            "logo": {
                "@type": "ImageObject",
                "url": f"{base_url}/logo.png"
            }
        },
        "datePublished": date,
        "dateModified": date,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url
        },
        "articleSection": category,
        "keywords": category
    }

def optimize_html_meta(html_content, title, description, keywords, og_image=None):
    """优化HTML的meta标签"""
    base_url = "https://0746.qzz.cn"
    
    # 更新description
    if description:
        html_content = re.sub(
            r'<meta name="description" content="[^"]*">',
            f'<meta name="description" content="{description}">',
            html_content
        )
    
    # 更新keywords
    if keywords:
        html_content = re.sub(
            r'<meta name="keywords" content="[^"]*">',
            f'<meta name="keywords" content="{keywords}">',
            html_content
        )
    
    # 更新OG标签
    if title:
        html_content = re.sub(
            r'<meta property="og:title" content="[^"]*">',
            f'<meta property="og:title" content="{title}">',
            html_content
        )
    
    if description:
        html_content = re.sub(
            r'<meta property="og:description" content="[^"]*">',
            f'<meta property="og:description" content="{description}">',
            html_content
        )
    
    if og_image:
        og_img_tag = f'<meta property="og:image" content="{og_image}">'
        if 'og:image' not in html_content:
            html_content = html_content.replace('</head>', f'{og_img_tag}</head>')
    
    return html_content

def generate_stats_json(articles_dir):
    """生成站点统计"""
    count = 0
    categories = {}
    last_update = None
    
    if os.path.exists(articles_dir):
        for f in os.listdir(articles_dir):
            if f.endswith(".html"):
                count += 1
                mtime = os.path.getmtime(os.path.join(articles_dir, f))
                if last_update is None or mtime > last_update:
                    last_update = mtime
                
                # 简单分类统计
                for cat in ["AI资讯", "AI工具", "AI评测", "本地部署", "工具教程"]:
                    if cat in f:
                        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "count": count,
        "categories": categories,
        "lastUpdate": datetime.fromtimestamp(last_update).strftime("%Y-%m-%d") if last_update else None,
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
