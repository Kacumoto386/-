# -*- coding: utf-8 -*-
"""
财务报表 — GUI
V2.11.0 - 强化日期筛选
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
from gui.base_frame import BaseDataFrame
from core.finance import FinanceManager, INCOME_HEADERS, EXPENSE_HEADERS


class FinanceReportFrame(BaseDataFrame):
    """财务报表界面"""

    def __init__(self, parent, biz):
        self.fm = FinanceManager(biz)
        super().__init__(parent, biz, "财务报表", "finance_report", [])
        self._build_custom_ui()

    def _build_custom_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # ── 筛选区 ──
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=8)

        ttk.Button(toolbar, text="🔄 刷新", command=self._load_report).pack(side="left", padx=2)

        # 月报/年报/自定义 切换
        self._mode = tk.StringVar(value="month")
        ttk.Radiobutton(toolbar, text="月报", variable=self._mode, value="month",
                        command=self._on_mode_change).pack(side="left", padx=(15, 2))
        ttk.Radiobutton(toolbar, text="年报", variable=self._mode, value="year",
                        command=self._on_mode_change).pack(side="left", padx=2)
        ttk.Radiobutton(toolbar, text="自定义", variable=self._mode, value="custom",
                        command=self._on_mode_change).pack(side="left", padx=2)

        self._month_selector = ttk.Frame(toolbar)

        ttk.Label(self._month_selector, text="年份:").pack(side="left")
        self._year_var = tk.StringVar(value=str(date.today().year))
        ttk.Combobox(self._month_selector, textvariable=self._year_var,
                     values=[str(y) for y in range(2024, 2030)],
                     width=6, state="readonly").pack(side="left")
        ttk.Label(self._month_selector, text="月份:").pack(side="left", padx=(5, 2))
        self._month_var = tk.StringVar(value=str(date.today().month))
        ttk.Combobox(self._month_selector, textvariable=self._month_var,
                     values=[str(i) for i in range(1, 13)],
                     width=4, state="readonly").pack(side="left")
        self._month_selector.pack(side="left", padx=10)

        # 自定义日期范围（默认隐藏，月报/年报时显示）
        self._date_range = ttk.Frame(toolbar)
        ttk.Label(self._date_range, text="起始日期:").pack(side="left")
        self._start_var = tk.StringVar(value="")
        self._start_entry = ttk.Entry(self._date_range, textvariable=self._start_var, width=11)
        self._start_entry.pack(side="left", padx=2)
        self._start_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Label(self._date_range, text="至").pack(side="left")
        self._end_var = tk.StringVar(value="")
        self._end_entry = ttk.Entry(self._date_range, textvariable=self._end_var, width=11)
        self._end_entry.pack(side="left", padx=2)
        self._end_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Button(toolbar, text="筛选", command=self._load_report).pack(side="left", padx=5)

        # ── 摘要卡片区 ──
        card_frame = ttk.Frame(self)
        card_frame.pack(fill="x", padx=10, pady=5)

        self._cards = {}
        for label in ["总收入", "总支出", "利润", "利润率"]:
            c = ttk.LabelFrame(card_frame, text=label, width=160, height=60)
            c.pack_propagate(False)
            c.pack(side="left", padx=5)
            val = ttk.Label(c, text="--", font=("微软雅黑", 14, "bold"))
            val.pack(expand=True)
            self._cards[label] = val

        # ── 详细报表 ──
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Tab 1: 收入明细
        income_tab = ttk.Frame(notebook)
        notebook.add(income_tab, text="收入明细")
        self._income_tree = ttk.Treeview(income_tab, columns=("收入类型", "笔数", "金额"),
                                         show="headings", height=6)
        for col in ["收入类型", "笔数", "金额"]:
            self._income_tree.heading(col, text=col)
            self._income_tree.column(col, width=150, anchor="center")
        self._income_tree.column("金额", anchor="e")
        self._income_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 2: 支出明细
        expense_tab = ttk.Frame(notebook)
        notebook.add(expense_tab, text="支出明细")
        self._expense_tree = ttk.Treeview(expense_tab, columns=("支出类别", "笔数", "金额"),
                                          show="headings", height=6)
        for col in ["支出类别", "笔数", "金额"]:
            self._expense_tree.heading(col, text=col)
            self._expense_tree.column(col, width=150, anchor="center")
        self._expense_tree.column("金额", anchor="e")
        self._expense_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 3: 明细列表
        detail_tab = ttk.Frame(notebook)
        notebook.add(detail_tab, text="明细列表")
        self._detail_tree = ttk.Treeview(detail_tab,
                                         columns=("日期", "类型", "类别", "金额", "来源"),
                                         show="headings", height=12)
        for col in ["日期", "类型", "类别", "金额", "来源"]:
            self._detail_tree.heading(col, text=col)
            self._detail_tree.column(col, width=140, anchor="center")
        self._detail_tree.column("金额", anchor="e")
        self._detail_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # 初始默认月报
        self._on_mode_change()
        self._load_report()

    def _on_mode_change(self):
        """切换月报/年报/自定义"""
        mode = self._mode.get()
        # 月报/年报模式：隐藏日期范围，显示年月选择器
        if mode == "month":
            self._date_range.pack_forget()
            self._month_selector.pack(side="left", padx=10)
        elif mode == "year":
            self._date_range.pack_forget()
            self._month_selector.pack(side="left", padx=10)
        else:
            # 自定义模式：隐藏年月选择器，显示日期范围
            self._month_selector.pack_forget()
            self._date_range.pack(side="left", padx=5)

    def _get_date_range(self):
        """根据当前模式获取起止日期"""
        mode = self._mode.get()
        if mode == "month":
            y = int(self._year_var.get())
            m = int(self._month_var.get())
            start = f"{y:04d}-{m:02d}-01"
            if m == 12:
                end = f"{y+1:04d}-01-01"
            else:
                end = f"{y:04d}-{m+1:02d}-01"
            return start, end
        elif mode == "year":
            y = int(self._year_var.get())
            return f"{y:04d}-01-01", f"{y+1:04d}-01-01"
        else:
            return (self._start_var.get().strip() or None,
                    self._end_var.get().strip() or None)

    def _load_report(self):
        start_str, end_str = self._get_date_range()
        if not start_str or not end_str:
            self._update_cards({"total_income": 0, "total_expense": 0, "profit": 0, "profit_rate": 0})
            return

        income_records = self.fm.get_income_records(start_date=start_str, end_date=end_str)
        expense_records = self.fm.get_expenses(start_date=start_str, end_date=end_str)

        total_income = sum(float(r.get("金额", 0) or 0) for r in income_records)
        total_expense = sum(float(e.get("金额", 0) or 0) for e in expense_records)
        profit = total_income - total_expense
        profit_rate = round(profit / total_income * 100, 1) if total_income else 0

        # 更新卡片
        self._cards["总收入"].config(text=f"¥{total_income:.2f}")
        self._cards["总支出"].config(text=f"¥{total_expense:.2f}")
        self._cards["利润"].config(text=f"¥{profit:.2f}")
        color = "#2e7d32" if profit >= 0 else "#c62828"
        self._cards["利润率"].config(text=f"{profit_rate:.1f}%", foreground=color)

        # 收入明细 Tab
        for item in self._income_tree.get_children():
            self._income_tree.delete(item)
        income_by_type = {}
        for r in income_records:
            typ = r.get("收入类型", "其他")
            amt = float(r.get("金额", 0) or 0)
            income_by_type[typ] = income_by_type.get(typ, 0) + amt
        for typ, amt in sorted(income_by_type.items(), key=lambda x: -x[1]):
            self._income_tree.insert("", "end", values=(typ, "--", f"¥{amt:.2f}"))

        # 支出明细 Tab
        for item in self._expense_tree.get_children():
            self._expense_tree.delete(item)
        expense_by_cat = {}
        for e in expense_records:
            cat = e.get("支出类别", "其他")
            amt = float(e.get("金额", 0) or 0)
            expense_by_cat[cat] = expense_by_cat.get(cat, 0) + amt
        for cat, amt in sorted(expense_by_cat.items(), key=lambda x: -x[1]):
            self._expense_tree.insert("", "end", values=(cat, "--", f"¥{amt:.2f}"))

        # 明细列表 Tab（合并收支按日期排序）
        for item in self._detail_tree.get_children():
            self._detail_tree.delete(item)
        details = []
        for r in income_records:
            details.append((str(r.get("日期", ""))[:10], "收入",
                           r.get("收入类型", ""), float(r.get("金额", 0) or 0),
                           r.get("关联编号", "")))
        for e in expense_records:
            details.append((str(e.get("日期", ""))[:10], "支出",
                           e.get("支出类别", ""), float(e.get("金额", 0) or 0),
                           e.get("支付方式", "")))
        details.sort(key=lambda x: x[0], reverse=True)
        for d in details:
            tag = "income" if d[1] == "收入" else "expense"
            self._detail_tree.insert("", "end", values=d, tags=(tag,))
        self._detail_tree.tag_configure("income", foreground="#2e7d32")
        self._detail_tree.tag_configure("expense", foreground="#c62828")
