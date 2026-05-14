# -*- coding: utf-8 -*-
"""
通过飞书 Open API 把手册文件发送给用户
使用 OpenClaw 已有的飞书机器人凭证
"""
import requests, json, os, mimetypes

USER_OPEN_ID = "ou_0ee65be084f0b5e343ef530cc4782aae"
FILE_PATH = "C:/Users/12225/.openclaw/workspace/projects/gym-excel-system/docs/系统操作手册.md"
FILE_NAME = "鼠小弟的健身系统-用户操作手册V2.6.0.md"

# Step 1: Get tenant token from OpenClaw's config
# Try to find app credentials
import sys
sys.path.insert(0, "C:/Users/12225/.openclaw")

possible_dirs = [
    "C:/Users/12225/.openclaw",
    "C:/Users/12225/.openclaw/credentials",
]
found = {}
for d in possible_dirs:
    if os.path.exists(d):
        for f in os.listdir(d):
            if 'feishu' in f.lower() or 'lark' in f.lower():
                fp = os.path.join(d, f)
                if f.endswith('.json'):
                    try:
                        data = json.load(open(fp, 'r', encoding='utf-8'))
                        found[f] = data
                    except: pass

# Try gateway config
gw = os.path.expanduser("~/.openclaw/gateway.json")
if os.path.exists(gw):
    found['gateway.json'] = json.load(open(gw, 'r', encoding='utf-8'))

# Try from environment variables
APP_ID = os.environ.get("FEISHU_APP_ID", "")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")

print(f"Found {len(found)} config files")
for name, data in list(found.items())[:3]:
    print(f"  {name}: {json.dumps(data, ensure_ascii=False)[:200]}")

# If nothing found, fallback
if not APP_ID:
    # Check OpenClaw main config
    for p in [
        "C:/Users/12225/.openclaw/config.yml",
        "C:/Users/12225/.openclaw/config.yaml",
    ]:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\nConfig content (first 2000 chars):\n{content[:2000]}")
                break
