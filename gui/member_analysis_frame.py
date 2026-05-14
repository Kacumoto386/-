# -*- coding: utf-8 -*-
"""
会员画像与分析看板 — GUI
V2.6.0
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.base_frame import BaseDataFrame
from core.member_analysis import MemberAnalysisEngine


class MemberAnalysisFrame(ttk.Frame):
    """会员分析/画像界面"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.engine = MemberAnalysisEngine(biz)
        self._current_member_id = None
        self._profile = None
        self._build_ui()

    def _build_ui(self):
        # ── 顶部搜索区 ──
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="会员编号:").pack(side="left")
        self._entry_id = ttk.Entry(top, width=15)
        self._entry_id.pack(side="left", padx=5)
        ttk.Label(top, text="姓名:").pack(side="left", padx=(10, 0))
        self._entry_name = ttk.Entry(top, width=12)
        self._entry_name.pack(side="left", padx=5)
        ttk.Button(top, text="查询", command=self._search).pack(side="left", padx=10)

        self._member_list = ttk.Combobox(top, width=20, state="readonly")
        self._member_list.pack(side="left", padx=10)
        ttk.Button(top, text="查看画像", command=self._load_from_combo).pack(side="left")

        # ── 会员选择器提示 ──
        ttk.Label(top, text="(或从下拉列表选择)").pack(side="left", padx=5)

        # ── 主内容区（使用 Notebook 分页） ──
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._frame_basic = ttk.Frame(self._notebook)
        self._frame_attendance = ttk.Frame(self._notebook)
        self._frame_churn = ttk.Frame(self._notebook)
        self._frame_detail = ttk.Frame(self._notebook)

        self._notebook.add(self._frame_basic, text="基本信息")
        self._notebook.add(self._frame_attendance, text="出勤分析")
        self._notebook.add(self._frame_churn, text="流失评估")
        self._notebook.add(self._frame_detail, text="课程偏好")

        self._build_basic_tab()
        self._build_attendance_tab()
        self._build_churn_tab()
        self._build_detail_tab()

        # ── 加载会员列表 ──
        self._load_member_list()

        # ── 初始占位 ──
        self._show_placeholder()

    def _build_basic_tab(self):
        f = self._frame_basic
        txt = tk.Text(f, font=("微软雅黑", 10), wrap="word", state="disabled",
                      relief="flat", bg="#fafafa", padx=12, pady=8)
        txt.pack(fill="both", expand=True)
        self._txt_basic = txt

    def _build_attendance_tab(self):
        f = self._frame_attendance
        txt = tk.Text(f, font=("微软雅黑", 10), wrap="word", state="disabled",
                      relief="flat", bg="#fafafa", padx=12, pady=8)
        txt.pack(fill="both", expand=True)
        self._txt_attendance = txt

    def _build_churn_tab(self):
        f = self._frame_churn
        txt = tk.Text(f, font=("微软雅黑", 10), wrap="word", state="disabled",
                      relief="flat", bg="#fafafa", padx=12, pady=8)
        txt.pack(fill="both", expand=True)
        self._txt_churn = txt

    def _build_detail_tab(self):
        f = self._frame_detail
        txt = tk.Text(f, font=("微软雅黑", 10), wrap="word", state="disabled",
                      relief="flat", bg="#fafafa", padx=12, pady=8)
        txt.pack(fill="both", expand=True)
        self._txt_detail = txt

    def _load_member_list(self):
        """加载会员列表到下拉框"""
        members = self.biz.get_all_members()
        items = []
        for m in members:
            mid = m.get("会员编号", "")
            name = m.get("姓名", "")
            if mid:
                items.append(f"{mid} - {name}")
        self._member_list["values"] = items
        if items:
            self._member_list.current(0)

    def _search(self):
        """按编号或姓名搜索"""
        mid = self._entry_id.get().strip()
        name = self._entry_name.get().strip()

        members = self.biz.get_all_members()
        target = None

        if mid:
            for m in members:
                if m.get("会员编号") == mid:
                    target = m
                    break
        elif name:
            for m in members:
                if name in (m.get("姓名", "") or ""):
                    target = m
                    break
        else:
            messagebox.showinfo("提示", "请输入会员编号或姓名")
            return

        if target:
            self._current_member_id = target["会员编号"]
            self._load_member(target)
        else:
            messagebox.showwarning("未找到", "未找到匹配的会员")

    def _load_from_combo(self):
        val = self._member_list.get()
        if not val or "-" not in val:
            return
        mid = val.split(" - ")[0].strip()
        members = self.biz.get_all_members()
        for m in members:
            if m.get("会员编号") == mid:
                self._current_member_id = mid
                self._entry_id.delete(0, tk.END)
                self._entry_id.insert(0, mid)
                self._load_member(m)
                return

    def _load_member(self, member):
        """加载会员数据到各Tab"""
        mid = member["会员编号"]
        self._profile = self.engine.get_member_profile(mid)

        self._render_basic(member, self._profile)
        self._render_attendance(self._profile)
        self._render_churn(self._profile)
        self._render_detail(self._profile)

    def _render_basic(self, member, profile):
        txt = self._txt_basic
        txt.configure(state="normal")
        txt.delete("1.0", tk.END)

        basic = profile["basic"]
        lines = [
            ("会员编号", basic.get("会员编号", "")),
            ("姓名", basic.get("姓名", "")),
            ("性别", basic.get("性别", "")),
            ("手机号", basic.get("手机号", "")),
            ("会员等级", basic.get("会员等级", "")),
            ("会员状态", basic.get("会员状态", "")),
            ("入会日期", basic.get("入会日期", "")),
            ("会员到期日", basic.get("会员到期日", "")),
            ("介绍人", basic.get("介绍人", "") or "无"),
        ]
        for k, v in lines:
            txt.insert("end", f"{k}: {v}\n")

        txt.insert("end", "\n— 消费概况 —\n")
        fin = profile["finance"]
        txt.insert("end", f"总消费金额: ¥{fin.get('总消费金额', 0):.2f}\n")
        txt.insert("end", f"总购课时: {fin.get('总购课时', 0)} 节\n")
        txt.insert("end", f"已消耗课时: {fin.get('已消耗课时', 0)} 节\n")
        txt.insert("end", f"剩余课时: {fin.get('剩余课时', 0)} 节\n")

        txt.configure(state="disabled")

    def _render_attendance(self, profile):
        txt = self._txt_attendance
        txt.configure(state="normal")
        txt.delete("1.0", tk.END)

        att = profile["attendance"]
        txt.insert("end", f"总上课次数: {att.get('总上课次数', 0)} 次\n")
        txt.insert("end", f"月均上课: {att.get('月均上课', 0)} 次\n")
        txt.insert("end", f"周均上课: {att.get('周均上课', 0)} 次\n")
        txt.insert("end", f"最近上课: {att.get('最近上课', '无')}\n")
        txt.insert("end", f"连续未上课: {att.get('连续未上课天数', 0)} 天\n")

        # 上课趋势
        trend = profile.get("class_trend", [])
        txt.insert("end", f"\n— 近90天上课趋势 ({len(trend)}天有课) —\n")
        for t in trend[-14:]:  # 最近14天
            bar = "█" * min(t["count"], 20)
            txt.insert("end", f"  {t['date']}: {bar} {t['count']}次\n")

        txt.configure(state="disabled")

    def _render_churn(self, profile):
        txt = self._txt_churn
        txt.configure(state="normal")
        txt.delete("1.0", tk.END)

        risk = profile["churn_risk"]
        level = risk.get("level", "normal")
        labels = {"normal": "🟢 正常", "low": "🟡 低风险", "medium": "🟠 中风险", "high": "🔴 高风险"}
        txt.insert("end", f"流失风险等级: {labels.get(level, level)}\n", "bold")
        txt.insert("end", f"评估依据: {risk.get('reason', '')}\n")
        txt.insert("end", f"连续未上课天数: {risk.get('连续未上课天数', 0)} 天\n")

        tags = risk.get("tags", [])
        if tags:
            txt.insert("end", f"\n⚠️ 叠加标记:\n")
            for tag in tags:
                txt.insert("end", f"  • {tag}\n")

        # 建议
        txt.insert("end", "\n— 建议 —\n")
        if level == "high":
            txt.insert("end", "建议立即电话回访，了解会员近况\n可安排免费体验课或优惠活动激活")
        elif level == "medium":
            txt.insert("end", "建议发送关怀消息或优惠提醒\n推荐新的课程活动增加到店频率")
        elif level == "low":
            txt.insert("end", "可发送提醒消息保持互动\n观察后续到店情况")
        else:
            txt.insert("end", "会员状态良好，继续保持")

        txt.tag_configure("bold", font=("微软雅黑", 10, "bold"))
        txt.configure(state="disabled")

    def _render_detail(self, profile):
        txt = self._txt_detail
        txt.configure(state="normal")
        txt.delete("1.0", tk.END)

        # 课程偏好
        pref = profile.get("course_preference", [])
        txt.insert("end", "— 课程偏好 —\n")
        if pref:
            for p in pref:
                bar = "█" * int(p["ratio"] / 5) if p["ratio"] > 0 else "▏"
                txt.insert("end", f"  {p['type']}: {bar} {p['ratio']}% ({p['count']}次)\n")
        else:
            txt.insert("end", "  （暂无上课记录）\n")

        # 热门时段
        peaks = self.engine.get_peak_hours(days=90)
        txt.insert("end", f"\n— 热门时段分布 —\n")
        if peaks:
            for h, c in peaks[:6]:
                bar = "█" * min(c * 2, 20)
                txt.insert("end", f"  {h}: {bar} {c}次\n")
        else:
            txt.insert("end", "  （暂无数据）\n")

        txt.configure(state="disabled")

    def _show_placeholder(self):
        """初始占位信息"""
        for txt_attr in ["_txt_basic", "_txt_attendance", "_txt_churn", "_txt_detail"]:
            txt = getattr(self, txt_attr, None)
            if txt:
                txt.configure(state="normal")
                txt.delete("1.0", tk.END)
                txt.insert("end", "请在顶部搜索或选择会员后查看画像")
                txt.configure(state="disabled")
