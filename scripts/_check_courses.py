"""查看课程数据和课程包 Sheet"""
import os, sys
base = r'C:\Users\12225\.openclaw\workspace\projects\gym-excel-system'
sys.path.insert(0, base)
os.chdir(base)

from core.excel_engine import ExcelEngine
from config import EXCEL_PATH, SHEETS

e = ExcelEngine(EXCEL_PATH)

# 课程数据
courses = e.get_all_data(SHEETS["course"])
print(f"Total courses: {len(courses)}")
for c in courses:
    ctype = c.get("课程类型", "")
    name = c.get("课程名称", "")
    status = c.get("课程状态", "")
    cid = c.get("课程编号", "")
    price = c.get("标准售价", "")
    print(f"  {cid} | {name} | 类型={ctype} | 状态={status} | 售价={price}")

print()
print("SHEETS keys:", list(SHEETS.keys()))
