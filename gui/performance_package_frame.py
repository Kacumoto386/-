# -*- coding: utf-8 -*-
"""
业绩统计模块 - 课程包业绩统计
V2.15.0
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime
import re
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gui.performance_sale_frame import BasePerformanceFrame


class PerformancePackageFrame(BasePerformanceFrame):
    """课程包业绩统计"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "📦 课程包业绩")
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

        # 查看状态筛选
        ttk.Label(filter_frame, text="状态：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(15, 2))
        self.status_var = tk.StringVar(value="全部")
        status_menu = ttk.Combobox(filter_frame, textvariable=self.status_var,
                                   values=["全部", "有效", "已用完", "已过期"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        status_menu.pack(side=tk.LEFT, padx=2)
        status_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        # 卡片指标
        card_frame = ttk.Frame(main)
        card_frame.pack(fill=tk.X, pady=10)

        self.stats_labels = {}
        stat_items = [
            ("课程包数量", "0"), ("总课时数", "0"),
            ("已消耗课时", "0"), ("剩余课时", "0"),
            ("消耗率", "0%"), ("活跃包数", "0"),
        ]

        for i, (label, default) in enumerate(stat_items):
            row, col = divmod(i, 3)
            card_w, card_v = self._make_card(card_frame, label, default)
            card_w.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_labels[label] = card_v

        for i in range(3):
            card_frame.columnconfigure(i, weight=1)

        # 详细表格
        ttk.Label(main, text="📋 课程包明细", font=("微软雅黑", 11, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W, pady=(10, 5))

        table_frame = ttk.Frame(main)
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.sort_col = None
        self.sort_reverse = False

        columns = ("课程包编号", "会员姓名", "课程名称", "总课时",
                   "已消耗", "剩余", "消耗率", "有效期起", "有效期止", "状态")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        col_widths = [140, 80, 130, 60, 60, 60, 60, 90, 90, 60]
        for i, col in enumerate(columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[i], minwidth=50)

        # 绑定表头点击排序（双重保障）
        self._bind_header_sort(columns)

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
                         fg="#ED7D31", bg="white")
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

    def _safe_int(self, val):
        try:
            return int(val) if val else 0
        except (ValueError, TypeError):
            return 0

    def _safe_date(self, val):
        if not val:
            return ""
        if hasattr(val, 'strftime'):
            return val.strftime("%Y-%m-%d")
        return str(val)[:10]

    def _calc_stats(self):
        rows = self.biz.get_all_packages() or []
        if not rows:
            return

        today = date.today()
        period = self.period_var.get()
        status_filter = self.status_var.get()

        # 筛选
        filtered = []
        for r in rows:
            # 尝试从多个日期字段匹配
            d = r.get("售出日期") or r.get("有效期起") or r.get("创建日期")
            if not self._in_period(d, period, today):
                continue

            pkg_status = r.get("状态", "有效")
            if status_filter == "有效" and pkg_status != "有效":
                continue
            elif status_filter == "已用完" and pkg_status != "已用完":
                continue
            elif status_filter == "已过期" and pkg_status != "已过期":
                continue

            filtered.append(r)

        if not filtered:
            for k in self.stats_labels:
                self.stats_labels[k].config(text="0" if k != "消耗率" else "0%")
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        # 统计
        total_count = len(filtered)
        total_lessons = sum(self._safe_int(r.get("总课时", 0)) for r in filtered)
        total_consumed = sum(self._safe_int(r.get("已消耗课时", 0)) for r in filtered)
        total_remaining = sum(self._safe_int(r.get("剩余课时", 0)) for r in filtered)
        active_count = len([r for r in filtered if r.get("状态") == "有效"])
        consume_rate = total_consumed / total_lessons * 100 if total_lessons > 0 else 0

        self.stats_labels["课程包数量"].config(text=str(total_count))
        self.stats_labels["总课时数"].config(text=str(int(total_lessons)))
        self.stats_labels["已消耗课时"].config(text=str(int(total_consumed)))
        self.stats_labels["剩余课时"].config(text=str(int(total_remaining)))
        self.stats_labels["消耗率"].config(text=f"{consume_rate:.1f}%")
        self.stats_labels["活跃包数"].config(text=str(active_count))

        # 填表
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in filtered:
            total = self._safe_int(r.get("总课时", 0))
            consumed = self._safe_int(r.get("已消耗课时", 0))
            remaining = self._safe_int(r.get("剩余课时", 0))
            rate = consumed / total * 100 if total > 0 else 0
            pkg_status = r.get("状态", "有效")

            vals = (
                r.get("课程包编号", ""),
                r.get("会员姓名", ""),
                r.get("课程名称", ""),
                total,
                consumed,
                remaining,
                f"{rate:.0f}%",
                self._safe_date(r.get("有效期起")),
                self._safe_date(r.get("有效期止")),
                pkg_status,
            )
            tags = ()
            if pkg_status == "已过期":
                tags = ("expired",)
                self.tree.tag_configure("expired", foreground="#E74C3C")
            elif pkg_status == "已用完":
                tags = ("used",)
                self.tree.tag_configure("used", foreground="#95A5A6")
            elif rate > 80:
                tags = ("high",)
                self.tree.tag_configure("high", foreground="#E67E22")

            self.tree.insert("", tk.END, values=vals, tags=tags)

    def _bind_header_sort(self, columns):
        """绑定表头点击排序（点击任意列位置触发，兼容所有主题）"""
        self._sort_columns = columns

        def on_click(event):
            col_id = self.tree.identify_column(event.x)
            if not col_id or col_id == "#0":
                return
            idx = int(col_id[1:]) - 1
            if 0 <= idx < len(self._sort_columns):
                self._toggle_sort(self._sort_columns[idx])

        self.tree.bind("<ButtonRelease-1>", on_click, "+")

    def _toggle_sort(self, col_name):
        """切换排序列和方向"""
        if self.sort_col == col_name:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col_name
            self.sort_reverse = False
        self._apply_sort()

    def _apply_sort(self):
        """当前数据按排序列排序后重新填入表格"""
        if not self.sort_col:
            return

        items = list(self.tree.get_children(""))
        if not items:
            return

        col_idx = ("课程包编号", "会员姓名", "课程名称", "总课时",
                   "已消耗", "剩余", "消耗率", "有效期起", "有效期止", "状态"
                   ).index(self.sort_col)

        def sort_key(item):
            val = self.tree.set(item, column=col_idx)
            val = str(val).strip()
            # 日期匹配
            if re.match(r'^\d{4}-\d{2}-\d{2}$', val):
                return (0, val)
            # 百分比
            if val.endswith('%'):
                try:
                    return (1, float(val[:-1]))
                except ValueError:
                    pass
            # 纯数字
            try:
                return (1, int(val))
            except ValueError:
                pass
            try:
                return (1, float(val))
            except ValueError:
                pass
            return (2, val)

        items.sort(key=sort_key, reverse=self.sort_reverse)

        for idx, item in enumerate(items):
            self.tree.move(item, "", idx)

    def refresh(self):
        self._calc_stats()
