# -*- coding: utf-8 -*-
"""
通过 OpenClaw Gateway API 发送飞书文件
"""
import subprocess, json, os, sys

FILE_PATH = "C:/Users/12225/.openclaw/workspace/projects/gym-excel-system/docs/系统操作手册.md"

# Read file content
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File size: {len(content)} chars, {os.path.getsize(FILE_PATH)} bytes")
print(f"Lines: {content.count(chr(10)) + 1}")

# Try to use the message tool with file upload
# OpenClaw's 'message' tool with buffer and filename
print(f"\nI'll send this via im:resource API or the OpenClaw message tool")
print("Trying OpenClaw's native file send capability...")
