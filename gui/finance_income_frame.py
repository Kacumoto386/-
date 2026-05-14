# -*- coding: utf-8 -*-
"""
收入总账 — GUI
V2.11.0 - 强化日期筛选
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
from gui.base_frame import BaseDataFrame
from core.finance import FinanceManager


class FinanceIncomeFrame(BaseDataFrame):
    """收入总账界面"""

    def __init__(self, parent, biz):
        self.fm = FinanceManager(biz)
        super().__init__(parent, biz, "收入总账", "finance_income", [])
        self._build_custom_ui()

    def _build_custom_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # Top toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=8)

        ttk.Button(toolbar, text="🔄 同步数据", command=self._sync).pack(side="left", padx=2)

        ttk.Label(toolbar, text="  起始日期:").pack(side="left", padx=(15, 2))
        self._start_var = tk.StringVar(value="")
        self._start_entry = ttk.Entry(toolbar, textvariable=self._start_var, width=12)
        self._start_entry.pack(side="left")
        self._start_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Label(toolbar, text="至").pack(side="left", padx=3)
        self._end_var = tk.StringVar(value="")
        self._end_entry = ttk.Entry(toolbar, textvariable=self._end_var, width=12)
        self._end_entry.pack(side="left")
        self._end_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Button(toolbar, text="今日", command=self._set_today, width=4).pack(side="left", padx=2)
        ttk.Button(toolbar, text="筛选", command=self._load_data).pack(side="left", padx=5)

        self._stats_label = ttk.Label(toolbar, text="", font=("微软雅黑", 9))
        self._stats_label.pack(side="right", padx=10)

        # Table
        cols = ("财务编号", "日期", "收入类型", "分类", "金额", "关联编号")
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        widths = [120, 100, 90, 120, 90, 130]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="center")
        self._tree.column("金额", anchor="e")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._load_data()

    def _set_today(self):
        today = date.today().strftime("%Y-%m-%d")
        self._start_var.set(today)
        self._end_var.set(today)

    def _load_data(self):
        start_str = self._start_var.get().strip()
        end_str = self._end_var.get().strip()

        for item in self._tree.get_children():
            self._tree.delete(item)

        records = self.fm.get_income_records(start_date=start_str or None,
                                             end_date=end_str or None)
        total = 0
        for r in records:
            amt = float(r.get("金额", 0) or 0)
            total += amt
            self._tree.insert("", "end", values=(
                r.get("财务编号", ""),
                str(r.get("日期", ""))[:10],
                r.get("收入类型", ""),
                r.get("分类", ""),
                f"¥{amt:.2f}",
                r.get("关联编号", ""),
            ))

        self._stats_label.config(
            text=f"收入: ¥{total:.2f} | 共 {len(records)} 条"
        )

    def _sync(self):
        # 同步时根据日期范围决定年月
        start_str = self._start_var.get().strip()
        end_str = self._end_var.get().strip()
        if start_str:
            try:
                d = datetime.strptime(start_str, "%Y-%m-%d")
                year, month = d.year, d.month
            except ValueError:
                year, month = date.today().year, date.today().month
        else:
            year, month = date.today().year, date.today().month
        result = self.fm.sync_all_income(year, month)
        self._load_data()
        self.master.event_generate("<<FinanceUpdate>>")
