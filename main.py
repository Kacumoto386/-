#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
健身房Excel管理系统 - 主入口
基于Python GUI (Tkinter) + Excel引擎的健身房会员管理系统
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox

# 确保项目根目录在Path中
if getattr(sys, 'frozen', False):
    # 打包运行：exe所在目录
    PROJECT_ROOT = os.path.dirname(sys.executable)
    # 打包模式下，数据文件夹在 _MEIPASS，添加 scripts 到 sys.path 以便 import
    if hasattr(sys, '_MEIPASS'):
        meipass_scripts = os.path.join(sys._MEIPASS, 'scripts')
        if os.path.exists(meipass_scripts) and meipass_scripts not in sys.path:
            sys.path.insert(0, meipass_scripts)
else:
    # 源码运行：脚本所在目录
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def check_dependencies():
    """检查依赖库是否安装"""
    missing = []
    try:
        import openpyxl
    except ImportError:
        missing.append("openpyxl")

    if missing:
        root = tk.Tk()
        root.withdraw()
        msg = (f"缺少依赖库: {', '.join(missing)}\n\n"
               f"请运行以下命令安装：\n"
               f"pip install openpyxl")
        messagebox.showerror("依赖检查失败", msg)
        root.destroy()
        return False
    return True


def check_workbook():
    """检查工作簿是否存在，不存在则初始化"""
    from config import EXCEL_PATH
    if not os.path.exists(EXCEL_PATH):
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(
            "初始化工作簿",
            f"数据文件 '{EXCEL_PATH}' 不存在。\n\n是否立即创建初始工作簿？（需要约10秒）"
        )
        root.destroy()

        if result:
            print("正在初始化Excel工作簿...")
            try:
                # 确保 scripts 目录在 sys.path 中（兼容打包和源码运行）
                scripts_dir = os.path.join(PROJECT_ROOT, "scripts")
                if scripts_dir not in sys.path:
                    sys.path.insert(0, scripts_dir)
                import init_workbook
                init_workbook.main()
                print("工作簿初始化完成！")
                return True
            except Exception as e:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("初始化失败", f"工作簿初始化失败：{str(e)}")
                root.destroy()
                return False
        else:
            return False
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("  健身房Excel管理系统 v2.0")
    print("  Python GUI + openpyxl 引擎")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        print("依赖检查失败，退出。")
        sys.exit(1)

    # 检查/初始化工作簿
    if not check_workbook():
        print("工作簿未就绪，退出。")
        sys.exit(1)

    # 启动GUI
    try:
        from gui.main_window import MainWindow
        app = MainWindow()
        app.run()
    except ImportError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动失败",
                             f"GUI模块加载失败：{str(e)}\n\n"
                             f"请确保项目结构完整。")
        root.destroy()
        sys.exit(1)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("运行时错误",
                             f"程序遇到错误：\n{str(e)}")
        root.destroy()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
