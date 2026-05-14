# -*- coding: utf-8 -*-
"""
业绩统计模块 - 会籍卡业绩统计
V2.15.0
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.performance_sale_frame import BasePerformanceFrame


class PerformanceMembershipFrame(BasePerformanceFrame):
    """会籍卡业绩统计"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "🎫 会籍卡业绩")
        self.build_content()

    def build_content(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 筛选栏
        filter_frame = ttk.Frame(main)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="统计期间：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.period_var = tk.StringVar(value="本月")
        period_menu = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                   values=["今日", "本周", "本月", "本季度", "本年", "全部"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        period_menu.pack(side=tk.LEFT, padx=5)
        period_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        tk.Button(filter_frame, text="📊 开始统计", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self._calc_stats).pack(side=tk.LEFT, padx=5)

        # 卡类型筛选
        ttk.Label(filter_frame, text="卡类型：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(15, 2))
        self.type_var = tk.StringVar(value="全部")
        type_menu = ttk.Combobox(filter_frame, textvariable=self.type_var,
                                 values=["全部", "次卡", "期限卡", "现金卡"],
                                 state="readonly", width=10, font=("微软雅黑", 9))
        type_menu.pack(side=tk.LEFT, padx=2)
        type_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        # 卡片指标 - 按卡类型分组展示
        card_frame = ttk.Frame(main)
        card_frame.pack(fill=tk.X, pady=10)

        self.stats_labels = {}
        stat_items = [
            ("总售卡数", "0张"), ("总金额", "¥0"),
            ("次卡", "¥0 (0张)"), ("期限卡", "¥0 (0张)"),
            ("现金卡", "¥0 (0张)"), ("有效卡数", "0张 / 0张"),
        ]

        for i, (label, default) in enumerate(stat_items):
            row, col = divmod(i, 3)
            card_w, card_v = self._make_card(card_frame, label, default)
            card_w.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_labels[label] = card_v

        for i in range(3):
            card_frame.columnconfigure(i, weight=1)

        # 详细表格
        ttk.Label(main, text="📋 售卡明细", font=("微软雅黑", 11, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W, pady=(10, 5))

        table_frame = ttk.Frame(main)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("会籍卡编号", "会员姓名", "会员手机号", "卡类型", "卡名称",
                   "售价", "实收金额", "开卡日期", "有效期止", "状态")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        col_widths = [140, 80, 110, 60, 100, 70, 70, 90, 90, 60]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=50)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._calc_stats()

    def _make_card(self, parent, label, default):
        frame = tk.Frame(parent, bg="white", relief="solid", bd=1,
                         highlightbackground="#E0E0E0", highlightthickness=1)
        frame.pack_propagate(False)
        frame.configure(height=70)
        value = tk.Label(frame, text=default, font=("微软雅黑", 18, "bold"),
                         fg="#70AD47", bg="white")
        value.pack(pady=(8, 0))
        tk.Label(frame, text=label, font=("微软雅黑", 9),
                 fg="#666666", bg="white").pack()
        return frame, value

    def _in_period(self, dt, period, today):
        if not dt:
            return period == "全部"
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, "%Y-%m-%d").date()
            except ValueError:
                return period == "全部"
        if isinstance(dt, datetime):
            dt = dt.date()
        if period == "今日":
            return dt == today
        elif period == "本周":
            return dt.isocalendar()[1] == today.isocalendar()[1] and dt.year == today.year
        elif period == "本月":
            return dt.month == today.month and dt.year == today.year
        elif period == "本季度":
            q = (today.month - 1) // 3
            return (dt.month - 1) // 3 == q and dt.year == today.year
        elif period == "本年":
            return dt.year == today.year
        return True

    def _safe_float(self, val):
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _safe_str(self, val):
        if val is None:
            return ""
        if hasattr(val, 'strftime'):
            return val.strftime("%Y-%m-%d")
        return str(val).strip()

    def _map_card_type(self, raw_type):
        """将原始卡类型映射为展示分类"""
        raw = str(raw_type).strip()
        if raw == "次卡" or raw == "次卡":
            return "次卡"
        elif raw in ("期限卡", "不限次", "时长卡"):
            return "期限卡"
        elif raw in ("现金卡", "储值卡") or "现金" in raw or "充值" in raw:
            return "现金卡"
        return raw

    def _calc_stats(self):
        rows = self.biz.get_all_memberships() or []
        if not rows:
            return

        today = date.today()
        period = self.period_var.get()
        type_filter = self.type_var.get()

        # 筛选
        filtered = []
        for r in rows:
            d = r.get("开卡日期") or r.get("创建日期")
            if not self._in_period(d, period, today):
                continue

            ctype = self._map_card_type(r.get("卡类型", ""))
            r["_display_type"] = ctype

            if type_filter != "全部" and ctype != type_filter:
                continue

            filtered.append(r)

        if not filtered:
            zeros = {k: ("0张" if "卡" in k else "¥0 (0张)" if "(" in k else "¥0" if "额" in k or "金" in k else "0张 / 0张") for k in self.stats_labels}
            for k in self.stats_labels:
                self.stats_labels[k].config(text=zeros.get(k, "0"))
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        # 按卡类型分组统计
        type_stats = {}
        for r in filtered:
            ctype = r["_display_type"]
            if ctype not in type_stats:
                type_stats[ctype] = {"count": 0, "amount": 0}
            type_stats[ctype]["count"] += 1
            type_stats[ctype]["amount"] += self._safe_float(r.get("实收金额", 0))

        total_count = len(filtered)
        total_amount = sum(st["amount"] for st in type_stats.values())
        valid_count = len([r for r in filtered if r.get("状态") == "有效"])

        self.stats_labels["总售卡数"].config(text=f"{total_count}张")
        self.stats_labels["总金额"].config(text=f"¥{total_amount:,.0f}")

        # 各类型展示
        type_names = {"次卡": "次卡", "期限卡": "期限卡", "现金卡": "现金卡"}
        for tname, label_key in [("次卡", "次卡"), ("期限卡", "期限卡"), ("现金卡", "现金卡")]:
            st = type_stats.get(tname, {"count": 0, "amount": 0})
            if label_key in self.stats_labels:
                self.stats_labels[label_key].config(
                    text=f"¥{st['amount']:,.0f} ({st['count']}张)")

        self.stats_labels["有效卡数"].config(
            text=f"{valid_count}张 / {total_count}张")

        # 填表
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in filtered:
            sale_date = self._safe_str(r.get("开卡日期"))
            valid_to = self._safe_str(r.get("有效期止"))

            tags = ()
            status = r.get("状态", "")
            if status == "已过期":
                tags = ("expired",)
                self.tree.tag_configure("expired", foreground="#E74C3C")
            elif status == "已用完":
                tags = ("used",)
                self.tree.tag_configure("used", foreground="#95A5A6")
            elif status == "已退费":
                tags = ("refunded",)
                self.tree.tag_configure("refunded", foreground="#999999")

            self.tree.insert("", tk.END, values=(
                r.get("会籍卡编号", ""),
                r.get("会员姓名", ""),
                r.get("会员手机号", ""),
                r["_display_type"],
                r.get("卡名称", ""),
                f"¥{self._safe_float(r.get('售价', 0)):,.0f}",
                f"¥{self._safe_float(r.get('实收金额', 0)):,.0f}",
                sale_date,
                valid_to,
                status,
            ), tags=tags)

    def refresh(self):
        self._calc_stats()
