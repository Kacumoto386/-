"""
教练排班日历 - 月历形式展示教练的约课数据
V2.15.8 - 紧凑月历 + 全屏预约详情
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import calendar
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ScheduleFrame(ttk.Frame):
    """教练排班日历 — 双栏布局：左侧月历 + 右侧扩展区 + 底部详情"""

    STATUS_COLORS = {
        "已预约": "#27AE60",
        "已签到": "#E67E22",
        "已完成": "#3498DB",
        "已取消": "#BDC3C7",
    }
    CARD_BG = {
        "已预约": "#E8F5E9",
        "已签到": "#FFF3E0",
        "已完成": "#E3F2FD",
        "已取消": "#F5F5F5",
    }

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.today = date.today()
        self.current_year = self.today.year
        self.current_month = self.today.month
        self._selected_day = None
        self._schedule_data = {}
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        """构建界面"""
        # ===== 顶部标题栏 =====
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(12, 4))

        ttk.Label(header, text="📅 教练排班",
                  font=("微软雅黑", 15, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 导航 + 教练筛选（右对齐）
        nav_frame = ttk.Frame(header)
        nav_frame.pack(side=tk.RIGHT)

        btn_s = {"font": ("微软雅黑", 10), "padx": 6, "pady": 0, "bd": 0, "cursor": "hand2"}

        tk.Button(nav_frame, text="◀", bg="#E8E8E8", fg="#555", **btn_s,
                  command=self._prev_month).pack(side=tk.LEFT)
        self.month_label = ttk.Label(nav_frame, text="", font=("微软雅黑", 12, "bold"),
                                     foreground="#333", width=12, anchor="center")
        self.month_label.pack(side=tk.LEFT, padx=4)
        tk.Button(nav_frame, text="▶", bg="#E8E8E8", fg="#555", **btn_s,
                  command=self._next_month).pack(side=tk.LEFT)

        tk.Button(nav_frame, text="今天", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=8, pady=0, bd=0, cursor="hand2",
                  command=self._go_today).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(nav_frame, text=" 教练：", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(8, 2))
        self.coach_var = tk.StringVar()
        self.coach_combo = ttk.Combobox(nav_frame, textvariable=self.coach_var,
                                        font=("微软雅黑", 10), width=10, state="readonly")
        self.coach_combo.pack(side=tk.LEFT)
        self.coach_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        tk.Button(nav_frame, text="🔄", font=("微软雅黑", 10),
                  bg="#E8E8E8", fg="#555", width=2, pady=0, bd=0, cursor="hand2",
                  command=self.refresh_data).pack(side=tk.LEFT, padx=2)

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=20, pady=4)

        # ===== 双栏主体（左右等宽） =====
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 8))
        body.columnconfigure(0, weight=1, uniform="half")
        body.columnconfigure(1, weight=1, uniform="half")
        body.rowconfigure(0, weight=1)

        # 左侧：月历 + 图例
        left_panel = ttk.Frame(body)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # 图例（精简）
        legend_frame = ttk.Frame(left_panel)
        legend_frame.pack(fill=tk.X, pady=(0, 4))
        legends = [
            ("#27AE60", "预约"), ("#E67E22", "签到"),
            ("#3498DB", "完成"),
        ]
        for color, label in legends:
            f = ttk.Frame(legend_frame)
            f.pack(side=tk.LEFT, padx=(0, 8))
            c = tk.Canvas(f, width=8, height=8, highlightthickness=0, bd=0)
            c.pack(side=tk.LEFT)
            c.create_oval(0, 0, 8, 8, fill=color, outline=color)
            ttk.Label(f, text=label, font=("微软雅黑", 8), foreground="#888").pack(side=tk.LEFT, padx=2)

        # 月历容器
        self.calendar_frame = ttk.Frame(left_panel)
        self.calendar_frame.pack(fill=tk.BOTH, anchor="nw")

        # 右侧扩展区
        right_panel = ttk.LabelFrame(body, text=" 统计摘要 ", padding=8)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.summary_var = tk.StringVar(value="选择教练和日期查看统计")
        ttk.Label(right_panel, textvariable=self.summary_var,
                  font=("微软雅黑", 9), foreground="#888").pack(anchor=tk.NW)

        # 统计卡片容器
        self.stats_container = ttk.Frame(right_panel)
        self.stats_container.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        # ===== 底部：日期详情（主区域） =====
        detail_frame = ttk.LabelFrame(self, text=" 预约详情 ", padding=4)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 12))

        self.detail_header_frame = ttk.Frame(detail_frame)
        self.detail_header_frame.pack(fill=tk.X)

        self.detail_var = tk.StringVar(value="点击日期查看预约详情")
        ttk.Label(self.detail_header_frame, textvariable=self.detail_var,
                  font=("微软雅黑", 9), foreground="#999").pack(anchor=tk.W)

        # 详情 Treeview 容器
        self.detail_tree_frame = ttk.Frame(detail_frame)
        self.detail_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
        self.detail_tree = None

    # ── 刷新 ──

    def refresh_data(self):
        """加载教练列表并刷新月历"""
        try:
            trainers = self.biz.get_all_trainers()
            coach_names = sorted(set(s.get("姓名", "") for s in trainers if s.get("姓名", "")))
            if not coach_names:
                coach_names = ["暂无教练"]
        except Exception:
            coach_names = ["暂无教练"]

        self.coach_combo["values"] = coach_names
        if not self.coach_var.get() or self.coach_var.get() not in coach_names:
            self.coach_var.set(coach_names[0] if coach_names else "")

        self._load_schedule_data()
        self._build_calendar()
        self._update_summary()

    def _load_schedule_data(self):
        coach = self.coach_var.get()
        if not coach or coach == "暂无教练":
            self._schedule_data = {}
            return
        try:
            self._schedule_data = self.biz.get_monthly_schedule(
                coach, self.current_year, self.current_month)
        except Exception:
            self._schedule_data = {}

    # ── 月历（紧凑型） ──

    def _build_calendar(self):
        """构建紧凑月历"""
        for w in self.calendar_frame.winfo_children():
            w.destroy()
        self._clear_detail()

        coach = self.coach_var.get()
        if not coach or coach == "暂无教练":
            ttk.Label(self.calendar_frame, text="暂无教练数据",
                      font=("微软雅黑", 10), foreground="#CCC").pack()
            return

        self.month_label.config(text=f"{self.current_year}年{self.current_month:02d}月")

        _, days = calendar.monthrange(self.current_year, self.current_month)
        first_wd = date(self.current_year, self.current_month, 1).weekday()

        # 星期行
        wds = ["一", "二", "三", "四", "五", "六", "日"]
        hdr = tk.Frame(self.calendar_frame, bg="#F5F7FA")
        hdr.pack(fill=tk.X)
        for col, wd in enumerate(wds):
            fg = "#C0392B" if col >= 5 else "#555"
            lbl = tk.Label(hdr, text=wd, font=("微软雅黑", 9),
                           fg=fg, bg="#F5F7FA", width=4, anchor="center")
            lbl.grid(row=0, column=col, padx=0, pady=0, sticky="nsew")
            hdr.columnconfigure(col, weight=1)

        # 日期行
        day_num = 1
        total = first_wd + days
        rows = (total + 6) // 7

        for row in range(rows):
            rframe = tk.Frame(self.calendar_frame)
            rframe.pack(fill=tk.X)
            for col in range(7):
                idx = row * 7 + col
                if idx < first_wd or day_num > days:
                    tk.Label(rframe, text="", width=4, bg="#FAFAFA"
                             ).grid(row=0, column=col, padx=0, pady=0)
                    rframe.columnconfigure(col, weight=1)
                    continue

                self._draw_cell(rframe, col, day_num)
                day_num += 1

    def _draw_cell(self, parent, col, day_num):
        """绘制单个紧凑日期格子"""
        is_today = (self.today == date(self.current_year, self.current_month, day_num))
        is_selected = (self._selected_day == day_num)
        is_weekend = col >= 5

        day_data = self._schedule_data.get(day_num, {"count": 0, "statuses": [], "bookings": []})
        has_booking = day_data["count"] > 0

        # 背景
        if is_selected:
            bg = "#FFFDE7"
        elif has_booking:
            prio = self._get_priority_status(day_data["statuses"])
            bg = self.CARD_BG.get(prio, "#FFFFFF")
        elif is_today:
            bg = "#E8F0FE"
        else:
            bg = "#FFFFFF"

        # 边框
        border_color = "#EEE"
        border_w = 0
        if has_booking:
            prio = self._get_priority_status(day_data["statuses"])
            border_color = self.STATUS_COLORS.get(prio, "#DDD")
            border_w = 1
        if is_selected:
            border_color = "#F9A825"
            border_w = 2

        cell = tk.Frame(parent, bg=bg,
                        highlightbackground=border_color,
                        highlightthickness=border_w,
                        highlightcolor=border_color,
                        relief="solid", bd=0)
        cell.grid(row=0, column=col, padx=1, pady=1, sticky="nsew")
        parent.columnconfigure(col, weight=1)
        cell.grid_propagate(False)

        # 日期数字
        fg = "#C0392B" if is_weekend else "#333"
        font = ("微软雅黑", 9, "bold" if is_today else "normal")
        lbl = tk.Label(cell, text=str(day_num), font=font,
                       fg=fg, bg=bg, padx=2, pady=0)
        lbl.pack(anchor="nw")

        # 今天指示
        if is_today:
            tk.Label(cell, text="·", font=("微软雅黑", 10, "bold"),
                     bg=bg, fg="#4472C4").pack(anchor="center", pady=0)

        # 有预约 → 课节数
        if has_booking:
            cnt = day_data["count"]
            tk.Label(cell, text=f"{cnt}节", font=("微软雅黑", 7),
                     fg="#999", bg=bg).pack(anchor="center", pady=(0, 1))

        # 点击
        for w in [cell, lbl]:
            w.bind("<Button-1>", lambda e, d=day_num: self._on_day_click(d))
            w.bind("<Enter>", lambda e: cell.configure(cursor="hand2"))
            w.bind("<Leave>", lambda e: cell.configure(cursor=""))

    def _get_priority_status(self, statuses):
        for s in ("已签到", "已预约", "已完成", "已取消"):
            if s in statuses:
                return s
        return "已预约"

    # ── 点击 + 详情 ──

    def _on_day_click(self, day):
        self._selected_day = day
        self._build_calendar()
        self._show_day_detail(day)
        self._update_summary()

    def _show_day_detail(self, day):
        """显示当日预约详情"""
        coach = self.coach_var.get()
        if not coach:
            return

        day_data = self._schedule_data.get(day, {"count": 0, "bookings": []})
        bookings = day_data["bookings"]
        td = date(self.current_year, self.current_month, day)

        self._clear_detail()

        wd = ["一", "二", "三", "四", "五", "六", "日"][td.weekday()]
        dlabel = f"{td.strftime('%Y年%m月%d日')} 周{wd}"

        if not bookings:
            self.detail_var.set(f"📋 {dlabel} · {coach} — 暂无预约")
            return

        total = len(bookings)
        sts = [b.get("预约状态", "") for b in bookings]
        cnt_b = sts.count("已预约")
        cnt_s = sts.count("已签到")
        cnt_d = sts.count("已完成")
        cnt_c = sts.count("已取消")
        parts = []
        if cnt_b: parts.append(f"🟢{cnt_b}节未签")
        if cnt_s: parts.append(f"🟡{cnt_s}节已签")
        if cnt_d: parts.append(f"🔵{cnt_d}节完成")
        if cnt_c: parts.append(f"⬜{cnt_c}节取消")
        summary = " | ".join(parts)

        self.detail_var.set(f"📋 {dlabel} · {coach} 共{total}节  {summary}")

        # Treeview 列表
        cols = ("时间", "会员", "课程", "状态", "手机")
        tree = ttk.Treeview(self.detail_tree_frame, columns=cols, show="headings",
                            height=8, selectmode="browse")
        tree.heading("时间", text="时间")
        tree.column("时间", width=65, anchor="center")
        tree.heading("会员", text="会员")
        tree.column("会员", width=90, anchor="center")
        tree.heading("课程", text="课程")
        tree.column("课程", width=160, anchor="center")
        tree.heading("状态", text="状态")
        tree.column("状态", width=80, anchor="center")
        tree.heading("手机", text="手机")
        tree.column("手机", width=110, anchor="center")

        vsb = ttk.Scrollbar(self.detail_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        indicators = {"已预约": "🟢", "已签到": "🟡", "已完成": "🔵", "已取消": "⬜"}
        for b in bookings:
            st = b.get("预约状态", "")
            ind = indicators.get(st, "⚪")
            tree.insert("", "end", values=(
                b.get("开始时间", ""),
                b.get("会员姓名", ""),
                b.get("课程名称", ""),
                f"{ind} {st}",
                b.get("会员手机号", ""),
            ))

        self.detail_tree = tree

    def _clear_detail(self):
        """彻底清除详情区"""
        self.detail_var.set("点击日期查看预约详情")
        # 销毁 detail_tree_frame 内的所有子控件（Treeview + Scrollbar）
        for w in self.detail_tree_frame.winfo_children():
            w.destroy()
        self.detail_tree = None

    # ── 右侧统计 ──

    def _update_summary(self):
        """更新右侧统计摘要"""
        coach = self.coach_var.get()
        if not coach or coach == "暂无教练":
            self.summary_var.set("请选择教练")
            for w in self.stats_container.winfo_children():
                w.destroy()
            return

        data = self._schedule_data
        if not data:
            self.summary_var.set(f"{coach} · 本月暂无排班数据")
            for w in self.stats_container.winfo_children():
                w.destroy()
            return

        # 汇总
        total_booked = sum(1 for d in data.values()
                           for s in d["statuses"] if s == "已预约")
        total_signed = sum(1 for d in data.values()
                           for s in d["statuses"] if s == "已签到")
        total_done = sum(1 for d in data.values()
                         for s in d["statuses"] if s == "已完成")
        total_all = total_booked + total_signed + total_done
        busy_days = sum(1 for d in data.values() if d["count"] > 0)

        self.summary_var.set(f"{coach} · {self.current_year}年{self.current_month}月")

        # 统计卡片
        for w in self.stats_container.winfo_children():
            w.destroy()

        cards = [
            ("📊", "总课节", f"{total_all}节", "#4472C4"),
            ("📅", "有课天数", f"{busy_days}天", "#27AE60"),
            ("🟢", "待签到", f"{total_booked}节", "#27AE60"),
            ("🟡", "已签到", f"{total_signed}节", "#E67E22"),
            ("🔵", "已完成", f"{total_done}节", "#3498DB"),
        ]

        card_frame = ttk.Frame(self.stats_container)
        card_frame.pack(fill=tk.X, pady=2)

        for i, (icon, label, value, color) in enumerate(cards):
            c = tk.Frame(card_frame, bg="#F8F9FA", relief="solid", bd=1,
                         highlightbackground="#E0E0E0", highlightthickness=0)
            c.pack(fill=tk.X, pady=2, padx=2)

            tk.Label(c, text=f"{icon} {label}", font=("微软雅黑", 8),
                     fg="#888", bg="#F8F9FA").pack(anchor="w", padx=6, pady=(3, 0))
            tk.Label(c, text=value, font=("微软雅黑", 12, "bold"),
                     fg=color, bg="#F8F9FA").pack(anchor="w", padx=6, pady=(0, 3))

    # ── 导航 ──

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._selected_day = None
        self._load_schedule_data()
        self._build_calendar()
        self._update_summary()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._selected_day = None
        self._load_schedule_data()
        self._build_calendar()
        self._update_summary()

    def _go_today(self):
        self.current_year = self.today.year
        self.current_month = self.today.month
        self._selected_day = self.today.day
        self._load_schedule_data()
        self._build_calendar()
        self._update_summary()
        self._show_day_detail(self.today.day)
