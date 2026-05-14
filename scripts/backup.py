#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本备份工具 — 鼠小弟的健身系统
用法: python scripts/backup.py [备注信息]
示例: python scripts/backup.py "修复了6个白屏页面和2个按钮交互"
"""

import os, sys, shutil, json
from datetime import datetime

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_ROOT = os.path.join(BASE_DIR, "..", "_backups")

# 从config读取版本号
sys.path.insert(0, BASE_DIR)
try:
    from config import __version__, PROJECT_NAME
except ImportError:
    __version__ = "unknown"
    PROJECT_NAME = "鼠小弟的健身系统"

def get_backup_path(version, comment=""):
    """生成备份路径: _backups/V{version}_备注_YYYYMMDD_HHMMSS/"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    comment_part = f"_{comment}" if comment else ""
    folder_name = f"V{version}{comment_part}_{ts}"
    return os.path.join(BACKUP_ROOT, folder_name)

def collect_files(base_dir):
    """收集需要备份的文件列表"""
    source_dirs = ["config.py", "main.py"]
    source_dirs_file = os.path.join(base_dir, "source_dirs.txt")
    
    if os.path.exists(source_dirs_file):
        with open(source_dirs_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # 默认收集关键目录
    default = ["config.py", "main.py", "core", "gui", "api", "docs", "scripts", "data"]
    return [d for d in default if os.path.exists(os.path.join(base_dir, d))]

def backup(comment=""):
    """执行备份"""
    src = BASE_DIR
    dst = get_backup_path(__version__, comment)
    
    os.makedirs(dst, exist_ok=True)
    
    items = collect_files(src)
    count = 0
    
    for item in items:
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True, 
                          ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            count += 1
        elif os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
            count += 1
    
    # 生成备份信息
    info = {
        "project": PROJECT_NAME,
        "version": __version__,
        "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "comment": comment,
        "files_count": count,
        "items": items,
    }
    with open(os.path.join(dst, "_backup_info.json"), 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    
    # 统计大小
    total_size = 0
    for root, dirs, files in os.walk(dst):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    
    info_msg = (f"[OK] 备份完成\n"
                f"   路径: {dst}\n"
                f"   版本: {__version__}\n"
                f"   文件: {count} 项, {total_size/1024:.1f} KB\n")
    if comment:
        info_msg += f"   备注: {comment}\n"
    print(info_msg)
    
    return dst

if __name__ == "__main__":
    comment = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    backup(comment)
