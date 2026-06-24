# -*- coding: utf-8 -*-
"""内容生成模块 - MiniMax API"""
import json, urllib.request
from .config import PROXY, MINIMAX_ENDPOINT, MODEL, MAX_TOKENS

def generate_article(title, url, subtitle, channel, api_key, proxy=None, max_tokens=None):
    """使用MiniMax生成文章"""
    if not api_key:
        return None
    proxy = proxy or PROXY
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    
    sub_short = subtitle[:4000] if len(subtitle) > 4000 else subtitle
    prompt = f"""你是专注于AI科技资讯的写手。请根据以下内容写一篇1500字以上的中文原创图文文章，包含多个小标题和图片，直接输出Markdown格式。

标题：{title}
链接：{url}

内容：\n{sub_short}

要求：包含4-6个小标题，文章中间和末尾要有图片，直接输出Markdown格式。"""
    
    try:
        api_url = f"{MINIMAX_ENDPOINT}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], 
                "max_tokens": max_tokens or MAX_TOKENS}
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(api_url, data=body, headers=headers, method="POST")
        with opener.open(req, timeout=180) as r:
            resp = json.loads(r.read().decode("utf-8"))
        if resp and "choices" in resp:
            return resp["choices"][0]["message"]["content"]
    except Exception as e:
        pass
    return None
