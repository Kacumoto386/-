"""
售课记录管理模块 V2.14.2
- 修复"重新激活"按钮不显示的问题
- 按钮搜索逻辑从 3 层嵌套改为 2 层，能正确找到 btn_frame
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from gui.base_frame import BaseDataFrame


class SaleFrame(BaseDataFrame):
    """售课记录"""

    def __init__(self, parent, biz):
        self.store_mgr = getattr(biz, 'store_mgr', None)
        display_cols = [
            ("售课编号", 160), ("售课日期", 100), ("销售员工", 80),
            ("会员姓名", 80), ("课程名称", 120),
            ("购买课时数", 80), ("实收金额", 80),
            ("付款方式", 80), ("课时有效期(天)", 100),
            ("有效期截止日", 110), ("售课状态", 80), ("购课来源", 100),
        ]
        super().__init__(parent, biz, "💰 售课记录管理", "sale", display_cols)
        self._add_reactivate_btn()
        # 标记过期行
        self._apply_expiry_tags()

    def _add_reactivate_btn(self):
        """在工具栏追加重新激活按钮"""
        try:
            import tkinter as tk
            for child in self.winfo_children():
                if isinstance(child, ttk.Frame):
                    for sub in child.winfo_children():
                        if isinstance(sub, ttk.Frame):
                            # 找到左侧按钮组(btn_frame)，在其末尾插入重新激活按钮
                            btn = tk.Button(
                                sub, text="🔄 重新激活",
                                font=("微软雅黑", 10),
                                bg="#E67E22", fg="white",
                                padx=12, pady=3, bd=0, cursor="hand2",
                                command=self.on_reactivate)
                            btn.pack(side=tk.LEFT, padx=2)
                            return
        except Exception:
            pass

    def _apply_expiry_tags(self):
        """为过期售课行添加颜色标记"""
        try:
            self.tree.tag_configure("expired", foreground="#FF0000")
            self.tree.tag_configure("active", foreground="#008000")
            self.tree.tag_configure("no_limit", foreground="#666666")
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if len(values) > 10:
                    status = values[10] if len(values) > 10 else ""  # 售课状态在第11列（索引10）
                    if status == "已过期":
                        self.tree.item(item, tags=("expired",))
                    elif status == "有效":
                        self.tree.item(item, tags=("active",))
                    elif status == "无期限":
                        self.tree.item(item, tags=("no_limit",))
        except Exception:
            pass

    def _populate_tree(self, data=None):
        """覆写：填充表格后应用过期标记"""
        super()._populate_tree(data)
        self._apply_expiry_tags()

    def refresh_data(self):
        """覆写：刷新数据前检查过期状态"""
        try:
            # 先执行过期检查（标记过期售课，写入"售课状态"列）
            self.biz.check_sale_expiry()
            # 同步更新课程包状态
            self.biz.update_package_status()
        except Exception:
            pass
        # 再刷新
        self.row_data = self._fetch_data()
        self._populate_tree()

    def _fetch_data(self):
        return self.biz.get_all_sales()

    def on_add(self):
        dialog = SaleDialog(self.winfo_toplevel(), self.biz, "新增售课记录", store_mgr=self.store_mgr)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = SaleDialog(self.winfo_toplevel(), self.biz, "编辑售课记录", row, store_mgr=self.store_mgr)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        sale_id = row.get("售课编号", "")
        if messagebox.askyesno("确认删除", f"确定要删除售课记录 {sale_id} 吗？\n此操作不可恢复！"):
            result = self.biz.delete_sale(row["_row"])
            messagebox.showinfo("提示", result.get("message", "操作成功"))
            self.refresh_data()

    def on_reactivate(self):
        """重新激活已过期的售课记录"""
        row = self.get_selected_row()
        if not row:
            return

        sale_id = row.get("售课编号", "")
        expiry = row.get("有效期截止日", "")
        if hasattr(expiry, 'strftime'):
            expiry = expiry.strftime("%Y-%m-%d")

        from datetime import date, timedelta
        default_new_expiry = (date.today() + timedelta(days=180)).strftime("%Y-%m-%d")

        dialog = ReactivateSaleDialog(self.winfo_toplevel(), self.biz,
                                      sale_id, row["_row"],
                                      old_expiry=str(expiry)[:10] if expiry else "无",
                                      default_new=default_new_expiry,
                                      on_done=self.refresh_data)
        self.winfo_toplevel().wait_window(dialog)


class SaleDialog(tk.Toplevel):
    """售课新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None, store_mgr=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.store_mgr = store_mgr
        self.title(title)
        self.geometry("600x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # 加载关联数据
        self.members = self.biz.get_member_id_names()
        self.staff_list = self.biz.get_staff_id_names()
        self.courses = self.biz.get_course_id_names()

        self.build_ui()
        if self.is_edit:
            self.load_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 会员选择
        ttk.Label(main, text="选择会员：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=4)
        member_values = list(self.members.values()) if self.members else ["暂无会员数据"]
        self.member_combo = ttk.Combobox(main, values=member_values, font=("微软雅黑", 10), width=35, state="readonly")
        self.member_combo.grid(row=0, column=1, sticky=tk.W, pady=4, padx=(5, 0))
        self.member_combo.bind("<<ComboboxSelected>>", self._on_member_select)

        # 销售员工
        ttk.Label(main, text="销售员工：", font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=4)
        staff_values = list(self.staff_list.values()) if self.staff_list else ["无"]
        self.staff_combo = ttk.Combobox(main, values=staff_values, font=("微软雅黑", 10), width=35, state="readonly")
        self.staff_combo.grid(row=1, column=1, sticky=tk.W, pady=4, padx=(5, 0))

        # 课程选择
        ttk.Label(main, text="选择课程：", font=("微软雅黑", 10)).grid(row=2, column=0, sticky=tk.W, pady=4)
        course_values = list(self.courses.values()) if self.courses else ["暂无课程"]
        self.course_combo = ttk.Combobox(main, values=course_values, font=("微软雅黑", 10), width=35, state="readonly")
        self.course_combo.grid(row=2, column=1, sticky=tk.W, pady=4, padx=(5, 0))
        self.course_combo.bind("<<ComboboxSelected>>", self._on_course_select)

        # 售课信息
        ttk.Separator(main, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=10)

        self.fields = {}
        field_list = [
            ("购买课时数", tk.Entry, {}, "10"),
            ("赠送课时数", tk.Entry, {}, "0"),
            ("单价", tk.Entry, {}, "0"),
            ("折扣", tk.Entry, {}, "1.0"),
            ("实收金额", tk.Entry, {}),
            ("付款方式", ttk.Combobox, {"values": ["微信", "支付宝", "现金", "银行卡", "对公转账", "储值卡扣款"], "state": "readonly"}),
            ("购课来源", ttk.Combobox, {"values": ["新客到店", "转介绍", "线上推广", "地推", "老客续费", "活动促销"], "state": "readonly"}),
        ]

        for i, (label, wtype, opts, *default) in enumerate(field_list):
            row = i + 4
            ttk.Label(main, text=label + "：", font=("微软雅黑", 10)).grid(row=row, column=0, sticky=tk.W, pady=4)
            if wtype == ttk.Combobox:
                w = wtype(main, font=("微软雅黑", 10), width=35, **opts)
            else:
                w = wtype(main, font=("微软雅黑", 10), width=37)
            w.grid(row=row, column=1, sticky=tk.W, pady=4, padx=(5, 0))
            if default:
                w.insert(0, default[0])
            self.fields[label] = w

        # 设置默认值
        self.fields["付款方式"].set("微信")
        self.fields["购课来源"].set("新客到店")

        # 实时计算
        self.fields["购买课时数"].bind("<KeyRelease>", self._calc_amount)
        self.fields["单价"].bind("<KeyRelease>", self._calc_amount)
        self.fields["折扣"].bind("<KeyRelease>", self._calc_amount)

        # 来源信息
        entry_frame = ttk.Frame(main)
        entry_frame.grid(row=len(field_list) + 4, column=0, columnspan=2, pady=10)

        ttk.Label(entry_frame, text=f"售课日期：{date.today().strftime('%Y-%m-%d')}",
                  font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=10)

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(field_list) + 5, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _on_member_select(self, event):
        """会员选中事件"""
        pass

    def _on_course_select(self, event):
        """课程选中事件 - 自动填入价格"""
        selected = self.course_combo.get()
        for cid, name in self.courses.items():
            if name == selected:
                course = self.biz.get_course(cid)
                if course:
                    price = course.get("标准售价", 0)
                    self.fields["单价"].delete(0, tk.END)
                    self.fields["单价"].insert(0, str(int(price)))
                    self._calc_amount()
                break

    def _calc_amount(self, event=None):
        """计算折后总价和实收金额"""
        try:
            qty = float(self.fields["购买课时数"].get() or 0)
            price = float(self.fields["单价"].get() or 0)
            discount = float(self.fields["折扣"].get() or 1)
            total = qty * price * discount
            self.fields["实收金额"].delete(0, tk.END)
            self.fields["实收金额"].insert(0, f"{total:.2f}")
        except (ValueError, TypeError):
            pass

    def load_data(self):
        """加载现有数据到表单"""
        from datetime import date, datetime

        # 设置会员
        member_id = self.data.get("会员编号", "")
        member_val = self.members.get(member_id, "")
        if member_val:
            self.member_combo.set(member_val)

        # 设置员工
        staff_name = self.data.get("销售员工", "")
        if staff_name and staff_name in self.staff_list.values():
            self.staff_combo.set(staff_name)

        # 设置课程
        course_id = self.data.get("课程编号", "")
        course_val = self.courses.get(course_id, "")
        if course_val:
            self.course_combo.set(course_val)

        # 设置字段
        field_map = {
            "购买课时数": "购买课时数",
            "赠送课时数": "赠送课时数",
            "单价": "单价",
            "折扣": "折扣",
            "实收金额": "实收金额",
        }
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if val is not None:
                w = self.fields[label]
                w.delete(0, tk.END)
                w.insert(0, str(val))

        # 设置下拉字段
        pay_method = self.data.get("付款方式", "")
        if pay_method in ["微信", "支付宝", "现金", "银行卡", "对公转账", "储值卡扣款"]:
            self.fields["付款方式"].set(pay_method)

        sale_source = self.data.get("购课来源", "")
        if sale_source in ["新客到店", "转介绍", "线上推广", "地推", "老客续费", "活动促销"]:
            self.fields["购课来源"].set(sale_source)

    def on_save(self):
        """保存售课记录"""
        member_name = self.member_combo.get()
        staff_name = self.staff_combo.get()
        course_name = self.course_combo.get()

        if not member_name or not course_name:
            messagebox.showwarning("提示", "请选择会员和课程")
            return

        # 解析会员编号
        member_id = ""
        for mid, name in self.members.items():
            if name == member_name:
                member_id = mid
                break

        # 获取课程编号
        course_id = ""
        for cid, name in self.courses.items():
            if name == course_name:
                course_id = cid
                break

        try:
            data = {
                "会员编号": member_id,
                "会员姓名": member_name.split(" - ")[-1] if " - " in member_name else member_name,
                "课程编号": course_id,
                "课程名称": course_name.split(" - ")[-1] if " - " in course_name else course_name,
                "销售员工": staff_name,
                "销售员姓名": staff_name.split(" - ")[-1] if " - " in staff_name else staff_name,
                "购买课时数": int(self.fields["购买课时数"].get() or 0),
                "赠送课时数": int(self.fields["赠送课时数"].get() or 0),
                "单价": float(self.fields["单价"].get() or 0),
                "折扣": float(self.fields["折扣"].get() or 1),
                "实收金额": float(self.fields["实收金额"].get() or 0),
                "付款方式": self.fields["付款方式"].get(),
                "购课来源": self.fields["购课来源"].get(),
                "销售提成比例": 0.08,
            }
            if self.is_edit:
                result = self.biz.update_sale(self.data["_row"], data)
            else:
                result = self.biz.add_sale(data)
            if result["success"]:
                # 自动绑定门店映射：找会员绑在哪个门店，售课就绑过去
                if self.store_mgr and member_id:
                    sale_id = result.get("sale_id", "")
                    if sale_id:
                        from config import STORE_MAP_SHEET
                        all_maps = self.biz.engine.get_all_data(STORE_MAP_SHEET)
                        store_id = None
                        for mp in all_maps:
                            if isinstance(mp, dict) and mp.get("数据类型") == "member" and mp.get("数据编号") == member_id:
                                store_id = mp.get("门店编号", "")
                                break
                        if store_id:
                            self.store_mgr.map_data_to_store("sale", sale_id, store_id)

                messagebox.showinfo("成功", result.get("message", "操作成功"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("message", "操作成功"))
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")


class ReactivateSaleDialog(tk.Toplevel):
    """售课记录重新激活对话框（V2.14.1 - 新增预设选项）"""

    def __init__(self, parent, biz, sale_id, row_num, old_expiry="无", default_new="", on_done=None):
        super().__init__(parent)
        self.biz = biz
        self.sale_id = sale_id
        self.row_num = row_num
        self.on_done = on_done

        self.title(f"🔄 重新激活 - {sale_id}")
        self.geometry("460x340")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 信息框
        info_text = f"售课编号：{sale_id}\n当前到期日：{old_expiry}"
        info_label = ttk.Label(main, text=info_text, font=("微软雅黑", 10),
                               justify=tk.LEFT, background="#F9F9F9",
                               relief="solid", padding=10)
        info_label.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(main, text="激活设置", font=("微软雅黑", 11, "bold"),
                  foreground="#1F4E79").pack(anchor=tk.W, pady=(5, 5))

        # 新有效期
        fields_frame = ttk.Frame(main)
        fields_frame.pack(fill=tk.X, pady=5)

        ttk.Label(fields_frame, text="新的到期日期：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.expiry_entry = tk.Entry(fields_frame, font=("微软雅黑", 10), width=25)
        self.expiry_entry.insert(0, default_new)
        self.expiry_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(fields_frame, text="格式：YYYY-MM-DD", font=("微软雅黑", 9),
                  foreground="#999").grid(row=1, column=1, sticky=tk.W, padx=5)

        # 快速预设按钮
        preset_frame = ttk.Frame(main)
        preset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(preset_frame, text="快速预设：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)

        from datetime import date, timedelta
        today = date.today()

        def make_preset(days):
            def set_date():
                new_d = (today + timedelta(days=days)).strftime("%Y-%m-%d")
                self.expiry_entry.delete(0, tk.END)
                self.expiry_entry.insert(0, new_d)
            return set_date

        for label, days in [("1个月", 30), ("3个月", 90), ("6个月", 180), ("1年", 365)]:
            btn = tk.Button(preset_frame, text=label,
                            font=("微软雅黑", 9), bg="#D6E4F0", fg="#1F4E79",
                            padx=8, pady=1, bd=0, cursor="hand2",
                            command=make_preset(days))
            btn.pack(side=tk.LEFT, padx=3)

        # 提示
        ttk.Label(main, text="💡 激活后将同步重置关联课程包的状态和有效期，并标记售课状态为「有效」",
                  font=("微软雅黑", 9), foreground="#666").pack(anchor=tk.W, pady=(10, 5))

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(10, 5))

        tk.Button(btn_frame, text="✅ 确认激活", font=("微软雅黑", 11, "bold"),
                  bg="#E67E22", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_activate).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def on_activate(self):
        new_expiry = self.expiry_entry.get().strip()
        try:
            from datetime import datetime as _dt
            _dt.strptime(new_expiry, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("提示", "日期格式错误，请使用 YYYY-MM-DD")
            return

        result = self.biz.reactivate_sale(self.row_num, new_expiry=new_expiry)
        if result.get("success"):
            messagebox.showinfo("成功", result.get("message", "操作成功"))
            if self.on_done:
                self.on_done()
            self.destroy()
        else:
            messagebox.showerror("错误", result.get("error", "重新激活失败"))
