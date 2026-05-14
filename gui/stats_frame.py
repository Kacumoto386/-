"""
统计分析模块 - 售课统计、上课统计、员工提成
"""
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime


class BaseStatsFrame(ttk.Frame):
    """统计基础框架"""

    def __init__(self, parent, biz, title):
        super().__init__(parent)
        self.biz = biz
        self.title = title
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text=self.title,
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        tk.Button(header, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.refresh).pack(side=tk.RIGHT, padx=5)


class SaleStatsFrame(BaseStatsFrame):
    """售课统计"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "📊 售课统计报表")
        self.build_content()

    def build_content(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 按时间筛选
        filter_frame = ttk.Frame(main)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="统计期间：",
                  font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.period_var = tk.StringVar(value="本月")
        period_menu = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                   values=["今日", "本周", "本月", "本季度", "本年", "全部"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        period_menu.pack(side=tk.LEFT, padx=5)
        period_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        tk.Button(filter_frame, text="📊 计算统计", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self._calc_stats).pack(side=tk.LEFT, padx=5)

        # 统计结果
        result_frame = ttk.Frame(main)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 卡片式指标
        card_frame = ttk.Frame(result_frame)
        card_frame.pack(fill=tk.X)

        self.stats_labels = {}
        stat_items = [
            ("总售课金额", "¥0"), ("总售课节数", "0"),
            ("总实收金额", "¥0"), ("售课订单数", "0"),
            ("平均单价", "¥0"), ("最高单笔", "¥0"),
        ]

        for i, (label, default) in enumerate(stat_items):
            row, col = divmod(i, 3)
            card_frame_w, card_value = self._make_card(card_frame, label, default)
            card_frame_w.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_labels[label] = card_value

        for i in range(3):
            card_frame.columnconfigure(i, weight=1)

        # 详细表格
        ttk.Label(result_frame, text="📋 售课明细",
                  font=("微软雅黑", 11, "bold"), foreground="#2E75B6").pack(anchor=tk.W, pady=(10, 5))

        table_frame = ttk.Frame(result_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("售课编号", "售课日期", "会员姓名", "课程名称", "购买课时数", "实收金额", "付款方式")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        col_widths = [140, 100, 80, 120, 80, 80, 80]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60)

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

    def _calc_stats(self):
        """计算统计"""
        rows = self.biz.get_all_sales()
        if not rows:
            return

        today = date.today()
        period = self.period_var.get()

        def in_period(dt):
            if not dt:
                return period == "全部"
            if isinstance(dt, str):
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d").date()
                except ValueError:
                    return period == "全部"
            if period == "今日":
                return dt == today
            elif period == "本周":
                monday = today.isocalendar()
                return dt.isocalendar()[1] == monday[1] and dt.year == today.year
            elif period == "本月":
                return dt.month == today.month and dt.year == today.year
            elif period == "本季度":
                q = (today.month - 1) // 3
                return (dt.month - 1) // 3 == q and dt.year == today.year
            elif period == "本年":
                return dt.year == today.year
            return True

        filtered = []
        for r in rows:
            sale_date = r.get("售课日期")
            if in_period(sale_date):
                filtered.append(r)

        if not filtered:
            for k in self.stats_labels:
                self.stats_labels[k].config(text="0")
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        total_amount = sum(float(r.get("实收金额", 0) or 0) for r in filtered)
        total_qty = sum(int(r.get("购买课时数", 0) or 0) for r in filtered)
        total_received = sum(float(r.get("实收金额", 0) or 0) for r in filtered)
        count = len(filtered)
        avg_price = total_received / count if count > 0 else 0
        max_sale = max(float(r.get("实收金额", 0) or 0) for r in filtered)

        self.stats_labels["总售课金额"].config(text=f"¥{total_amount:,.0f}")
        self.stats_labels["总售课节数"].config(text=str(int(total_qty)))
        self.stats_labels["总实收金额"].config(text=f"¥{total_received:,.0f}")
        self.stats_labels["售课订单数"].config(text=str(count))
        self.stats_labels["平均单价"].config(text=f"¥{avg_price:,.0f}")
        self.stats_labels["最高单笔"].config(text=f"¥{max_sale:,.0f}")

        # 填充表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in filtered:
            self.tree.insert("", tk.END, values=(
                r.get("售课编号", ""),
                r.get("售课日期", ""),
                r.get("会员姓名", ""),
                r.get("课程名称", ""),
                int(r.get("购买课时数", 0) or 0),
                f"¥{float(r.get('实收金额', 0) or 0):.0f}",
                r.get("付款方式", ""),
            ))

    def refresh(self):
        self._calc_stats()


class ClassStatsFrame(BaseStatsFrame):
    """上课统计"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "📈 上课统计报表")
        self.build_content()

    def build_content(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        filter_frame = ttk.Frame(main)
        filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(filter_frame, text="统计期间：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.period_var = tk.StringVar(value="本月")
        period_menu = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                   values=["今日", "本周", "本月", "本季度", "本年", "全部"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        period_menu.pack(side=tk.LEFT, padx=5)
        period_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        tk.Button(filter_frame, text="📊 计算统计", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self._calc_stats).pack(side=tk.LEFT, padx=5)

        result_frame = ttk.Frame(main)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        card_frame = ttk.Frame(result_frame)
        card_frame.pack(fill=tk.X)

        self.stats_labels = {}
        stat_items = [
            ("总上课节数", "0"), ("总消耗课时", "0"),
            ("上课学员数", "0"), ("教练上课次数", "0"),
        ]

        for i, (label, default) in enumerate(stat_items):
            row, col = divmod(i, 2)
            card_frame_w, card_value = self._make_card(card_frame, label, default)
            card_frame_w.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_labels[label] = card_value

        for i in range(2):
            card_frame.columnconfigure(i, weight=1)

        # 按课程分类统计
        ttk.Label(result_frame, text="📋 课程上课频次统计",
                  font=("微软雅黑", 11, "bold"), foreground="#2E75B6").pack(anchor=tk.W, pady=(10, 5))

        table_frame = ttk.Frame(result_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("课程名称", "上课次数", "总消耗课时", "上课人数", "占比")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        col_widths = [150, 100, 100, 100, 100]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60)

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

    def _calc_stats(self):
        rows = self.biz.get_all_class_records()
        if not rows:
            return

        today = date.today()
        period = self.period_var.get()

        def in_period(dt):
            if not dt:
                return period == "全部"
            if isinstance(dt, str):
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d").date()
                except ValueError:
                    return period == "全部"
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

        filtered = [r for r in rows if in_period(r.get("上课日期"))]

        if not filtered:
            for k in self.stats_labels:
                self.stats_labels[k].config(text="0")
            for item in self.tree.get_children():
                self.tree.delete(item)
            return

        total_classes = len(filtered)
        total_lessons_used = sum(int(r.get("消耗课时数", 0) or 0) for r in filtered)
        member_set = set(r.get("会员编号", "") for r in filtered if r.get("会员编号"))
        coach_set = set(r.get("授课教练", "") for r in filtered if r.get("授课教练"))

        self.stats_labels["总上课节数"].config(text=str(total_classes))
        self.stats_labels["总消耗课时"].config(text=str(int(total_lessons_used)))
        self.stats_labels["上课学员数"].config(text=str(len(member_set)))
        self.stats_labels["教练上课次数"].config(text=str(len(coach_set)))

        # 按课程分组
        course_stats = {}
        for r in filtered:
            course = r.get("课程名称", "未知")
            if course not in course_stats:
                course_stats[course] = {"count": 0, "lessons": 0, "members": set()}
            course_stats[course]["count"] += 1
            course_stats[course]["lessons"] += int(r.get("消耗课时数", 0) or 0)
            course_stats[course]["members"].add(r.get("会员编号", ""))

        for item in self.tree.get_children():
            self.tree.delete(item)
        for course, stats in sorted(course_stats.items(), key=lambda x: -x[1]["count"]):
            pct = f"{stats['count'] / total_classes * 100:.1f}%" if total_classes > 0 else "0%"
            self.tree.insert("", tk.END, values=(
                course, stats["count"], stats["lessons"],
                len(stats["members"]), pct,
            ))

    def refresh(self):
        self._calc_stats()


class CommissionFrame(BaseStatsFrame):
    """员工提成统计（V2 - 支持梯度提成）"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "💵 员工提成报表")
        self.show_detail = False  # 是否显示详细分段
        self.build_content()

    def build_content(self):
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 第一行：统计期间
        filter_frame = ttk.Frame(main)
        filter_frame.pack(fill=tk.X, pady=3)

        ttk.Label(filter_frame, text="统计期间：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.period_var = tk.StringVar(value="本月")
        period_menu = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                   values=["本月", "上月", "本年", "全部"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        period_menu.pack(side=tk.LEFT, padx=5)
        period_menu.bind("<<ComboboxSelected>>", lambda e: self._calc_stats())

        tk.Button(filter_frame, text="📊 计算提成", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self._calc_stats).pack(side=tk.LEFT, padx=5)

        # 第二行：梯度管理按钮 + 详细模式切换
        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, pady=3)

        tk.Button(action_frame, text="⚙️ 梯度配置", font=("微软雅黑", 9),
                  bg="#7030A0", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.on_open_tier_config).pack(side=tk.LEFT, padx=5)

        self.detail_btn = tk.Button(action_frame, text="📋 显示详细分段", font=("微软雅黑", 9),
                                    bg="#5B9BD5", fg="white", padx=10, pady=2, bd=0,
                                    cursor="hand2", command=self.on_toggle_detail)
        self.detail_btn.pack(side=tk.LEFT, padx=5)

        # 梯度状态提示
        self.tier_status = tk.Label(action_frame, text="",
                                    font=("微软雅黑", 9), fg="#666")
        self.tier_status.pack(side=tk.LEFT, padx=15)

        # 主表格
        table_frame = ttk.Frame(main)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 根据是否显示详细模式，用不同的列
        self.columns_detail = (
            "员工姓名", "岗位", "售课金额", "售课梯度", "售课提成",
            "上课节数", "上课梯度", "上课提成", "总提成", "排名"
        )
        self.columns_simple = ("员工姓名", "岗位", "售课提成金额", "上课提成金额",
                               "总提成", "匹配梯度", "绩效排名")
        self.table_frame = table_frame
        self._build_table(table_frame)

        # 合计行
        self.total_bar = ttk.Frame(main)
        self.total_bar.pack(fill=tk.X, pady=5)
        self.total_label = tk.Label(self.total_bar, text="总计：—",
                                    font=("微软雅黑", 11, "bold"),
                                    fg="#1F4E79", bg="#F0F0F0", anchor=tk.W)
        self.total_label.pack(fill=tk.X, padx=5, pady=5, ipady=5)

        self._calc_stats()

    def _build_table(self, parent):
        """构建表格"""
        if hasattr(self, 'table_container') and self.table_container:
            self.table_container.destroy()

        self.table_container = ttk.Frame(parent)
        self.table_container.pack(fill=tk.BOTH, expand=True)

        cols = self.columns_detail if self.show_detail else self.columns_simple
        self.tree = ttk.Treeview(self.table_container, columns=cols, show="headings", height=15)

        if self.show_detail:
            col_widths = [90, 60, 90, 130, 90, 70, 130, 90, 90, 55]
        else:
            col_widths = [90, 60, 110, 110, 110, 130, 80]
        for col, w in zip(cols, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=50)

        scroll = ttk.Scrollbar(self.table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def on_toggle_detail(self):
        """切换详细/简洁模式"""
        self.show_detail = not self.show_detail
        self._build_table(self.table_frame)
        self.detail_btn.config(text="📋 简洁模式" if self.show_detail else "📋 显示详细分段")
        self._calc_stats()

    def on_open_tier_config(self):
        """打开梯度配置界面"""
        try:
            from gui.commission_tier_frame import CommissionTierFrame
            top = tk.Toplevel(self.winfo_toplevel())
            top.title("⚙️ 梯度提成配置")
            top.geometry("850x600")
            top.transient(self.winfo_toplevel())
            frame = CommissionTierFrame(top, self.biz)
            frame.pack(fill=tk.BOTH, expand=True)
            self.winfo_toplevel().wait_window(top)
            self._calc_stats()
        except Exception as e:
            messagebox.showerror("错误", f"打开梯度配置失败: {str(e)}")

    def _calc_stats(self):
        """计算员工提成（使用梯度提成引擎）"""
        sales = self.biz.get_all_sales()
        classes = self.biz.get_all_class_records()
        staff = self.biz.get_all_staff()
        if not staff:
            return

        today = date.today()
        period = self.period_var.get()

        def in_month(dt, target_month, target_year):
            if not dt:
                return period == "全部"
            if isinstance(dt, str):
                try:
                    dt = datetime.strptime(dt, "%Y-%m-%d").date()
                except ValueError:
                    return period == "全部"
            return dt.month == target_month and dt.year == target_year

        if period == "本月":
            t_month, t_year = today.month, today.year
        elif period == "上月":
            t_month = today.month - 1 or 12
            t_year = today.year if t_month != 12 else today.year - 1
        elif period == "本年":
            t_month, t_year = None, today.year
        else:
            t_month, t_year = None, None

        def is_in_period(dt):
            if t_month and t_year:
                return in_month(dt, t_month, t_year)
            elif t_year:
                if isinstance(dt, str):
                    try:
                        dt = datetime.strptime(dt, "%Y-%m-%d").date()
                    except ValueError:
                        return False
                return dt.year == t_year
            return True

        filtered_sales = [s for s in sales if is_in_period(s.get("售课日期"))]
        filtered_classes = [c for c in classes if is_in_period(c.get("上课日期"))]

        # 累积每个员工的销售额和上课量
        staff_sale_amounts = {}
        staff_class_counts = {}
        staff_positions = {}

        for s in staff:
            name = s.get("姓名", "")
            staff_positions[name] = s.get("岗位", "")
            staff_sale_amounts[name] = 0.0
            staff_class_counts[name] = 0.0

        for s in filtered_sales:
            raw_name = s.get("销售员工", "")
            name = raw_name.split(" - ")[-1] if " - " in str(raw_name) else str(raw_name)
            amount = float(s.get("实收金额", 0) or 0)
            if name in staff_sale_amounts:
                staff_sale_amounts[name] += amount
            else:
                staff_sale_amounts[name] = amount

        for c in filtered_classes:
            raw_name = c.get("授课教练", "")
            name = raw_name.split(" - ")[-1] if " - " in str(raw_name) else str(raw_name)
            lessons = int(c.get("消耗课时数", 1) or 1)
            if name in staff_class_counts:
                staff_class_counts[name] += lessons
            else:
                staff_class_counts[name] = lessons

        # 计算梯度提成
        staff_results = {}
        for name in staff_sale_amounts:
            sale_amount = staff_sale_amounts.get(name, 0)
            sale_result = self.biz.calc_sale_commission_by_tier(name, sale_amount)
            class_count = staff_class_counts.get(name, 0)
            class_result = self.biz.calc_class_commission_by_tier(name, class_count)
            staff_results[name] = {
                "岗位": staff_positions.get(name, ""),
                "售课金额": sale_amount,
                "售课提成": sale_result["total_commission"],
                "售课梯度名称": sale_result["tier_name"],
                "售课分段": sale_result["segments"],
                "上课节数": int(class_count),
                "上课提成": class_result["total_commission"],
                "上课梯度名称": class_result["tier_name"],
                "上课分段": class_result["segments"],
            }

        # 更新梯度提示
        sale_rules = self.biz.get_tier_rules("售课提成")
        class_rules = self.biz.get_tier_rules("上课提成")
        if sale_rules or class_rules:
            self.tier_status.config(
                text=f"📐 售课{len(sale_rules)}档 | 上课{len(class_rules)}档 · 分段累进计算"
            )
        else:
            self.tier_status.config(text="⚠️ 暂未配置梯度规则，使用固定比例计算")

        # 填充表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_commission = 0.0
        total_sale_com = 0.0
        total_class_com = 0.0
        ranked = []

        for name, result in staff_results.items():
            total_com = result["售课提成"] + result["上课提成"]
            total_commission += total_com
            total_sale_com += result["售课提成"]
            total_class_com += result["上课提成"]
            ranked.append((name, total_com))

        ranked.sort(key=lambda x: -x[1])

        for idx, (name, total_com) in enumerate(ranked):
            r = staff_results[name]

            if self.show_detail:
                # 完善课梯度标签
                sale_tier_label = r["售课梯度名称"]
                if r["售课分段"]:
                    seg_str = " → ".join(
                        f"{s['range']}×{s['rate']*100:.0f}%"
                        for s in r["售课分段"][:2]
                    )
                    if len(r["售课分段"]) > 2:
                        seg_str += "…"
                    sale_tier_label = seg_str

                class_tier_label = r["上课梯度名称"]
                if r["上课分段"]:
                    seg_str = " → ".join(
                        f"{s['range']}×{s['rate']*100:.0f}%"
                        for s in r["上课分段"][:2]
                    )
                    if len(r["上课分段"]) > 2:
                        seg_str += "…"
                    class_tier_label = seg_str

                self.tree.insert("", tk.END, values=(
                    name,
                    r["岗位"],
                    f"¥{r['售课金额']:,.0f}",
                    sale_tier_label,
                    f"¥{r['售课提成']:,.0f}",
                    f"{r['上课节数']}节",
                    class_tier_label,
                    f"¥{r['上课提成']:,.0f}",
                    f"¥{total_com:,.0f}",
                    f"#{idx + 1}",
                ))
            else:
                # 简洁模式
                tier_label = r["售课梯度名称"]
                if r["上课节数"] > 0:
                    tier_label += f" / {r['上课梯度名称']}"

                self.tree.insert("", tk.END, values=(
                    name,
                    r["岗位"],
                    f"¥{r['售课提成']:,.0f}",
                    f"¥{r['上课提成']:,.0f}",
                    f"¥{total_com:,.0f}",
                    tier_label,
                    f"#{idx + 1}",
                ))

        self.total_label.config(
            text=f"📋 统计期间 {self.period_var.get()} | "
                 f"售课提成合计: ¥{total_sale_com:,.0f} | "
                 f"上课提成合计: ¥{total_class_com:,.0f} | "
                 f"总提成: ¥{total_commission:,.0f}"
        )

    def refresh(self):
        self._calc_stats()
