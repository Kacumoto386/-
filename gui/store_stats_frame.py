"""
跨店统计看板 - 多门店数据对比与报表
"""
import tkinter as tk
from tkinter import ttk
from datetime import date


class StoreStatsFrame(ttk.Frame):
    """跨店统计看板"""

    def __init__(self, parent, biz, store_mgr):
        super().__init__(parent)
        self.biz = biz
        self.mgr = store_mgr
        self.build_ui()
        self.refresh()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📊 跨店统计看板",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        tk.Button(header, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.refresh).pack(side=tk.RIGHT, padx=2)

        # 统计卡片
        card_frame = ttk.Frame(self)
        card_frame.pack(fill=tk.X, padx=15, pady=5)

        self.cards = {}
        card_configs = [
            ("total_stores", "🏪 门店总数", "#4472C4"),
            ("total_members", "👥 会员总数", "#70AD47"),
            ("total_staff", "👨‍💼 员工总数", "#FFC000"),
        ]
        for i, (key, label, color) in enumerate(card_configs):
            card = self._make_card(card_frame, label, color)
            card["frame"].pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
            self.cards[key] = card

        # 门店对比表格
        table_frame = ttk.LabelFrame(self, text="📋 门店数据对比")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=(
            "门店名称", "状态", "有效会员", "本月新增", "本月售课额",
            "本月充值额", "本月零售额", "本月上课数"
        ), show="headings", height=10)

        col_widths = [120, 70, 80, 80, 100, 100, 100, 80]
        for col, w in zip(self.tree["columns"], col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # 底部说明
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        self.info_label = ttk.Label(info_frame, text="",
                                    font=("微软雅黑", 9), foreground="#999")
        self.info_label.pack(side=tk.LEFT)

    def _make_card(self, parent, label, color):
        """创建统计卡片"""
        frame = tk.Frame(parent, bg="white", relief="solid", bd=1,
                         highlightbackground="#E0E0E0", highlightthickness=1)
        frame.configure(height=80, width=200)
        frame.pack_propagate(False)

        value_label = tk.Label(frame, text="—", font=("微软雅黑", 22, "bold"),
                               fg=color, bg="white")
        value_label.pack(pady=(8, 0))

        name_label = tk.Label(frame, text=label, font=("微软雅黑", 9),
                              fg="#666666", bg="white")
        name_label.pack()

        return {"frame": frame, "value": value_label}

    def refresh(self):
        """刷新数据（按门店编号字段直接聚合）"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        stores = self.mgr.get_all_stores()
        today = date.today()
        current_month = today.month
        current_year = today.year

        total_members = 0
        total_staff = 0

        # 一次读取所有业务数据
        all_members = self.biz.get_all_members()
        all_staff = self.biz.get_all_staff()
        all_sales = self.biz.get_all_sales()
        all_recharges = self.biz.get_all_recharges()
        all_retails = self.biz.get_all_product_sales()
        all_classes = self.biz.get_all_class_records()

        def _safe_date(val):
            """安全转换日期"""
            if not val:
                return None
            try:
                if isinstance(val, date):
                    return val
                from datetime import datetime
                val_str = str(val).strip()[:10]
                return datetime.strptime(val_str, "%Y-%m-%d").date()
            except:
                return None

        def _safe_float(val):
            """安全转换浮点数"""
            if not val:
                return 0
            try:
                return float(val)
            except:
                return 0

        for store in stores:
            store_id = store.get("门店编号", "")
            store_name = store.get("门店名称", "")

            # 会员统计 —— 直接用门店编号字段过滤
            store_members = [m for m in all_members if m.get("门店编号", "") == store_id]
            member_count = len(store_members)
            total_members += member_count

            new_members = sum(1 for m in store_members
                if m.get("会员状态", "") in ("有效", "正常", "active", "")
                and _safe_date(m.get("入会日期"))
                and _safe_date(m.get("入会日期")).month == current_month
                and _safe_date(m.get("入会日期")).year == current_year)

            # 员工统计
            staff_count = sum(1 for s in all_staff if s.get("门店编号", "") == store_id)
            total_staff += staff_count

            # 售课额
            sale_amount = sum(
                _safe_float(s.get("实收金额", 0)) for s in all_sales
                if s.get("门店编号", "") == store_id
                and _safe_date(s.get("售课日期"))
                and _safe_date(s.get("售课日期")).month == current_month
                and _safe_date(s.get("售课日期")).year == current_year
            )

            # 充值额
            recharge_amount = sum(
                _safe_float(r.get("充值金额", 0)) for r in all_recharges
                if r.get("门店编号", "") == store_id
                and _safe_date(r.get("充值日期"))
                and _safe_date(r.get("充值日期")).month == current_month
                and _safe_date(r.get("充值日期")).year == current_year
            )

            # 零售额
            retail_amount = sum(
                _safe_float(p.get("总价", 0)) for p in all_retails
                if p.get("门店编号", "") == store_id
                and _safe_date(p.get("零售日期"))
                and _safe_date(p.get("零售日期")).month == current_month
                and _safe_date(p.get("零售日期")).year == current_year
            )

            # 上课数
            class_count = sum(1 for c in all_classes
                if c.get("门店编号", "") == store_id
                and _safe_date(c.get("上课日期"))
                and _safe_date(c.get("上课日期")).month == current_month
                and _safe_date(c.get("上课日期")).year == current_year
            )

            self.tree.insert("", "end", values=(
                store_name,
                store.get("门店状态", ""),
                member_count,
                new_members,
                f"¥{sale_amount:,.0f}",
                f"¥{recharge_amount:,.0f}",
                f"¥{retail_amount:,.0f}",
                class_count,
            ))

        # 更新汇总卡片
        self.cards["total_stores"]["value"].config(text=str(len(stores)))
        self.cards["total_members"]["value"].config(text=str(total_members))
        self.cards["total_staff"]["value"].config(text=str(total_staff))

        self.info_label.config(
            text=f"📅 {today.strftime('%Y年%m月')} 经营数据 | 共 {len(stores)} 个门店"
        )
