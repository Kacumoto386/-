# -*- coding: utf-8 -*-
"""
售卡记录管理模块 - V2.14.0
展示会籍卡（会员卡）的销售记录
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS, MEMBERSHIP_STATUSES


class MembershipSaleFrame(ttk.Frame):
    """售卡记录管理主界面"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self._all_records = []
        self._filtered_records = []
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="🃏 售卡记录",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=15, pady=5)

        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)

        self.btn_refresh = tk.Button(btn_frame, text="🔄 刷新",
                                     font=("微软雅黑", 10),
                                     bg="#E0E0E0", fg="#333333",
                                     padx=12, pady=3, bd=0, cursor="hand2",
                                     command=self.refresh_data)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        self.btn_reactivate = tk.Button(btn_frame, text="🔄 重新激活（已过期→有效）",
                                        font=("微软雅黑", 10),
                                        bg="#E67E22", fg="white",
                                        padx=12, pady=3, bd=0, cursor="hand2",
                                        command=self.on_reactivate)
        self.btn_reactivate.pack(side=tk.LEFT, padx=2)

        # 右侧筛选
        filter_frame = ttk.Frame(toolbar)
        filter_frame.pack(side=tk.RIGHT)

        ttk.Label(filter_frame, text="状态：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        self.status_var = tk.StringVar()
        status_values = ["全部", "有效", "已过期", "已用完", "已退费"]
        self.status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var,
                                          values=status_values, font=("微软雅黑", 9),
                                          width=10, state="readonly")
        self.status_combo.set("全部")
        self.status_combo.pack(side=tk.LEFT, padx=2)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        ttk.Label(filter_frame, text=" 会员：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(5, 2))
        self.member_var = tk.StringVar()
        members = self.biz.get_member_id_names()
        member_values = ["全部"] + list(members.values())
        self.member_combo = ttk.Combobox(filter_frame, textvariable=self.member_var,
                                          values=member_values, font=("微软雅黑", 9),
                                          width=22, state="readonly")
        self.member_combo.set("全部")
        self.member_combo.pack(side=tk.LEFT, padx=2)
        self.member_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # 表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = [
            "会籍卡编号", "会员姓名", "会员手机号", "卡类型", "卡名称",
            "售价", "实收金额", "付款方式", "销售员工",
            "开卡日期", "有效期起", "有效期止",
            "总次数", "已消耗次数", "剩余次数",
            "余额", "已消费金额", "有效天数",
            "状态", "备注"
        ]
        # 显示列（精简版，隐藏一些不常用的技术字段）
        display_cols = [
            ("会籍卡编号", 150), ("会员姓名", 80), ("会员手机号", 110),
            ("卡类型", 60), ("卡名称", 100),
            ("售价", 70), ("实收金额", 75), ("付款方式", 70),
            ("销售员工", 70),
            ("开卡日期", 90), ("有效期止", 90),
            ("总次数", 60), ("剩余次数", 60), ("余额", 70),
            ("有效天数", 60),
            ("状态", 60), ("备注", 150),
        ]

        self.tree = ttk.Treeview(table_frame, columns=[c for c, w in display_cols],
                                 show="headings", selectmode="browse")
        for col, w in display_cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=50)

        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", lambda e: self.on_reactivate())

        # 底部状态栏
        self.status_label = ttk.Label(self, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(side=tk.BOTTOM, anchor=tk.E, padx=15, pady=5)

        self.selected_row_num = None

    def refresh_data(self):
        """刷新数据"""
        try:
            self._all_records = self.biz.get_all_memberships()
        except Exception:
            self._all_records = []
        self._apply_filter()

    def _apply_filter(self):
        """应用筛选"""
        keyword_status = self.status_var.get()
        keyword_member = self.member_var.get()

        records = list(self._all_records)

        # 状态筛选
        if keyword_status and keyword_status != "全部":
            records = [r for r in records if r.get("状态", "") == keyword_status]

        # 会员筛选
        if keyword_member and keyword_member != "全部":
            records = [r for r in records if keyword_member in str(r.get("会员姓名", ""))
                       or keyword_member in str(r.get("会员手机号", ""))]

        self._filtered_records = records

        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in records:
            # 格式化日期
            sale_date = r.get("开卡日期", "")
            if hasattr(sale_date, 'strftime'):
                sale_date = sale_date.strftime("%Y-%m-%d")
            valid_to = r.get("有效期止", "")
            if hasattr(valid_to, 'strftime'):
                valid_to = valid_to.strftime("%Y-%m-%d")

            values = [
                r.get("会籍卡编号", ""),
                r.get("会员姓名", ""),
                r.get("会员手机号", ""),
                r.get("卡类型", ""),
                r.get("卡名称", ""),
                r.get("售价", ""),
                r.get("实收金额", ""),
                r.get("付款方式", ""),
                r.get("销售员工", ""),
                sale_date,
                valid_to,
                r.get("总次数", ""),
                r.get("剩余次数", ""),
                r.get("余额", ""),
                r.get("有效天数", ""),
                r.get("状态", ""),
                r.get("备注", ""),
            ]
            # 标记颜色
            tags = ()
            status = r.get("状态", "")
            if status == "已过期":
                tags = ("expired",)
            elif status == "已退费":
                tags = ("refunded",)
            elif status == "已用完":
                tags = ("used_up",)

            self.tree.insert("", tk.END, values=values, tags=tags)

        # 设置颜色
        self.tree.tag_configure("expired", foreground="#E74C3C")
        self.tree.tag_configure("refunded", foreground="#999999")
        self.tree.tag_configure("used_up", foreground="#95A5A6")

        total = len(self._all_records)
        shown = len(records)
        self.status_label.config(text=f"📊 共 {shown}/{total} 条售卡记录")

    # ── 重新激活 ──

    def on_reactivate(self):
        """重新激活已过期的产品"""
        row = self.get_selected()
        if not row:
            return

        status = row.get("状态", "")
        if status not in ("已过期", "已用完", "已退费"):
            messagebox.showinfo("提示", f"当前状态为 '{status}'，无需重新激活")
            return

        card_id = row.get("会籍卡编号", "")
        member_name = row.get("会员姓名", "")
        card_type = row.get("卡类型", "")

        # 根据不同卡类型定制对话框
        ReactivateMembershipDialog(self.winfo_toplevel(), self.biz, self, row)

    def get_selected(self):
        """获取选中的记录"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条记录")
            return None
        index = self.tree.index(selection[0])
        if index < len(self._filtered_records):
            return self._filtered_records[index]
        return None

    def refresh_and_show(self, msg):
        """刷新后显示提示"""
        self.refresh_data()
        if msg:
            messagebox.showinfo("成功", msg)


class ReactivateMembershipDialog(tk.Toplevel):
    """售卡记录重新激活对话框"""

    def __init__(self, parent, biz, frame, row_data):
        super().__init__(parent)
        self.biz = biz
        self.frame = frame
        self.row_data = row_data
        self.row_num = row_data.get("_row")

        self.title(f"🔄 重新激活 - {row_data.get('会籍卡编号', '')}")
        self.geometry("450x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        r = self.row_data
        card_type = r.get("卡类型", "")

        info_text = (
            f"会籍卡编号：{r.get('会籍卡编号', '')}\n"
            f"会员：{r.get('会员姓名', '')}\n"
            f"卡类型：{card_type}\n"
            f"卡名称：{r.get('卡名称', '')}\n"
            f"当前状态：{r.get('状态', '')}"
        )

        info_label = ttk.Label(main, text=info_text, font=("微软雅黑", 10),
                               justify=tk.LEFT, background="#F9F9F9",
                               relief="solid", padding=10)
        info_label.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main, text="激活设置", font=("微软雅黑", 11, "bold"),
                  foreground="#1F4E79").pack(anchor=tk.W, pady=(5, 5))

        # 新有效期
        fields_frame = ttk.Frame(main)
        fields_frame.pack(fill=tk.X, pady=5)

        ttk.Label(fields_frame, text="新的有效期起：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.valid_from_entry = tk.Entry(fields_frame, font=("微软雅黑", 10), width=25)
        self.valid_from_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.valid_from_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(fields_frame, text="新的有效期止：", font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.valid_to_entry = tk.Entry(fields_frame, font=("微软雅黑", 10), width=25)

        # 根据卡类型给出默认有效期
        if card_type == "次卡":
            total = r.get("总次数", 0)
            default_days = 180  # 次卡默认半年
        elif card_type == "期限卡":
            days = r.get("有效天数", 30)
            default_days = int(days) if days else 30
        else:
            default_days = 30

        default_to = date.today() + timedelta(days=int(default_days) if default_days else 30)
        self.valid_to_entry.insert(0, default_to.strftime("%Y-%m-%d"))
        self.valid_to_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # 重置剩余次数（仅对次卡）
        if card_type == "次卡":
            self.reset_count_var = tk.BooleanVar(value=True)
            self.reset_cb = tk.Checkbutton(fields_frame, text="重置剩余次数为总次数",
                                           font=("微软雅黑", 10),
                                           variable=self.reset_count_var)
            self.reset_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 重置余额（仅对现金卡）
        if card_type == "现金卡":
            self.reset_balance_var = tk.BooleanVar(value=True)
            original_balance = r.get("余额", 0)
            self.reset_cb = tk.Checkbutton(fields_frame, text=f"重置余额为原始金额",
                                           font=("微软雅黑", 10),
                                           variable=self.reset_balance_var)
            self.reset_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(15, 5))

        tk.Button(btn_frame, text="✅ 确认激活", font=("微软雅黑", 11, "bold"),
                  bg="#E67E22", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_activate).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def on_activate(self):
        """确认激活"""
        from datetime import datetime as _dt

        valid_from = self.valid_from_entry.get().strip()
        valid_to = self.valid_to_entry.get().strip()

        # 验证日期
        try:
            _dt.strptime(valid_from, "%Y-%m-%d")
            _dt.strptime(valid_to, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("提示", "日期格式错误，请使用 YYYY-MM-DD")
            return

        r = self.row_data
        card_type = r.get("卡类型", "")

        # 构造更新数据
        update_data = {
            "状态": "有效",
            "有效期起": valid_from,
            "有效期止": valid_to,
        }

        # 次卡：重置剩余次数
        if card_type == "次卡" and getattr(self, 'reset_count_var', None) and self.reset_count_var.get():
            total = int(float(str(r.get("总次数", 0) or 0)))
            update_data["剩余次数"] = total
            update_data["已消耗次数"] = 0

        # 现金卡
        if card_type == "现金卡" and getattr(self, 'reset_balance_var', None) and self.reset_balance_var.get():
            original_price = float(str(r.get("实收金额", 0) or 0))
            update_data["余额"] = original_price
            update_data["已消费金额"] = 0

        # 调用业务层更新
        result = self.biz.reactivate_membership(self.row_num, update_data)

        if result.get("success"):
            self.frame.refresh_and_show(result.get("message", "重新激活成功"))
            self.destroy()
        else:
            messagebox.showerror("错误", result.get("error", "重新激活失败"))
