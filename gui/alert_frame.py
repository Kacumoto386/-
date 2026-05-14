"""
到期提醒模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from gui.base_frame import BaseDataFrame


class AlertFrame(ttk.Frame):
    """到期提醒管理"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.build_ui()
        self.load_alerts()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))

        ttk.Label(header, text="⏰ 到期提醒 & 智能预警",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        tk.Button(header, text="🔄 重新检测", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.load_alerts).pack(side=tk.RIGHT, padx=5)

        # 说明
        ttk.Label(header, text="自动检测会员剩余课时不足、长期未到店、即将过期等情况",
                  font=("微软雅黑", 9), foreground="#999999").pack(side=tk.RIGHT, padx=10)

        # 筛选
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(filter_frame, text="紧急程度筛选：",
                  font=("微软雅黑", 10)).pack(side=tk.LEFT)

        self.filter_var = tk.StringVar(value="全部")
        filter_menu = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                   values=["全部", "紧急(7天内)", "关注(30天内)"],
                                   state="readonly", width=15, font=("微软雅黑", 9))
        filter_menu.pack(side=tk.LEFT, padx=5)
        filter_menu.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # 主表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("提醒类型", "会员编号", "会员姓名", "手机号", "提醒内容", "紧急程度", "状态")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        col_widths = [100, 120, 80, 120, 350, 120, 80]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部统计
        self.status_label = ttk.Label(self, text="共 0 条提醒",
                                      font=("微软雅黑", 9), foreground="#999999")
        self.status_label.pack(anchor=tk.W, padx=15, pady=5)

        self.rows = []
        self.load_alerts()

    def load_alerts(self):
        """加载提醒"""
        try:
            self.rows = self.biz.generate_alerts()
        except Exception:
            self.rows = []

        # 如果有已保存的提醒数据
        try:
            saved = self.biz.get_all_alerts()
            for r in saved:
                self.rows.append({
                    "提醒类型": r.get("提醒类型", ""),
                    "会员编号": r.get("会员编号", ""),
                    "会员姓名": r.get("会员姓名", ""),
                    "手机号": r.get("手机号", ""),
                    "提醒内容": r.get("提醒内容", ""),
                    "紧急程度": r.get("紧急程度", "关注(30天内)"),
                    "状态": "未处理",
                })
        except Exception:
            pass

        self._apply_filter()

    def _apply_filter(self):
        """应用筛选"""
        filter_val = self.filter_var.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        count = 0
        for r in self.rows:
            if filter_val == "全部" or r.get("紧急程度") == filter_val:
                self.tree.insert("", tk.END, values=(
                    r.get("提醒类型", ""),
                    r.get("会员编号", ""),
                    r.get("会员姓名", ""),
                    r.get("手机号", ""),
                    r.get("提醒内容", ""),
                    r.get("紧急程度", ""),
                    r.get("状态", "未处理"),
                ))
                count += 1

        self.status_label.config(text=f"共 {count} 条提醒（{filter_val}）")
