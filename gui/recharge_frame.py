"""
会员充值管理模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.base_frame import BaseDataFrame


class RechargeFrame(BaseDataFrame):
    """充值管理"""

    def __init__(self, parent, biz):
        display_cols = [
            ("充值编号", 140), ("充值日期", 100), ("会员姓名", 80),
            ("充值金额", 80), ("赠送金额", 80), ("到账金额", 80),
            ("储值余额", 90), ("付款方式", 80),
            ("充值类型", 100), ("经办员工", 80),
        ]
        # 提前初始化统计卡片属性，避免父类 build_ui → refresh_data 时找不到
        self.summary_labels = {}
        super().__init__(parent, biz, "💳 会员充值管理", "recharge", display_cols)

        # 在表格下方添加统计卡片
        self._build_summary_cards()
        # 初次加载后更新卡片数据
        self._update_summary()

    def _build_summary_cards(self):
        """在状态栏下方添加统计卡片"""
        card_frame = tk.Frame(self, bg="#F0F4F8", relief="solid", bd=1,
                              highlightbackground="#D0D8E0", highlightthickness=1)
        card_frame.pack(fill=tk.X, padx=15, pady=(0, 8))

        # 4个统计指标
        self.summary_labels = {}
        items = [
            ("充值总额", "¥0"),
            ("赠送总额", "¥0"),
            ("到账总额", "¥0"),
            ("记录数", "0条"),
        ]
        for i, (label, default) in enumerate(items):
            item_frame = tk.Frame(card_frame, bg="white", relief="solid", bd=1,
                                  highlightbackground="#E0E0E0", highlightthickness=1)
            item_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=6)

            value_lbl = tk.Label(item_frame, text=default, font=("微软雅黑", 16, "bold"),
                                 fg="#ED7D31", bg="white")
            value_lbl.pack(pady=(8, 0))

            title_lbl = tk.Label(item_frame, text=label, font=("微软雅黑", 9),
                                 fg="#666666", bg="white")
            title_lbl.pack(pady=(0, 6))

            self.summary_labels[label] = value_lbl

    def _fetch_data(self):
        return self.biz.get_all_recharges()

    def refresh_data(self):
        """刷新数据并更新统计卡片"""
        super().refresh_data()
        # 统计卡片控件可能在父类 build_ui 之后才创建，如果还未就绪则跳过
        if self.summary_labels:
            self._update_summary()

    def _update_summary(self):
        """根据当前显示数据更新统计卡片"""
        if not self.row_data:
            for k in self.summary_labels:
                self.summary_labels[k].config(text="¥0" if k != "记录数" else "0条")
            return

        total_amount = sum(self._safe_float(r.get("充值金额", 0)) for r in self.row_data)
        total_gift = sum(self._safe_float(r.get("赠送金额", 0)) for r in self.row_data)
        total_arrival = sum(self._safe_float(r.get("到账金额", 0)) for r in self.row_data)
        total_count = len(self.row_data)

        self.summary_labels["充值总额"].config(text=f"¥{total_amount:,.0f}")
        self.summary_labels["赠送总额"].config(text=f"¥{total_gift:,.0f}")
        self.summary_labels["到账总额"].config(text=f"¥{total_arrival:,.0f}")
        self.summary_labels["记录数"].config(text=f"{total_count}条")

    def _safe_float(self, val):
        """安全转为浮点数"""
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0

    def on_add(self):
        dialog = RechargeDialog(self.winfo_toplevel(), self.biz, "新增充值记录")
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = RechargeDialog(self.winfo_toplevel(), self.biz, "编辑充值记录", row)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        recharge_id = row.get("充值编号", "")
        if messagebox.askyesno("确认删除", f"确定要删除充值记录 {recharge_id} 吗？\n此操作不可恢复！"):
            result = self.biz.delete_recharge(row["_row"], recharge_id)
            messagebox.showinfo("提示", result.get("message", "操作成功"))
            self.refresh_data()


class RechargeDialog(tk.Toplevel):
    """充值新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.title(title)
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.members = self.biz.get_member_id_names()
        self.build_ui()
        if self.is_edit:
            self.load_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("选择会员", ttk.Combobox,
             {"values": list(self.members.values()) if self.members else ["无"], "state": "readonly"}),
            ("充值金额", tk.Entry, {}),
            ("赠送金额", tk.Entry, {}),
            ("付款方式", ttk.Combobox,
             {"values": ["微信", "支付宝", "现金", "银行卡", "对公转账"], "state": "readonly"}),
            ("充值类型", ttk.Combobox,
             {"values": ["储值卡充值", "课时包充值", "活动充值"], "state": "readonly"}),
            ("经办员工", tk.Entry, {}),
        ]

        self.widgets = {}
        for i, (label, wtype, opts) in enumerate(fields):
            ttk.Label(main, text=label + "：", font=("微软雅黑", 10)).grid(row=i, column=0, sticky=tk.W, pady=4)
            if wtype == ttk.Combobox:
                w = wtype(main, font=("微软雅黑", 10), width=32, **opts)
            else:
                w = wtype(main, font=("微软雅黑", 10), width=34)
            w.grid(row=i, column=1, sticky=tk.W, pady=4, padx=(5, 0))
            self.widgets[label] = w

        self.widgets["付款方式"].set("微信")
        self.widgets["充值类型"].set("储值卡充值")
        self.widgets["充值金额"].insert(0, "0")
        self.widgets["赠送金额"].insert(0, "0")
        self._update_arrival_preview()

        # 到账金额预览
        self.arrival_label = ttk.Label(main, text="💡 到账金额：¥0.00（充值 + 赠送）",
                                       font=("微软雅黑", 9), foreground="#2E75B6")
        self.arrival_label.grid(row=len(fields), column=0, columnspan=2, pady=2)

        # 实时更新到账预览
        self.widgets["充值金额"].bind("<KeyRelease>", lambda e: self._update_arrival_preview())
        self.widgets["赠送金额"].bind("<KeyRelease>", lambda e: self._update_arrival_preview())

        ttk.Label(main, text=f"📅 充值日期：{date.today().strftime('%Y-%m-%d')}",
                  font=("微软雅黑", 9), foreground="#666666").grid(
            row=len(fields) + 1, column=0, columnspan=2, pady=5)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(fields) + 2, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _update_arrival_preview(self):
        """实时更新到账金额预览"""
        try:
            amount = float(self.widgets["充值金额"].get() or 0)
            gift = float(self.widgets["赠送金额"].get() or 0)
            total = amount + gift
            self.arrival_label.config(text=f"💡 到账金额：¥{total:.2f}（充值 ¥{amount:.0f} + 赠送 ¥{gift:.0f}）")
        except ValueError:
            pass

    def load_data(self):
        """加载现有数据到表单"""
        member_id = self.data.get("会员编号", "")
        member_val = self.members.get(member_id, "")
        if member_val:
            self.widgets["选择会员"].set(member_val)

        field_map = {"充值金额": "充值金额", "赠送金额": "赠送金额", "经办员工": "经办员工"}
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if val is not None:
                w = self.widgets[label]
                w.delete(0, tk.END)
                w.insert(0, str(val))

        pay_method = self.data.get("付款方式", "")
        if pay_method in ["微信", "支付宝", "现金", "银行卡", "对公转账"]:
            self.widgets["付款方式"].set(pay_method)

        recharge_type = self.data.get("充值类型", "")
        if recharge_type in ["储值卡充值", "课时包充值", "活动充值"]:
            self.widgets["充值类型"].set(recharge_type)

        # 编辑时也更新到账预览
        self._update_arrival_preview()

    def on_save(self):
        member_str = self.widgets["选择会员"].get()
        if not member_str:
            messagebox.showwarning("提示", "请选择会员")
            return

        try:
            member_id = next((m for m, n in self.members.items() if n == member_str), "")
            amount = float(self.widgets["充值金额"].get() or 0)
            gift = float(self.widgets["赠送金额"].get() or 0)
            arrival = amount + gift
            data = {
                "会员编号": member_id,
                "会员姓名": member_str.split(" - ")[-1] if " - " in member_str else member_str,
                "充值金额": amount,
                "赠送金额": gift,
                "到账金额": arrival,
                "付款方式": self.widgets["付款方式"].get(),
                "充值类型": self.widgets["充值类型"].get(),
                "经办员工": self.widgets["经办员工"].get(),
            }
            if self.is_edit:
                result = self.biz.update_recharge(self.data["_row"], data)
            else:
                result = self.biz.add_recharge(data)
            if result["success"]:
                messagebox.showinfo("成功", result.get("message", "操作成功"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("message", "操作成功"))
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
