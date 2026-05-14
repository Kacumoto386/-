"""
会籍卡售卡对话框 - 支持次卡/期限卡/现金卡三种卡类型
售卡时从「可售会籍卡」产品目录中选择卡名称，自动代入参数
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PAYMENT_METHODS


class MembershipDialog(tk.Toplevel):
    """会籍卡售卖对话框"""

    def __init__(self, parent, biz, title, member_data=None, store_mgr=None):
        super().__init__(parent)
        self.biz = biz
        self.member_data = member_data
        self.store_mgr = store_mgr
        self.result = None
        self._product_options = []
        self._selected_product = None

        self.title(title)
        self.geometry("550x580")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.members = self.biz.get_member_id_names()
        self.staff_list = self.biz.get_staff_id_names()

        self.build_ui()
        if self.member_data:
            self._load_member()

    def build_ui(self):
        """构建表单界面"""
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # === 会员信息 ===
        ttk.Label(main, text="● 会员信息", font=("微软雅黑", 11, "bold"),
                  foreground="#1F4E79").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 8))

        ttk.Label(main, text="选择会员：", font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=3)
        member_values = list(self.members.values()) if self.members else ["暂无会员数据"]
        self.member_combo = ttk.Combobox(main, values=member_values,
                                          font=("微软雅黑", 10), width=35, state="readonly")
        self.member_combo.grid(row=1, column=1, sticky=tk.W, pady=3, padx=(5, 0))
        self.member_combo.bind("<<ComboboxSelected>>", self._on_member_select)
        self._member_phone_label = ttk.Label(main, text="", font=("微软雅黑", 9), foreground="#999")
        self._member_phone_label.grid(row=1, column=2, sticky=tk.W, padx=(5, 0), pady=3)

        # === 会籍卡信息 ===
        sep1 = ttk.Separator(main, orient=tk.HORIZONTAL)
        sep1.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=10)

        ttk.Label(main, text="● 会籍卡信息", font=("微软雅黑", 11, "bold"),
                  foreground="#1F4E79").grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))

        # 卡类型
        ttk.Label(main, text="卡类型：", font=("微软雅黑", 10)).grid(row=4, column=0, sticky=tk.W, pady=3)
        self.type_combo = ttk.Combobox(main, values=["次卡", "期限卡", "现金卡"],
                                        font=("微软雅黑", 10), width=35, state="readonly")
        self.type_combo.set("次卡")
        self.type_combo.grid(row=4, column=1, sticky=tk.W, pady=3, padx=(5, 0))
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # 卡名称（从可售会籍卡加载）
        ttk.Label(main, text="卡名称：", font=("微软雅黑", 10)).grid(row=5, column=0, sticky=tk.W, pady=3)
        self.name_combo = ttk.Combobox(main, font=("微软雅黑", 10), width=38, state="readonly")
        self.name_combo.grid(row=5, column=1, sticky=tk.W, pady=3, padx=(5, 0))
        self.name_combo.bind("<<ComboboxSelected>>", self._on_name_select)

        # 动态字段
        self.dynamic_frame = ttk.Frame(main)
        self.dynamic_frame.grid(row=6, column=0, columnspan=3, sticky=tk.EW, pady=5)
        self.dynamic_widgets = {}
        self._build_dynamic_fields("次卡")

        # 销售员工
        ttk.Label(main, text="销售员工：", font=("微软雅黑", 10)).grid(row=7, column=0, sticky=tk.W, pady=3)
        staff_values = list(self.staff_list.values()) if self.staff_list else ["无"]
        self.staff_combo = ttk.Combobox(main, values=staff_values,
                                         font=("微软雅黑", 10), width=35, state="readonly")
        self.staff_combo.grid(row=7, column=1, sticky=tk.W, pady=3, padx=(5, 0))

        # 付款方式
        ttk.Label(main, text="付款方式：", font=("微软雅黑", 10)).grid(row=8, column=0, sticky=tk.W, pady=3)
        self.pay_combo = ttk.Combobox(main, values=PAYMENT_METHODS,
                                       font=("微软雅黑", 10), width=35, state="readonly")
        self.pay_combo.set("微信")
        self.pay_combo.grid(row=8, column=1, sticky=tk.W, pady=3, padx=(5, 0))

        # 开卡日期
        ttk.Label(main, text="开卡日期：", font=("微软雅黑", 10)).grid(row=9, column=0, sticky=tk.W, pady=3)
        today_str = date.today().strftime("%Y-%m-%d")
        self.date_entry = tk.Entry(main, font=("微软雅黑", 10), width=37)
        self.date_entry.insert(0, today_str)
        self.date_entry.grid(row=9, column=1, sticky=tk.W, pady=3, padx=(5, 0))

        # 备注
        ttk.Label(main, text="备  注：", font=("微软雅黑", 10)).grid(row=10, column=0, sticky=tk.W, pady=3)
        self.note_entry = tk.Entry(main, font=("微软雅黑", 10), width=37)
        self.note_entry.grid(row=10, column=1, sticky=tk.W, pady=3, padx=(5, 0))

        # 按钮区
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=11, column=0, columnspan=3, pady=20)

        tk.Button(btn_frame, text="✅ 确认售卡", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _load_member(self):
        """自动填入已选中的会员"""
        mid = self.member_data.get("会员编号", "")
        name = self.member_data.get("姓名", "")
        phone = self.member_data.get("手机号", "")
        for cid, cname in self.members.items():
            if cid == mid:
                self.member_combo.set(cname)
                break
        self._member_phone_label.config(text=f"📞 {phone}")

    def _on_member_select(self, event):
        selected = self.member_combo.get()
        for mid, name in self.members.items():
            if name == selected:
                member = self.biz.get_member(mid)
                if member:
                    phone = member.get("手机号", "")
                    self._member_phone_label.config(text=f"📞 {phone}")
                break

    def _on_type_change(self, event):
        """卡类型切换 - 从可售会籍卡加载该类型的产品"""
        card_type = self.type_combo.get()
        self._build_dynamic_fields(card_type)

        store_id = None
        if self.store_mgr:
            store = self.store_mgr.get_current_store()
            if store:
                store_id = store.get("store_id", "")

        self._product_options = self.biz.get_card_product_options(card_type, store_id)
        labels = [opt[2] for opt in self._product_options]
        if not labels:
            labels = ["（暂无可售会籍卡，请先设置）"]
        self.name_combo["values"] = labels
        self.name_combo.set("")
        self._selected_product = None

    def _build_dynamic_fields(self, card_type):
        """根据卡类型构建动态字段"""
        for w in self.dynamic_widgets.values():
            w.destroy()
        self.dynamic_widgets.clear()

        if card_type == "次卡":
            self._add_dynamic_field("总次数：", 0, "0", is_number=True)
            self._add_dynamic_field("售价(元)：", 1, "0")
            self._add_dynamic_field("实收金额：", 2, "0")
            self._add_dynamic_field("有效期起：", 3, date.today().strftime("%Y-%m-%d"))
            self._add_dynamic_field("有效期止：", 4, "")

        elif card_type == "期限卡":
            self._add_dynamic_field("有效天数：", 0, "30", is_number=True)
            self._add_dynamic_field("售价(元)：", 1, "0")
            self._add_dynamic_field("实收金额：", 2, "0")
            self._add_dynamic_field("有效期起：", 3, date.today().strftime("%Y-%m-%d"))
            self._add_dynamic_field("有效期止：", 4, "", readonly=True)
            if "有效天数" in self.dynamic_widgets:
                self.dynamic_widgets["有效天数"].bind("<KeyRelease>", self._calc_period_end)
            if "有效期起" in self.dynamic_widgets:
                self.dynamic_widgets["有效期起"].bind("<KeyRelease>", self._calc_period_end)

        elif card_type == "现金卡":
            self._add_dynamic_field("售价(元)：", 0, "0")
            self._add_dynamic_field("实收金额：", 1, "0")
            self._add_dynamic_field("卡内余额：", 2, "0")

    def _add_dynamic_field(self, label, row_idx, default="", is_number=False, readonly=False):
        """添加动态字段"""
        ttk.Label(self.dynamic_frame, text=label, font=("微软雅黑", 10)) \
            .grid(row=row_idx, column=0, sticky=tk.W, pady=3)

        if readonly:
            w = tk.Entry(self.dynamic_frame, font=("微软雅黑", 10), width=35, state="readonly")
        else:
            w = tk.Entry(self.dynamic_frame, font=("微软雅黑", 10), width=37)
        w.grid(row=row_idx, column=1, sticky=tk.W, pady=3, padx=(5, 0))

        if default:
            w.insert(0, default)

        self.dynamic_widgets[label] = w

    def _calc_period_end(self, event=None):
        """计算期限卡有效期止"""
        try:
            days = int(self.dynamic_widgets["有效天数"].get() or 0)
            from_str = self.dynamic_widgets["有效期起"].get()
            from_date = datetime.strptime(from_str, "%Y-%m-%d").date() if from_str else date.today()
            end_date = from_date + timedelta(days=days - 1)
            end_w = self.dynamic_widgets.get("有效期止")
            if end_w:
                end_w.config(state="normal")
                end_w.delete(0, tk.END)
                end_w.insert(0, end_date.strftime("%Y-%m-%d"))
                end_w.config(state="readonly")
        except (ValueError, TypeError):
            pass

    def _on_name_select(self, event):
        """卡名称选中 - 从可售会籍卡产品自动填入参数"""
        label = self.name_combo.get()
        if not label or label.startswith("（暂无可售"):
            return

        self._selected_product = None
        for pid, pname, plabel, pdata in self._product_options:
            if plabel == label:
                self._selected_product = pdata
                break

        if not self._selected_product:
            return

        p = self._selected_product
        card_type = self.type_combo.get()
        price = float(p.get("标准售价", 0))
        display_price = str(int(price)) if price == int(price) else f"{price:.2f}"

        price_key = "售价(元)"
        amount_key = "实收金额"
        if price_key in self.dynamic_widgets:
            w = self.dynamic_widgets[price_key]
            w.delete(0, tk.END)
            w.insert(0, display_price)
        if amount_key in self.dynamic_widgets:
            w = self.dynamic_widgets[amount_key]
            w.delete(0, tk.END)
            w.insert(0, display_price)

        if card_type == "次卡" and "总次数" in self.dynamic_widgets:
            count = int(p.get("总次数", 0))
            if count > 0:
                self.dynamic_widgets["总次数"].delete(0, tk.END)
                self.dynamic_widgets["总次数"].insert(0, str(count))

        if card_type == "期限卡" and "有效天数" in self.dynamic_widgets:
            days = int(p.get("有效天数", 0))
            if days > 0:
                self.dynamic_widgets["有效天数"].delete(0, tk.END)
                self.dynamic_widgets["有效天数"].insert(0, str(days))

        if card_type == "现金卡" and "卡内余额" in self.dynamic_widgets:
            amount = float(p.get("储值金额", 0))
            if amount > 0:
                disp = str(int(amount)) if amount == int(amount) else f"{amount:.2f}"
                self.dynamic_widgets["卡内余额"].delete(0, tk.END)
                self.dynamic_widgets["卡内余额"].insert(0, disp)

    def on_save(self):
        """保存售卡"""
        member_name = self.member_combo.get()
        card_type = self.type_combo.get()
        card_name = self.name_combo.get()

        if not member_name:
            messagebox.showwarning("提示", "请选择会员")
            return
        if not card_name or card_name.startswith("（暂无可售"):
            messagebox.showwarning("提示", "请选择卡名称")
            return

        member_id = ""
        for mid, name in self.members.items():
            if name == member_name:
                member_id = mid
                break

        member_phone = ""
        member = self.biz.get_member(member_id)
        if member:
            member_phone = member.get("手机号", "")

        staff_name = self.staff_combo.get()
        pay_method = self.pay_combo.get()

        # 从产品获取卡名称（去除编号和价格后缀）
        card_display_name = card_name
        if self._selected_product:
            card_display_name = self._selected_product.get("卡名称", card_name)

        try:
            data = {
                "会员编号": member_id,
                "会员姓名": member_name.split(" - ")[-1] if " - " in member_name else member_name,
                "会员手机号": member_phone,
                "卡类型": card_type,
                "卡名称": card_display_name,
                "付款方式": pay_method,
                "销售员工": staff_name,
                "开卡日期": self.date_entry.get().strip(),
                "备注": self.note_entry.get().strip(),
            }

            if card_type == "次卡":
                data["总次数"] = self._safe_int(self._get_dynamic("总次数：", 0))
                data["售价"] = self._safe_float(self._get_dynamic("售价(元)：", 0))
                data["实收金额"] = self._safe_float(self._get_dynamic("实收金额：", 0))
                data["有效期起"] = self._get_dynamic("有效期起：", date.today().strftime("%Y-%m-%d"))
                data["有效期止"] = self._get_dynamic("有效期止：", "")

            elif card_type == "期限卡":
                data["有效天数"] = self._safe_int(self._get_dynamic("有效天数：", 30))
                data["售价"] = self._safe_float(self._get_dynamic("售价(元)：", 0))
                data["实收金额"] = self._safe_float(self._get_dynamic("实收金额：", 0))
                data["有效期起"] = self._get_dynamic("有效期起：", date.today().strftime("%Y-%m-%d"))

            elif card_type == "现金卡":
                data["售价"] = self._safe_float(self._get_dynamic("售价(元)：", 0))
                data["实收金额"] = self._safe_float(self._get_dynamic("实收金额：", 0))
                data["余额"] = self._safe_float(self._get_dynamic("卡内余额：", 0))

            result = self.biz.add_membership(data)
            if result.get("success"):
                messagebox.showinfo("成功", result.get("message", "操作成功"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("error", "未知错误"))

        except Exception as e:
            messagebox.showerror("错误", f"售卡失败: {str(e)}")

    def _get_dynamic(self, key, default=""):
        w = self.dynamic_widgets.get(key)
        if w:
            try:
                return w.get().strip()
            except tk.TclError:
                return default
        return default

    def _safe_int(self, val):
        try:
            return int(val) if val else 0
        except (ValueError, TypeError):
            return 0

    def _safe_float(self, val):
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0
