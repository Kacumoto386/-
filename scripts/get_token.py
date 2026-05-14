# -*- coding: utf-8 -*-
"""get feishu token from openclaw gateway"""
import http.client, json

try:
    conn = http.client.HTTPConnection("localhost", 17789, timeout=5)
    conn.request("GET", "/api/feishu/token")
    r = conn.getresponse()
    data = json.loads(r.read())
    print(json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"Error: {e}")
