# -*- coding: utf-8 -*-
"""GitHub API操作模块"""
import base64, urllib.request, urllib.parse, json
from .config import OPENER, REPO_OWNER, REPO_NAME, BRANCH, Logger

def get_opener():
    import os
    from .config import PROXY
    return urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))

def gh_get(path, token):
    """获取GitHub文件内容"""
    encoded_path = urllib.parse.quote(path, safe="")
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{encoded_path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with get_opener().open(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return None

def gh_put_file(path, content_str, token, msg, logger=None):
    """上传/更新GitHub文件"""
    encoded_path = urllib.parse.quote(path, safe="")
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{encoded_path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    existing = gh_get(path, token)
    sha = existing.get("sha") if existing else None
    encoded = base64.b64encode(content_str.encode("utf-8")).decode("ascii")
    payload = {"message": msg, "content": encoded, "branch": BRANCH}
    if sha:
        payload["sha"] = sha
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    try:
        with get_opener().open(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        if logger:
            logger.log(f"gh_put error: {e}")
        return {}
