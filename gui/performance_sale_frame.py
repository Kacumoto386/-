# -*- coding: utf-8 -*-
"""
业绩统计模块 - 售课业绩（原售课统计增强版）
V2.15.0 - 新增到期时间展示
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BasePerformanceFrame(ttk.Frame):
    """业绩统计基类"""

    def __init__(self, parent, biz, title):
        super().__init__(parent)
        self.biz = biz
        self.title = title
        self.build_header()

    def build_header(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text=self.title,
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        tk.Button(header, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.refresh).pack(side=tk.RIGHT, padx=5)

    def refresh(self):
        pass


class PerformanceSaleFrame(BasePerformanceFrame):
    """售课业绩 - 增强版（含到期时间展示）"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "💳 售课业绩")
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

        # 到期状态筛选
        ttk.Label(filter_frame, text="到期状态：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(15, 2))
        self.expiry_var = tk.StringVar(value="全部")
        expiry_menu = ttk.Combobox(filter_frame, textvariable=self.expiry_var,
                                   values=["全部", "正常", "即将到期(<7天)", "已过期"],
                                   state="readonly", width=14, font=("微软雅黑", 9))
        expiry_menu.pack(side=tk.LEFT, padx=2)
        expiry_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        # 卡片指标区
        card_frame = ttk.Frame(main)
        card_frame.pack(fill=tk.X, pady=10)

        self.stats_labels = {}
        stat_items = [
            ("售课总额", "¥0"), ("售课课时", "0"),
            ("实收金额", "¥0"), ("售课笔数", "0"),
            ("均价", "¥0"), ("已到期金额", "¥0"),
        ]

        for i, (label, default) in enumerate(stat_items):
            row, col = divmod(i, 3)
            card_w, card_v = self._make_card(card_frame, label, default)
            card_w.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_labels[label] = card_v

        for i in range(3):
            card_frame.columnconfigure(i, weight=1)

        # 详细表格
        ttk.Label(main, text="📋 售课明细", font=("微软雅黑", 11, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W, pady=(10, 5))

        table_frame = ttk.Frame(main)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("售课编号", "售课日期", "会员姓名", "课程名称",
                   "售卖课时", "实收金额", "支付方式",
                   "有效期截止日", "剩余天数", "到期状态")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        col_widths = [140, 90, 80, 120, 70, 70, 70, 100, 70, 80]
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
                         fg="#4472C4", bg="white")
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

    def _get_expiry_status(self, expiry_date):
        """获取到期状态和剩余天数"""
        if not expiry_date:
            return "无期限", None, "#999999"
        if isinstance(expiry_date, str):
            try:
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            except ValueError:
                return "未知", None, "#999999"
        if isinstance(expiry_date, datetime):
            expiry_date = expiry_date.date()

        today = date.today()
        remaining = (expiry_date - today).days

        if remaining < 0:
            return "已过期", remaining, "#E74C3C"
        elif remaining <= 7:
            return "即将到期", remaining, "#E67E22"
        else:
            return "正常", remaining, "#27AE60"

    def _calc_stats(self):
        rows = self.biz.get_all_sales() or []
        if not rows:
            return

        today = date.today()
        period = self.period_var.get()
        expiry_filter = self.expiry_var.get()

        # 筛选 + 构建到期状态
        filtered = []
        for r in rows:
            sale_date = r.get("售课日期")
            if not self._in_period(sale_date, period, today):
                continue

            expiry = r.get("有效期截止日")
            status, remaining, _ = self._get_expiry_status(expiry)

            r["_expiry_status"] = status
            r["_remaining_days"] = remaining
            r["_expiry_date"] = expiry

            if expiry_filter == "已过期":
                if status != "已过期":
                    continue
            elif expiry_filter == "即将到期(<7天)":
                if status != "即将到期":
                    continue
            elif expiry_filter == "正常":
                if status not in ("正常", "无期限"):
                    continue

            filtered.append(r)

        if not filtered:
            for k in self.stats_labels:
                self.stats_labels[k].config(text="0" if k in ("售课课时", "售课笔数") else "¥0")
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        # 统计
        total_amount = sum(float(r.get("售价", 0) or 0) for r in filtered)
        total_qty = sum(int(r.get("售卖课时", 0) or 0) for r in filtered)
        total_received = sum(float(r.get("实收金额", 0) or 0) for r in filtered)
        count = len(filtered)
        avg_price = total_received / count if count > 0 else 0
        expired_amount = sum(
            float(r.get("实收金额", 0) or 0)
            for r in filtered if r.get("_expiry_status") == "已过期"
        )

        self.stats_labels["售课总额"].config(text=f"¥{total_amount:,.0f}")
        self.stats_labels["售课课时"].config(text=str(int(total_qty)))
        self.stats_labels["实收金额"].config(text=f"¥{total_received:,.0f}")
        self.stats_labels["售课笔数"].config(text=str(count))
        self.stats_labels["均价"].config(text=f"¥{avg_price:,.0f}")
        self.stats_labels["已到期金额"].config(text=f"¥{expired_amount:,.0f}")

        # 填表
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in filtered:
            expiry = r.get("_expiry_date", "")
            exp_str = ""
            if hasattr(expiry, 'strftime'):
                exp_str = expiry.strftime("%Y-%m-%d")
            elif expiry:
                exp_str = str(expiry)[:10]

            remaining = r.get("_remaining_days")
            rem_str = f"{remaining}天" if remaining is not None else "-"

            status = r.get("_expiry_status", "无期限")
            _, _, color = self._get_expiry_status(r.get("有效期截止日"))

            iid = self.tree.insert("", tk.END, values=(
                r.get("售课编号", ""),
                r.get("售课日期", ""),
                r.get("会员姓名", ""),
                r.get("课程名称", ""),
                int(r.get("售卖课时", 0) or 0),
                f"¥{float(r.get('实收金额', 0) or 0):,.0f}",
                r.get("支付方式", ""),
                exp_str,
                rem_str,
                status,
            ))
            if status == "已过期":
                self.tree.tag_configure("expired", foreground="#E74C3C")
                self.tree.item(iid, tags=("expired",))
            elif status == "即将到期":
                self.tree.tag_configure("soon", foreground="#E67E22")
                self.tree.item(iid, tags=("soon",))

    def refresh(self):
        self._calc_stats()
