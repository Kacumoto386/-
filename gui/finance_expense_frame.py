# -*- coding: utf-8 -*-
"""
支出管理 — GUI
V2.11.0 - 强化日期筛选
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.base_frame import BaseDataFrame
from core.finance import FinanceManager


class FinanceExpenseFrame(BaseDataFrame):
    """支出管理界面"""

    def __init__(self, parent, biz):
        self.fm = FinanceManager(biz)
        super().__init__(parent, biz, "支出记录", "finance_expense", [])
        self._build_custom_ui()

    def _build_custom_ui(self):
        for w in self.winfo_children():
            w.destroy()

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=8)

        ttk.Button(toolbar, text="➕ 新增支出", command=self._add).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔄 刷新", command=self._load_data).pack(side="left", padx=2)

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

        cols = ("财务编号", "日期", "支出类别", "金额", "支付方式", "经办人")
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        widths = [120, 100, 100, 90, 90, 90]
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

        records = self.fm.get_expenses(start_date=start_str or None,
                                       end_date=end_str or None)
        total = 0
        for r in records:
            amt = float(r.get("金额", 0) or 0)
            total += amt
            self._tree.insert("", "end", values=(
                r.get("财务编号", ""),
                str(r.get("日期", ""))[:10],
                r.get("支出类别", ""),
                f"¥{amt:.2f}",
                r.get("支付方式", ""),
                r.get("经办人", ""),
            ))

        self._stats_label.config(
            text=f"支出: ¥{total:.2f} | 共 {len(records)} 条"
        )

    def _add(self):
        dlg = ExpenseEditDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.fm.add_expense(dlg.result)
            self._load_data()
            self.master.event_generate("<<FinanceUpdate>>")


class ExpenseEditDialog(tk.Toplevel):
    """新增支出弹窗"""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("新增支出")
        self.geometry("380x350")
        self.resizable(False, False)
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill="both", expand=True)

        fields = [
            ("日期", ttk.Entry, "2026-05-04"),
            ("支出类别", ttk.Combobox, ["房租", "水电", "工资", "设备", "装修", "营销", "办公", "其他"]),
            ("金额", ttk.Entry, ""),
            ("支付方式", ttk.Combobox, ["银行卡", "微信", "支付宝", "现金", "转账"]),
            ("经办人", ttk.Entry, ""),
            ("备注", ttk.Entry, ""),
        ]

        self._widgets = {}
        for i, (label, wtype, extra) in enumerate(fields):
            ttk.Label(f, text=label + ":").grid(row=i, column=0, sticky="w", pady=3, padx=(0, 5))
            if wtype == ttk.Combobox:
                w = ttk.Combobox(f, values=extra, state="readonly", width=25)
                if extra:
                    w.set(extra[0])
            else:
                w = ttk.Entry(f, width=28)
                if extra:
                    w.insert(0, extra)
            w.grid(row=i, column=1, sticky="w", pady=3)
            self._widgets[label] = w

        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="left", padx=10)

    def _save(self):
        data = {
            "日期": self._widgets["日期"].get().strip(),
            "支出类别": self._widgets["支出类别"].get(),
            "金额": 0,
            "支付方式": self._widgets["支付方式"].get(),
            "经办人": self._widgets["经办人"].get().strip(),
            "备注": self._widgets["备注"].get().strip(),
        }
        try:
            data["金额"] = float(self._widgets["金额"].get().strip())
        except ValueError:
            messagebox.showwarning("输入错误", "金额必须为数字")
            return
        if not data["支出类别"]:
            messagebox.showwarning("输入错误", "请选择支出类别")
            return
        if data["金额"] <= 0:
            messagebox.showwarning("输入错误", "金额必须大于0")
            return
        self.result = data
        self.destroy()
