# -*- coding: utf-8 -*-
"""
流失预警看板 — GUI
V2.6.0
"""
import tkinter as tk
from tkinter import ttk
from gui.base_frame import BaseDataFrame
from core.member_analysis import MemberAnalysisEngine


class ChurnWarningFrame(ttk.Frame):
    """流失预警看板"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.engine = MemberAnalysisEngine(biz)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # ── 顶部统计区 ──
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        self._stat_high = ttk.Label(top, text="高风险: -", font=("微软雅黑", 11, "bold"), foreground="#d32f2f")
        self._stat_high.pack(side="left", padx=15)

        self._stat_medium = ttk.Label(top, text="中风险: -", font=("微软雅黑", 11, "bold"), foreground="#f57c00")
        self._stat_medium.pack(side="left", padx=15)

        self._stat_low = ttk.Label(top, text="低风险: -", font=("微软雅黑", 11, "bold"), foreground="#fbc02d")
        self._stat_low.pack(side="left", padx=15)

        self._stat_total = ttk.Label(top, text="总会员: -", font=("微软雅黑", 11))
        self._stat_total.pack(side="left", padx=15)

        ttk.Button(top, text="🔄 刷新", command=self._load_data).pack(side="right", padx=5)

        # ── 筛选区 ──
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Label(filter_frame, text="风险等级:").pack(side="left")
        self._level_filter = ttk.Combobox(
            filter_frame, values=["全部", "高风险", "中风险", "低风险"],
            width=12, state="readonly"
        )
        self._level_filter.current(0)
        self._level_filter.pack(side="left", padx=10)
        self._level_filter.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        ttk.Label(filter_frame, text="标签:").pack(side="left")
        self._tag_filter = ttk.Combobox(
            filter_frame, values=["全部", "课时不足", "低频到店", "即将到期"],
            width=12, state="readonly"
        )
        self._tag_filter.current(0)
        self._tag_filter.pack(side="left", padx=10)
        self._tag_filter.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # ── 表格区 ──
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("姓名", "会员编号", "会员等级", "风险等级", "连续未上课", "剩余课时", "标记")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=100, anchor="center")
        self._tree.column("姓名", width=80)
        self._tree.column("会员等级", width=80)
        self._tree.column("风险等级", width=80)
        self._tree.column("连续未上课", width=100)
        self._tree.column("剩余课时", width=80)
        self._tree.column("标记", width=160)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # ── 选择会员查看详情 ──
        ttk.Label(self, text="双击行可查看该会员详情（如果安装了会员分析模块）",
                  font=("微软雅黑", 9), foreground="gray").pack(pady=(0, 5))

    def _load_data(self):
        """加载流失预警数据"""
        self._all_warnings = self.engine.get_churn_warnings()
        self._apply_filter()

    def _apply_filter(self):
        """应用筛选"""
        level_map = {"全部": None, "高风险": "high", "中风险": "medium", "低风险": "low"}
        tag_map = {"全部": None, "课时不足": "课时不足", "低频到店": "低频到店", "即将到期": "即将到期"}

        level_filter = level_map.get(self._level_filter.get(), None)
        tag_filter = tag_map.get(self._tag_filter.get(), None)

        # 清除旧数据
        for item in self._tree.get_children():
            self._tree.delete(item)

        # 统计
        counts = {"high": 0, "medium": 0, "low": 0}
        filtered = []

        for w in self._all_warnings:
            if level_filter and w["level"] != level_filter:
                continue
            if tag_filter and tag_filter not in w.get("tags", []):
                continue
            filtered.append(w)
            counts[w["level"]] = counts.get(w["level"], 0) + 1

        # 插入数据
        for w in filtered:
            level_label = {"high": "🔴 高", "medium": "🟠 中", "low": "🟡 低"}.get(w["level"], w["level"])
            tags_str = ", ".join(w.get("tags", [])) if w.get("tags") else ""
            self._tree.insert("", "end", values=(
                w["姓名"],
                w["会员编号"],
                w["会员等级"],
                level_label,
                f"{w['连续未上课天数']}天",
                w["剩余课时"],
                tags_str,
            ))

        # 更新统计
        all_members = len(self.biz.get_all_members())
        self._stat_high.configure(text=f"🔴 高风险: {counts['high']}")
        self._stat_medium.configure(text=f"🟠 中风险: {counts['medium']}")
        self._stat_low.configure(text=f"🟡 低风险: {counts['low']}")
        self._stat_total.configure(text=f"总会员: {all_members}")
