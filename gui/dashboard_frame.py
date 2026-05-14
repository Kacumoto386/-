"""
首页看板 V3 - 数据看板升级 V2.8.5
支持：多图表类型（柱状图/折线图/饼图/雷达图）、自动轮播、大屏模式、排行榜可视化
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta
import math
import locale

from gui.dashboard_charts import (
    draw_line_chart, draw_bar_chart, draw_pie_chart,
    draw_radar_chart, draw_horizontal_bar
)


class DashboardFrame(ttk.Frame):
    """首页看板 V3 - 大屏仪表盘增强版"""

    # 指标卡片颜色方案
    CARD_COLORS = {
        "active_members":       {"fg": "#4472C4", "bg": "#EBF1FA", "border": "#4472C4"},
        "new_members":          {"fg": "#70AD47", "bg": "#EAF5DE", "border": "#70AD47"},
        "total_remaining":      {"fg": "#FFC000", "bg": "#FFF8E0", "border": "#FFC000"},
        "class_count":          {"fg": "#ED7D31", "bg": "#FDE9DB", "border": "#ED7D31"},
        "sale_amount":          {"fg": "#5B9BD5", "bg": "#E6EFF8", "border": "#5B9BD5"},
        "recharge_amount":      {"fg": "#9B59B6", "bg": "#F0E6F5", "border": "#9B59B6"},
        "product_sale_amount":  {"fg": "#1ABC9C", "bg": "#D4F5ED", "border": "#1ABC9C"},
        "expire_soon":          {"fg": "#E74C3C", "bg": "#FCE4E2", "border": "#E74C3C"},
    }

    def __init__(self, parent, biz, main_window=None, store_id=None):
        super().__init__(parent)
        self.biz = biz
        self._main_win = main_window
        self.store_id = store_id
        self.is_fullscreen = False
        self._auto_refresh_id = None
        self._carousel_id = None
        self._carousel_index = 0
        self._last_stats = {}
        self._charts_initialized = False
        self.build_ui()
        self.load_data()

    def build_ui(self):
        """构建界面"""
        self._build_checkin_panel()
        self._build_header()
        self._build_toolbar()
        self._build_metric_cards()
        self._build_chart_area()
        self._build_bottom_area()

    def _build_checkin_panel(self):
        """构建进场核销面板（嵌入看板顶部）"""
        from gui.checkin_frame import CheckinPanel
        self.checkin_panel = CheckinPanel(self, self.biz)
        self.checkin_panel.pack(fill=tk.X, padx=20, pady=(10, 2))

    def _build_header(self):
        """标题栏"""
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=20, pady=(15, 5))

        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        self.title_label = ttk.Label(header, text="🏋️ 经营仪表盘",
                                     font=("微软雅黑", 18, "bold"), foreground="#1F4E79")
        self.title_label.pack(side=tk.LEFT)

        self.time_label = ttk.Label(header, text=f"📅 {now}",
                                    font=("微软雅黑", 10), foreground="#999999")
        self.time_label.pack(side=tk.RIGHT)

        # 副标题 - 统计范围
        self.range_label = ttk.Label(header, text="本月统计",
                                     font=("微软雅黑", 9), foreground="#888888")
        self.range_label.pack(side=tk.LEFT, padx=(15, 0))

    def _build_toolbar(self):
        """操作栏"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=20, pady=(0, 8))

        # 大屏模式
        self.fs_btn = tk.Button(toolbar, text="🖥️ 大屏模式",
                                font=("微软雅黑", 9),
                                bg="#4472C4", fg="white",
                                padx=12, pady=3, bd=0, cursor="hand2",
                                command=self.toggle_fullscreen)
        self.fs_btn.pack(side=tk.LEFT, padx=2)

        # 自动刷新
        self.auto_refresh_var = tk.BooleanVar(value=False)
        tk.Checkbutton(toolbar, text="自动刷新(30秒)",
                       font=("微软雅黑", 9),
                       variable=self.auto_refresh_var,
                       command=self._toggle_auto_refresh).pack(side=tk.LEFT, padx=10)

        # 轮播切换
        self.carousel_var = tk.BooleanVar(value=False)
        tk.Checkbutton(toolbar, text="图表轮播(8秒)",
                       font=("微软雅黑", 9),
                       variable=self.carousel_var,
                       command=self._toggle_carousel).pack(side=tk.LEFT, padx=5)

        # 刷新按钮
        tk.Button(toolbar, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#E0E0E0", fg="#333333",
                  padx=12, pady=3, bd=0, cursor="hand2",
                  command=self.load_data).pack(side=tk.LEFT, padx=2)

        # 图表切换导航
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Label(toolbar, text="图表：", font=("微软雅黑", 9)).pack(side=tk.LEFT)

        self.chart_btns = {}
        chart_types = [
            ("trend", "📈 趋势"),
            ("pie",   "🥧 分布"),
            ("radar", "🕸️ 画像"),
            ("rank",  "🏆 排行"),
        ]
        for key, text in chart_types:
            btn = tk.Button(toolbar, text=text, font=("微软雅黑", 9),
                           bg="#F0F0F0", fg="#555555",
                           padx=8, pady=2, bd=0, cursor="hand2",
                           command=lambda k=key: self._switch_chart(k))
            btn.pack(side=tk.LEFT, padx=2)
            self.chart_btns[key] = btn

        self._highlight_chart_btn("trend")

    def _build_metric_cards(self):
        """核心指标卡（2行×4列，带渐变色背景）"""
        card_frame = ttk.Frame(self)
        card_frame.pack(fill=tk.X, padx=20, pady=3)

        self.metrics = {}
        metric_configs = [
            # 第一行：经营核心
            ("active_members", "👥 有效会员"),
            ("new_members", "📝 本月新增"),
            ("total_remaining", "📦 总剩余课时"),
            ("class_count", "🎓 本月上课"),
            # 第二行：财务
            ("sale_amount", "💰 本月售课额"),
            ("recharge_amount", "💳 本月充值额"),
            ("product_sale_amount", "🛒 本月零售额"),
            ("expire_soon", "⏰ 本月到期"),
        ]

        for i, (key, label) in enumerate(metric_configs):
            row, col = divmod(i, 4)
            card = self._create_metric_card(card_frame, label, key)
            card["frame"].grid(row=row, column=col, padx=5, pady=4, sticky="nsew")
            self.metrics[key] = card

        for i in range(4):
            card_frame.columnconfigure(i, weight=1)

    def _create_metric_card(self, parent, label, key):
        """创建指标卡片（圆角样式+渐变色感）"""
        scheme = self.CARD_COLORS.get(key, {"fg": "#4472C4", "bg": "#F0F0F0", "border": "#CCCCCC"})

        frame = tk.Frame(parent, bg="white", relief="solid", bd=0,
                         highlightbackground=scheme["border"], highlightthickness=1)
        frame.pack_propagate(False)
        frame.configure(height=88)

        # 顶部色条
        color_bar = tk.Frame(frame, bg=scheme["fg"], height=4)
        color_bar.pack(fill=tk.X, side=tk.TOP)
        color_bar.pack_propagate(False)

        value_label = tk.Label(frame, text="—", font=("微软雅黑", 24, "bold"),
                               fg=scheme["fg"], bg="white")
        value_label.pack(pady=(10, 0))

        name_label = tk.Label(frame, text=label, font=("微软雅黑", 9),
                              fg="#888888", bg="white")
        name_label.pack()

        return {"frame": frame, "value": value_label, "card_body": frame}

    def _build_chart_area(self):
        """图表区域（4种图表使用笔记本式切换）"""
        chart_frame = ttk.Frame(self)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # 使用 Notebook 风格的多页面切换（实际用 stack 实现）
        self.chart_stack = ttk.Frame(chart_frame)
        self.chart_stack.pack(fill=tk.BOTH, expand=True)

        # 图表1：趋势/柱状图
        self._build_trend_chart()
        # 图表2：饼图
        self._build_pie_chart()
        # 图表3：雷达图
        self._build_radar_chart()
        # 图表4：排行榜
        self._build_rank_chart()

        # 隐藏其他
        self._switch_chart("trend")

    def _build_trend_chart(self):
        """趋势图（折线+柱状组合）"""
        f = ttk.Frame(self.chart_stack)
        f.pack(fill=tk.BOTH, expand=True)

        # 上半：7天售课趋势（柱状图）
        top_frame = ttk.Frame(f)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 3))

        self.trend_header = ttk.Label(top_frame, text="📈 近7天售课趋势",
                                      font=("微软雅黑", 11, "bold"), foreground="#2E75B6")
        self.trend_header.pack(anchor=tk.W)

        self.chart_canvas_trend = tk.Canvas(top_frame, bg="#FAFAFA",
                                             highlightthickness=1,
                                             highlightbackground="#E0E0E0",
                                             height=160)
        self.chart_canvas_trend.pack(fill=tk.BOTH, expand=True)
        self.chart_canvas_trend.bind("<Configure>", lambda e: self._draw_chart_trend())

        # 下半：月度趋势（折线图）
        bottom_frame = ttk.Frame(f)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(3, 0))

        self.month_trend_header = ttk.Label(bottom_frame, text="📉 月度营收趋势",
                                            font=("微软雅黑", 11, "bold"), foreground="#2E75B6")
        self.month_trend_header.pack(anchor=tk.W)

        self.chart_canvas_month = tk.Canvas(bottom_frame, bg="#FAFAFA",
                                             highlightthickness=1,
                                             highlightbackground="#E0E0E0",
                                             height=140)
        self.chart_canvas_month.pack(fill=tk.BOTH, expand=True)
        self.chart_canvas_month.bind("<Configure>", lambda e: self._draw_chart_month())

        self._chart_widgets_trend = f

    def _build_pie_chart(self):
        """饼图（课程类型分布 + 商品类别分布）"""
        f = ttk.Frame(self.chart_stack)

        # 左：课程类型分布
        left_frame = ttk.Frame(f)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(left_frame, text="🥧 课程类型分布",
                  font=("微软雅黑", 11, "bold"), foreground="#2E75B6").pack(anchor=tk.W)

        self.pie_canvas_course = tk.Canvas(left_frame, bg="#FAFAFA",
                                            highlightthickness=1,
                                            highlightbackground="#E0E0E0",
                                            height=220)
        self.pie_canvas_course.pack(fill=tk.BOTH, expand=True)
        self.pie_canvas_course.bind("<Configure>", lambda e: self._draw_pie_course())

        # 右：商品类别分布
        right_frame = ttk.Frame(f)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(right_frame, text="🥧 商品类别销售占比",
                  font=("微软雅黑", 11, "bold"), foreground="#2E75B6").pack(anchor=tk.W)

        self.pie_canvas_product = tk.Canvas(right_frame, bg="#FAFAFA",
                                             highlightthickness=1,
                                             highlightbackground="#E0E0E0",
                                             height=220)
        self.pie_canvas_product.pack(fill=tk.BOTH, expand=True)
        self.pie_canvas_product.bind("<Configure>", lambda e: self._draw_pie_product())

        self._chart_widgets_pie = f

    def _build_radar_chart(self):
        """雷达图（教练综合能力画像）"""
        f = ttk.Frame(self.chart_stack)

        # 顶部：标题
        ttk.Label(f, text="🕸️ 教练综合能力画像（Top5）",
                  font=("微软雅黑", 11, "bold"), foreground="#2E75B6").pack(anchor=tk.W, pady=(0, 3))

        # 教练选择器
        selector_frame = ttk.Frame(f)
        selector_frame.pack(fill=tk.X)

        self.radar_coach_var = tk.StringVar()
        coaches = self._get_coach_list()
        ttk.Label(selector_frame, text="选择教练：", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.radar_combo = ttk.Combobox(selector_frame,
                                        textvariable=self.radar_coach_var,
                                        values=coaches,
                                        state="readonly", width=15, font=("微软雅黑", 9))
        self.radar_combo.pack(side=tk.LEFT, padx=5)
        if coaches:
            self.radar_combo.current(0)
        self.radar_combo.bind("<<ComboboxSelected>>", lambda e: self._draw_radar_chart())

        self.radar_canvas = tk.Canvas(f, bg="#FAFAFA",
                                       highlightthickness=1,
                                       highlightbackground="#E0E0E0",
                                       height=280)
        self.radar_canvas.pack(fill=tk.BOTH, expand=True)
        self.radar_canvas.bind("<Configure>", lambda e: self._draw_radar_chart())

        self._chart_widgets_radar = f

    def _build_rank_chart(self):
        """排行榜（教练业绩排行可视化）"""
        f = ttk.Frame(self.chart_stack)

        # 左：教练排行
        left_frame = ttk.Frame(f)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(left_frame, text="🏆 教练业绩排行（Top8）",
                  font=("微软雅黑", 11, "bold"), foreground="#2E75B6").pack(anchor=tk.W)

        self.rank_canvas_trainer = tk.Canvas(left_frame, bg="#FAFAFA",
                                              highlightthickness=1,
                                              highlightbackground="#E0E0E0",
                                              height=250)
        self.rank_canvas_trainer.pack(fill=tk.BOTH, expand=True)
        self.rank_canvas_trainer.bind("<Configure>", lambda e: self._draw_rank_trainer())

        # 右：课程销量排行
        right_frame = ttk.Frame(f)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(right_frame, text="🏆 课程销量排行（Top8）",
                  font=("微软雅黑", 11, "bold"), foreground="#2E75B6").pack(anchor=tk.W)

        self.rank_canvas_course = tk.Canvas(right_frame, bg="#FAFAFA",
                                             highlightthickness=1,
                                             highlightbackground="#E0E0E0",
                                             height=250)
        self.rank_canvas_course.pack(fill=tk.BOTH, expand=True)
        self.rank_canvas_course.bind("<Configure>", lambda e: self._draw_rank_course())

        self._chart_widgets_rank = f

    def _build_bottom_area(self):
        """底部区域：快捷操作 + 今日动态"""
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=20, pady=(5, 15))
        bottom_frame.columnconfigure(0, weight=2)
        bottom_frame.columnconfigure(1, weight=1)

        # 今日动态
        activity_frame = ttk.LabelFrame(bottom_frame, text="📋 今日动态")
        activity_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.activity_text = tk.Text(activity_frame, height=3, font=("微软雅黑", 9),
                                      fg="#555555", bg="#FAFAFA", wrap=tk.WORD,
                                      relief="flat", state=tk.DISABLED)
        self.activity_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 快捷操作
        quick_frame = ttk.LabelFrame(bottom_frame, text="⚡ 快捷操作")
        quick_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        actions_inner = ttk.Frame(quick_frame)
        actions_inner.pack(expand=True, pady=5)

        actions = [
            ("👤 新增会员", self._on_add_member),
            ("💰 新增售课", self._on_add_sale),
            ("🎓 新增上课", self._on_add_class),
            ("📅 新增预约", self._on_add_booking),
            ("⏰ 到期提醒", self._on_show_alerts),
            ("📊 全部报表", self._on_show_report),
        ]

        for i, (text, cmd) in enumerate(actions):
            row, col = divmod(i, 3)
            btn = tk.Button(actions_inner, text=text,
                           font=("微软雅黑", 10),
                           bg="#4472C4", fg="white",
                           activebackground="#2E75B6", activeforeground="white",
                           padx=12, pady=5, bd=0, cursor="hand2",
                           command=cmd)
            btn.grid(row=row, column=col, padx=4, pady=3, sticky="ew")
            actions_inner.columnconfigure(col, weight=1)

    # ========== 图表绘制方法 ==========

    def _draw_chart_trend(self):
        """绘制近7天售课趋势柱状图"""
        stats = self._last_stats
        daily_data = stats.get("daily_trend", [])
        draw_bar_chart(self.chart_canvas_trend, daily_data,
                       x_key="date", y_key="sale",
                       title="", colors=["#4472C4", "#ED7D31"])

    def _draw_chart_month(self):
        """绘制月度营收折线图"""
        stats = self._last_stats
        month_data = stats.get("monthly_trend", [])
        draw_line_chart(self.chart_canvas_month, month_data,
                        x_key="month", y_key="amount",
                        title="", color="#5B9BD5",
                        fill_color="#D6E4F0")

    def _draw_pie_course(self):
        """绘制课程类型饼图"""
        stats = self._last_stats
        course_dist = stats.get("course_distribution", [])
        draw_pie_chart(self.pie_canvas_course, course_dist,
                       label_key="name", value_key="count",
                       title="")

    def _draw_pie_product(self):
        """绘制商品类别饼图"""
        stats = self._last_stats
        product_dist = stats.get("product_distribution", [])
        draw_pie_chart(self.pie_canvas_product, product_dist,
                       label_key="name", value_key="amount",
                       title="")

    def _draw_radar_chart(self):
        """绘制教练综合能力雷达图"""
        coach_name = self.radar_coach_var.get()
        stats = self._last_stats
        all_radar = stats.get("coach_radar_data", {})

        if coach_name and coach_name in all_radar:
            data = all_radar[coach_name]
        else:
            # 取第一个有数据的
            data = next(iter(all_radar.values())) if all_radar else []

        draw_radar_chart(self.radar_canvas, data,
                         label_key="label", series_key="value",
                         title="")

    def _draw_rank_trainer(self):
        """绘制教练业绩排行"""
        stats = self._last_stats
        ranking = stats.get("trainer_ranking", [])
        draw_horizontal_bar(self.rank_canvas_trainer, ranking,
                            label_key="name", value_key="sale_amount",
                            title="", bar_height=18)

    def _draw_rank_course(self):
        """绘制课程销量排行"""
        stats = self._last_stats
        course_rank = stats.get("course_ranking", [])
        draw_horizontal_bar(self.rank_canvas_course, course_rank,
                            label_key="name", value_key="count",
                            title="", bar_height=18)

    # ========== 图表切换 ==========

    def _switch_chart(self, chart_key):
        """切换图表视图"""
        self._carousel_index = ["trend", "pie", "radar", "rank"].index(chart_key)
        widgets_map = {
            "trend": self._chart_widgets_trend,
            "pie":   self._chart_widgets_pie,
            "radar": self._chart_widgets_radar,
            "rank":  self._chart_widgets_rank,
        }

        # 隐藏所有
        for name in ["trend", "pie", "radar", "rank"]:
            if hasattr(self, f"_chart_widgets_{name}"):
                try:
                    getattr(self, f"_chart_widgets_{name}").pack_forget()
                except Exception:
                    pass

        # 显示选中
        w = widgets_map.get(chart_key)
        if w:
            w.pack(fill=tk.BOTH, expand=True)
            w.update_idletasks()
            # 激活绘制
            schedule = {
                "trend": lambda: (self._draw_chart_trend(), self._draw_chart_month()),
                "pie":   lambda: (self._draw_pie_course(), self._draw_pie_product()),
                "radar": self._draw_radar_chart,
                "rank":  lambda: (self._draw_rank_trainer(), self._draw_rank_course()),
            }
            fn = schedule.get(chart_key)
            if fn:
                self.after(50, fn)

        self._highlight_chart_btn(chart_key)

    def _highlight_chart_btn(self, active_key):
        """高亮选中图表按钮"""
        for key, btn in self.chart_btns.items():
            if key == active_key:
                btn.config(bg="#4472C4", fg="white")
            else:
                btn.config(bg="#F0F0F0", fg="#555555")

    def _next_chart(self):
        """轮播到下一个图表"""
        keys = ["trend", "pie", "radar", "rank"]
        self._carousel_index = (self._carousel_index + 1) % len(keys)
        self._switch_chart(keys[self._carousel_index])

    # ========== 数据加载 ==========

    def load_data(self):
        """加载所有看板数据"""
        try:
            stats = self.biz.get_dashboard_stats()
            self._last_stats = stats

            # 更新指标卡
            metric_map = {
                "active_members":      ("active_members", int),
                "new_members":         ("new_members", int),
                "total_remaining":     ("total_remaining", int),
                "class_count":         ("class_count", int),
                "sale_amount":         ("sale_amount", lambda v: f"¥{v:,.0f}"),
                "recharge_amount":     ("recharge_amount", lambda v: f"¥{v:,.0f}"),
                "product_sale_amount": ("product_sale_amount", lambda v: f"¥{v:,.0f}"),
                "expire_soon":         ("expire_soon", int),
            }

            for key, (stat_key, fmt) in metric_map.items():
                if key in self.metrics:
                    raw = stats.get(stat_key, 0)
                    display = fmt(raw) if raw else ("0" if fmt is int else "¥0")
                    self.metrics[key]["value"].config(text=str(display))

            # 更新所有图表
            self._draw_chart_trend()
            self._draw_chart_month()
            self._draw_pie_course()
            self._draw_pie_product()
            self._draw_radar_chart()
            self._draw_rank_trainer()
            self._draw_rank_course()

            # 更新今日动态
            self._update_activity(stats)

            # 更新时间
            now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
            self.time_label.config(text=f"📅 {now}")

            # 统计范围
            today = date.today()
            self.range_label.config(text=f"{today.year}年{today.month}月")

        except Exception:
            import traceback
            traceback.print_exc()

    def _update_activity(self, stats):
        """更新今日动态"""
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")

        try:
            members = self.biz.get_all_members()
            sales = self.biz.get_all_sales()
            classes = self.biz.get_all_class_records()

            new_today = sum(1 for m in members
                            if m.get("加入日期") and str(m["加入日期"])[:10] == today_str)
            sale_today = sum(1 for s in sales
                             if s.get("售课日期") and str(s["售课日期"])[:10] == today_str)
            class_today = sum(1 for c in classes
                              if c.get("上课日期") and str(c["上课日期"])[:10] == today_str)

            lines = [
                f"🎯 今日进场 {stats.get('today_checkin_count', 0)} 人",
                f"📌 今日新增会员 {new_today} 人 | 售课 {sale_today} 笔 | 上课 {class_today} 节",
                f"💰 本月累计售课 ¥{stats.get('sale_amount', 0):,.0f} | "
                f"充值 ¥{stats.get('recharge_amount', 0):,.0f} | "
                f"零售 ¥{stats.get('product_sale_amount', 0):,.0f}",
                f"👥 有效会员 {stats.get('active_members', 0)} 人 | "
                f"总剩余 {stats.get('total_remaining', 0):,.0f} 课时 | "
                f"到期提醒 {stats.get('expire_soon', 0)} 人",
            ]

            # 如果有进场明细，追加几句
            checkin_list = stats.get('today_checkin_list', [])
            for s in checkin_list[:8]:  # 最多显示8条
                lines.append(f"  ├ {s}")

            self.activity_text.config(state=tk.NORMAL)
            self.activity_text.delete("1.0", tk.END)
            self.activity_text.insert("1.0", "\n".join(lines))
            self.activity_text.config(state=tk.DISABLED)

        except Exception:
            pass

    def _get_coach_list(self):
        """获取教练列表"""
        try:
            staff = self.biz.get_all_staff_members()
            coaches = [s.get("姓名", "") for s in staff
                       if s.get("职务") in ("教练", "私教", "高级教练")]
            return coaches or ["暂无教练"]
        except Exception:
            return ["暂无教练"]

    def _trigger_redraw(self):
        """触发所有图表重绘"""
        # 延迟重绘，等布局稳定
        self.after(100, lambda: [
            self._draw_chart_trend(),
            self._draw_chart_month(),
            self._draw_pie_course(),
            self._draw_pie_product(),
            self._draw_radar_chart(),
            self._draw_rank_trainer(),
            self._draw_rank_course(),
        ])

    # ========== 轮播控制 ==========

    def _toggle_carousel(self):
        """切换轮播"""
        if self.carousel_var.get():
            self._start_carousel()
        else:
            self._stop_carousel()

    def _start_carousel(self):
        """开始图表轮播"""
        self._stop_carousel()
        self._carousel_id = self.after(8000, self._carousel_callback)

    def _carousel_callback(self):
        """轮播回调"""
        if self.carousel_var.get():
            self._next_chart()
            self._start_carousel()

    def _stop_carousel(self):
        """停止轮播"""
        if self._carousel_id:
            self.after_cancel(self._carousel_id)
            self._carousel_id = None

    # ========== 自动刷新 ==========

    def _toggle_auto_refresh(self):
        if self.auto_refresh_var.get():
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()

    def _start_auto_refresh(self):
        self._stop_auto_refresh()
        self._auto_refresh_id = self.after(30000, self._auto_refresh_callback)

    def _auto_refresh_callback(self):
        if self.auto_refresh_var.get():
            self.load_data()
            self._start_auto_refresh()

    def _stop_auto_refresh(self):
        if self._auto_refresh_id:
            self.after_cancel(self._auto_refresh_id)
            self._auto_refresh_id = None

    # ========== 大屏模式 ==========

    def toggle_fullscreen(self):
        root = self.winfo_toplevel()
        self.is_fullscreen = not self.is_fullscreen
        root.attributes("-fullscreen", self.is_fullscreen)
        if self.is_fullscreen:
            self.fs_btn.config(text="❌ 退出大屏", bg="#E74C3C")
            self.title_label.config(font=("微软雅黑", 24, "bold"))
            # 大屏自动开启轮播
            self.carousel_var.set(True)
            self._start_carousel()
        else:
            self.fs_btn.config(text="🖥️ 大屏模式", bg="#4472C4")
            self.title_label.config(font=("微软雅黑", 18, "bold"))
            self.carousel_var.set(False)
            self._stop_carousel()
        self._trigger_redraw()

    # ========== 快捷操作回调 ==========

    def _on_add_member(self):
        if self._main_win and hasattr(self._main_win, "show_member"):
            self._main_win.show_member()

    def _on_add_sale(self):
        if self._main_win and hasattr(self._main_win, "show_sale"):
            self._main_win.show_sale()

    def _on_add_class(self):
        if self._main_win and hasattr(self._main_win, "show_class_record"):
            self._main_win.show_class_record()

    def _on_add_booking(self):
        if self._main_win and hasattr(self._main_win, "show_booking"):
            self._main_win.show_booking()

    def _on_show_alerts(self):
        if self._main_win and hasattr(self._main_win, "show_alert"):
            self._main_win.show_alert()

    def _on_show_report(self):
        if self._main_win and hasattr(self._main_win, "show_export"):
            self._main_win.show_export()

    def destroy(self):
        self._stop_auto_refresh()
        self._stop_carousel()
        super().destroy()
