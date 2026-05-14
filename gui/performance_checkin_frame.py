# -*- coding: utf-8 -*-
"""
业绩统计模块 - 会员进场统计
V2.15.0
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.performance_sale_frame import BasePerformanceFrame


class PerformanceCheckinFrame(BasePerformanceFrame):
    """会员进场统计"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "🏃 会员进场")
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

        # 进场方式筛选
        ttk.Label(filter_frame, text="进场方式：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(15, 2))
        self.cat_var = tk.StringVar(value="全部")
        cat_menu = ttk.Combobox(filter_frame, textvariable=self.cat_var,
                                values=["全部", "次卡", "现金卡", "期限卡", "无卡进场"],
                                state="readonly", width=10, font=("微软雅黑", 9))
        cat_menu.pack(side=tk.LEFT, padx=2)
        cat_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        # 主区域：左右两列
        panes = ttk.Frame(main)
        panes.pack(fill=tk.BOTH, expand=True)

        # 左列：卡片指标 + 进场方式分布
        left_frame = ttk.Frame(panes)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 卡片指标
        card_frame = ttk.Frame(left_frame)
        card_frame.pack(fill=tk.X, pady=5)

        self.stats_labels = {}
        stat_items = [
            ("总进场人次", "0"), ("今日进场", "0"),
            ("日均进场", "0"), ("单日最高", "0"),
        ]

        for i, (label, default) in enumerate(stat_items):
            row, col = divmod(i, 2)
            card_w, card_v = self._make_card(card_frame, label, default)
            card_w.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_labels[label] = card_v

        for i in range(2):
            card_frame.columnconfigure(i, weight=1)

        # 进场方式分布表格
        ttk.Label(left_frame, text="📊 进场方式分布", font=("微软雅黑", 11, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W, pady=(10, 5))

        cat_table_frame = ttk.Frame(left_frame)
        cat_table_frame.pack(fill=tk.BOTH, expand=True)

        cat_columns = ("核销方式", "人次", "占比")
        self.cat_tree = ttk.Treeview(cat_table_frame, columns=cat_columns,
                                     show="headings", height=5)
        for col, w in zip(cat_columns, [120, 100, 100]):
            self.cat_tree.heading(col, text=col)
            self.cat_tree.column(col, width=w, minwidth=60)

        cat_scroll = ttk.Scrollbar(cat_table_frame, orient=tk.VERTICAL,
                                   command=self.cat_tree.yview)
        self.cat_tree.configure(yscrollcommand=cat_scroll.set)
        self.cat_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 右列：时段分布 + 详细表格
        right_frame = ttk.Frame(panes)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 时段分布
        ttk.Label(right_frame, text="🕐 时段分布", font=("微软雅黑", 11, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W, pady=(0, 5))

        time_table_frame = ttk.Frame(right_frame)
        time_table_frame.pack(fill=tk.X)

        time_columns = ("时段", "人次", "占当日比例")
        self.time_tree = ttk.Treeview(time_table_frame, columns=time_columns,
                                      show="headings", height=4)
        for col, w in zip(time_columns, [100, 80, 100]):
            self.time_tree.heading(col, text=col)
            self.time_tree.column(col, width=w, minwidth=60)
        self.time_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 进场明细
        ttk.Label(right_frame, text="📋 进场明细（前20条）", font=("微软雅黑", 11, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W, pady=(10, 5))

        detail_table_frame = ttk.Frame(right_frame)
        detail_table_frame.pack(fill=tk.BOTH, expand=True)

        detail_columns = ("进场编号", "会员姓名", "核销方式", "关联卡号", "进场时间", "日期")
        self.detail_tree = ttk.Treeview(detail_table_frame, columns=detail_columns,
                                        show="headings", height=10)
        col_widths = [140, 80, 70, 120, 80, 90]
        for col, w in zip(detail_columns, col_widths):
            self.detail_tree.heading(col, text=col)
            self.detail_tree.column(col, width=w, minwidth=50)

        detail_scroll = ttk.Scrollbar(detail_table_frame, orient=tk.VERTICAL,
                                      command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=detail_scroll.set)
        self.detail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._calc_stats()

    def _make_card(self, parent, label, default):
        frame = tk.Frame(parent, bg="white", relief="solid", bd=1,
                         highlightbackground="#E0E0E0", highlightthickness=1)
        frame.pack_propagate(False)
        frame.configure(height=70)
        value = tk.Label(frame, text=default, font=("微软雅黑", 18, "bold"),
                         fg="#9B59B6", bg="white")
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

    def _get_hour_from_time(self, time_str):
        """从进场时间提取小时"""
        if not time_str:
            return None
        time_str = str(time_str).strip()
        if ":" in time_str:
            try:
                return int(time_str.split(":")[0])
            except ValueError:
                return None
        return None

    def _get_period_label(self, hour):
        """小时转时段标签"""
        if hour is None:
            return "未知"
        if hour < 8:
            return "早晨(06-08)"
        elif hour < 12:
            return "上午(08-12)"
        elif hour < 14:
            return "中午(12-14)"
        elif hour < 18:
            return "下午(14-18)"
        else:
            return "晚上(18-22)"

    def _get_period_days(self, today, period):
        if period == "今日":
            return 1
        elif period == "本周":
            return 7
        elif period == "本月":
            import calendar
            return calendar.monthrange(today.year, today.month)[1]
        elif period == "本季度":
            q_month = ((today.month - 1) // 3) * 3 + 1
            import calendar
            if q_month == 12:
                return 92
            return (date(today.year, q_month + 3, 1) - date(today.year, q_month, 1)).days
        elif period == "本年":
            return 365
        return 0

    def _calc_stats(self):
        rows = self.biz.get_all_checkins() or []
        if not rows:
            return

        today = date.today()
        period = self.period_var.get()
        cat_filter = self.cat_var.get()

        # 筛选
        filtered = []
        for r in rows:
            d = r.get("进场日期") or r.get("日期")
            if not self._in_period(d, period, today):
                continue

            cat = str(r.get("核销方式", "未知")).strip()
            r["_cat_display"] = cat

            if cat_filter != "全部":
                # 模糊匹配
                if cat_filter not in cat:
                    continue

            filtered.append(r)

        if not filtered:
            default_values = {
                "总进场人次": "0", "今日进场": "0",
                "日均进场": "0", "单日最高": "0",
            }
            for k in self.stats_labels:
                self.stats_labels[k].config(text=default_values.get(k, "0"))
            for t in (self.cat_tree, self.time_tree, self.detail_tree):
                for item in t.get_children():
                    t.delete(item)
            return

        total = len(filtered)
        today_count = len([r for r in filtered
                          if r.get("进场日期") == today or r.get("日期") == today])

        days_range = self._get_period_days(today, period)
        daily_avg = total / days_range if days_range > 0 else total

        # 单日最高（按日期分组）
        day_counts = {}
        for r in filtered:
            d = r.get("进场日期") or r.get("日期")
            if hasattr(d, 'strftime'):
                d = d.strftime("%Y-%m-%d")
            day_counts[str(d)] = day_counts.get(str(d), 0) + 1
        max_day = max(day_counts.values()) if day_counts else 0

        self.stats_labels["总进场人次"].config(text=str(total))
        self.stats_labels["今日进场"].config(text=str(today_count))
        self.stats_labels["日均进场"].config(text=f"{daily_avg:.1f}")
        self.stats_labels["单日最高"].config(text=str(max_day))

        # 进场方式分布
        cat_stats = {}
        for r in filtered:
            cat = r.get("_cat_display", "未知")
            cat_stats[cat] = cat_stats.get(cat, 0) + 1

        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        for cat, cnt in sorted(cat_stats.items(), key=lambda x: -x[1]):
            pct = f"{cnt / total * 100:.1f}%" if total > 0 else "0%"
            self.cat_tree.insert("", tk.END, values=(cat, cnt, pct))

        # 时段分布
        time_stats = {}
        for r in filtered:
            hour = self._get_hour_from_time(r.get("进场时间", ""))
            label = self._get_period_label(hour)
            time_stats[label] = time_stats.get(label, 0) + 1

        for item in self.time_tree.get_children():
            self.time_tree.delete(item)

        period_labels = ["早晨(06-08)", "上午(08-12)", "中午(12-14)", "下午(14-18)", "晚上(18-22)"]
        for label in period_labels:
            cnt = time_stats.get(label, 0)
            # 以今日为基数算比例
            pct = f"{cnt / today_count * 100:.1f}%" if today_count > 0 else "0%"
            self.time_tree.insert("", tk.END, values=(label, cnt, pct))

        # 进场明细
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)

        for r in filtered[:20]:  # 最多前20条
            d = r.get("进场日期") or r.get("日期")
            if hasattr(d, 'strftime'):
                d = d.strftime("%Y-%m-%d")

            self.detail_tree.insert("", tk.END, values=(
                r.get("进场编号", ""),
                r.get("会员姓名", ""),
                r.get("_cat_display", ""),
                r.get("会籍卡编号", ""),
                r.get("进场时间", ""),
                str(d),
            ))

    def refresh(self):
        self._calc_stats()
