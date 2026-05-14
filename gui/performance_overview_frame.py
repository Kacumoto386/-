# -*- coding: utf-8 -*-
"""
业绩统计模块 - 业绩总览看板
V2.15.0
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PerformanceOverviewFrame(ttk.Frame):
    """业绩总览看板 - 展示4个核心业绩维度"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📊 业绩总览",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 时间筛选
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(filter_frame, text="统计期间：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.period_var = tk.StringVar(value="本月")
        period_menu = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                   values=["今日", "本周", "本月", "本季度", "本年", "全部"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        period_menu.pack(side=tk.LEFT, padx=5)
        period_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        tk.Button(filter_frame, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self._calc_stats).pack(side=tk.LEFT, padx=5)

        # 主区域：指标卡片
        self.cards_frame = ttk.Frame(self)
        self.cards_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        card_items = [
            ("💳 售课业绩", "sale", "#4472C4"),
            ("📦 课程包业绩", "package", "#ED7D31"),
            ("🎫 会籍卡业绩", "membership", "#70AD47"),
            ("🏃 会员进场", "checkin", "#9B59B6"),
        ]

        self.card_frames = {}
        self.card_values = {}

        for i, (title, key, color) in enumerate(card_items):
            frame = tk.Frame(self.cards_frame, bg="white", relief="solid", bd=1,
                             highlightbackground="#E0E0E0", highlightthickness=1)
            frame.pack_propagate(False)
            frame.configure(height=140)

            # 标题
            header_lb = tk.Label(frame, text=title, font=("微软雅黑", 10, "bold"),
                                 fg=color, bg="white")
            header_lb.pack(anchor=tk.W, padx=12, pady=(8, 2))

            # 金额
            amount_lb = tk.Label(frame, text="¥0", font=("微软雅黑", 22, "bold"),
                                 fg="#333333", bg="white")
            amount_lb.pack(anchor=tk.W, padx=12)

            # 副指标
            sub_lb = tk.Label(frame, text="", font=("微软雅黑", 9),
                              fg="#999999", bg="white")
            sub_lb.pack(anchor=tk.W, padx=12, pady=(2, 0))

            # 详细数据框
            detail_frame = tk.Frame(frame, bg="white")
            detail_frame.pack(fill=tk.X, padx=12, pady=(5, 0))

            detail_lb = tk.Label(detail_frame, text="", font=("微软雅黑", 9),
                                 fg="#666666", bg="white", justify=tk.LEFT)
            detail_lb.pack(anchor=tk.W)

            frame.grid(row=0, column=i, padx=6, pady=5, sticky="nsew")
            self.card_frames[key] = frame
            self.card_values[key] = {
                "amount": amount_lb,
                "sub": sub_lb,
                "detail": detail_lb,
            }

        for i in range(4):
            self.cards_frame.columnconfigure(i, weight=1)

        # 详细数据表格区
        detail_title = ttk.Frame(self)
        detail_title.pack(fill=tk.X, padx=15, pady=(15, 5))
        ttk.Label(detail_title, text="📋 本期业绩明细",
                  font=("微软雅黑", 12, "bold"), foreground="#2E75B6").pack(side=tk.LEFT)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("业绩类型", "金额/数量", "笔数/人次", "占比")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        col_widths = [120, 150, 120, 100]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部时间戳
        self.ts_label = tk.Label(self, text="", font=("微软雅黑", 8),
                                 fg="#CCCCCC", anchor=tk.E)
        self.ts_label.pack(fill=tk.X, padx=15, pady=5)

        self._calc_stats()

    def _in_period(self, dt, period, today):
        """判断日期是否在统计区间内"""
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

    def _calc_stats(self):
        """计算所有业绩指标"""
        today = date.today()
        period = self.period_var.get()

        # === 1. 售课业绩 ===
        sales = self.biz.get_all_sales() or []
        filtered_sales = [s for s in sales if self._in_period(s.get("售课日期"), period, today)]
        sale_amount = sum(float(s.get("实收金额", 0) or 0) for s in filtered_sales)
        sale_count = len(filtered_sales)
        sale_qty = sum(int(s.get("售卖课时", 0) or 0) for s in filtered_sales)

        # 到期售课统计
        expired_sales = [s for s in filtered_sales if self._is_expired(s)]
        expire_amount = sum(float(s.get("实收金额", 0) or 0) for s in expired_sales)

        # === 2. 课程包业绩 ===
        packages = self.biz.get_all_packages() or []
        filtered_pkgs = [p for p in packages if self._in_period(p.get("售出日期"), period, today)]
        # 课程包没有金额字段，统计数量和课时
        pkg_count = len(filtered_pkgs)
        pkg_lessons = sum(int(p.get("总课时", 0) or 0) for p in filtered_pkgs)
        pkg_remaining = sum(int(p.get("剩余课时", 0) or 0) for p in filtered_pkgs)

        # === 3. 会籍卡业绩 ===
        memberships = self.biz.get_all_memberships() or []
        filtered_mem = [m for m in memberships if self._in_period(m.get("出售日期"), period, today)]
        mem_amount = sum(float(m.get("实收金额", 0) or 0) for m in filtered_mem)
        mem_count = len(filtered_mem)

        # 按卡类型分类
        mem_type_stats = {}
        for m in filtered_mem:
            ctype = m.get("卡类型", "未知")
            if ctype not in mem_type_stats:
                mem_type_stats[ctype] = {"count": 0, "amount": 0}
            mem_type_stats[ctype]["count"] += 1
            mem_type_stats[ctype]["amount"] += float(m.get("实收金额", 0) or 0)

        # === 4. 会员进场 ===
        checkins = self.biz.get_all_checkins() or []
        filtered_ck = [c for c in checkins if self._in_period(c.get("进场日期"), period, today)]
        ck_count = len(filtered_ck)

        # 按进场方式统计
        ck_cat_stats = {}
        for c in filtered_ck:
            cat = c.get("进场方式", "未知")
            ck_cat_stats[cat] = ck_cat_stats.get(cat, 0) + 1

        # --- 更新卡片 ---
        self.card_values["sale"]["amount"].config(text=f"¥{sale_amount:,.0f}")
        sale_sub = f"{sale_count}笔 | {sale_qty}课时"
        if expire_amount > 0:
            sale_sub += f" | ⚠到期¥{expire_amount:,.0f}"
        self.card_values["sale"]["sub"].config(text=sale_sub)
        self.card_values["sale"]["detail"].config(
            text=f"均价¥{sale_amount/sale_count:,.0f}" if sale_count else "")

        self.card_values["package"]["amount"].config(text=f"{pkg_count}个")
        self.card_values["package"]["sub"].config(text=f"总{pkg_lessons}课时 | 剩余{pkg_remaining}")
        self.card_values["package"]["detail"].config(text="")

        self.card_values["membership"]["amount"].config(text=f"¥{mem_amount:,.0f}")
        mem_sub_parts = [f"{mem_count}张"]
        for ctype, st in sorted(mem_type_stats.items(), key=lambda x: -x[1]["amount"]):
            mem_sub_parts.append(f"{ctype}¥{st['amount']:,.0f}")
        self.card_values["membership"]["sub"].config(text=" | ".join(mem_sub_parts))
        self.card_values["membership"]["detail"].config(text="")

        self.card_values["checkin"]["amount"].config(text=f"{ck_count}人次")
        # 日均
        if period != "全部":
            days_range = self._get_period_days(today, period)
            daily_avg = ck_count / days_range if days_range > 0 else ck_count
            ck_sub = f"日均{daily_avg:.1f}人次"
        else:
            ck_sub = ""
        # 进场方式分布
        cat_parts = [f"{k}{v}" for k, v in sorted(ck_cat_stats.items(), key=lambda x: -x[1])[:3]]
        self.card_values["checkin"]["sub"].config(text=ck_sub)
        self.card_values["checkin"]["detail"].config(
            text=" | ".join(cat_parts) if cat_parts else "")

        # --- 更新明细表格 ---
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_amount = sale_amount + mem_amount
        items = [
            ("💳 售课业绩", f"¥{sale_amount:,.0f}", f"{sale_count}笔",
             f"{sale_amount/total_amount*100:.1f}%" if total_amount > 0 else "0%"),
            ("📦 课程包业绩", f"{pkg_count}个 ({pkg_lessons}课时)", f"{pkg_count}笔",
             ""),
            ("🎫 会籍卡业绩", f"¥{mem_amount:,.0f}", f"{mem_count}张",
             f"{mem_amount/total_amount*100:.1f}%" if total_amount > 0 else "0%"),
            ("🏃 会员进场", f"{ck_count}人次", f"{ck_count}次",
             ""),
        ]

        for vals in items:
            self.tree.insert("", tk.END, values=vals)

        # 合计行
        self.tree.insert("", tk.END, values=(
            "📊 合计", f"¥{total_amount:,.0f}",
            f"{(sale_count + pkg_count + mem_count)}笔",
            "100%"
        ))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ts_label.config(text=f"更新于 {now} | 统计期间: {period}")

    def _is_expired(self, sale):
        """判断售课是否到期"""
        exp = sale.get("有效期截止日")
        if not exp:
            return False
        if isinstance(exp, str):
            try:
                exp = datetime.strptime(exp, "%Y-%m-%d").date()
            except ValueError:
                return False
        if isinstance(exp, datetime):
            exp = exp.date()
        if hasattr(exp, 'toordinal'):
            return exp < date.today()
        return False

    def _get_period_days(self, today, period):
        """获取统计区间的天数"""
        if period == "今日":
            return 1
        elif period == "本周":
            return 7
        elif period == "本月":
            import calendar
            return calendar.monthrange(today.year, today.month)[1]
        elif period == "本季度":
            q_month = ((today.month - 1) // 3) * 3 + 1
            if q_month == 1:
                return 90
            elif q_month == 4:
                return 91
            elif q_month == 7:
                return 92
            else:
                return 92
        elif period == "本年":
            return 365
        return 0

    def refresh(self):
        self._calc_stats()
