"""
会员管理模块
V2.16.0 - 新增会员照片功能（拍照/上传/删除）
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from gui.base_frame import BaseDataFrame
from gui.membership_dialog import MembershipDialog


class MemberFrame(BaseDataFrame):
    """会员管理"""

    def __init__(self, parent, biz):
        display_cols = [
            ("会员编号", 140), ("姓名", 80), ("性别", 50),
            ("手机号", 120), ("会员等级", 70), ("会员状态", 80),
            ("剩余课时", 80), ("可用课时", 80), ("累计上课次数", 100),
            ("会籍卡(次卡剩余)", 105), ("会籍卡(现金余额)", 115),
            ("会籍卡到期日", 110),
            ("最后上课日期", 110), ("跟进状态", 80), ("备注", 150),
        ]
        super().__init__(parent, biz, "\U0001f464 会员信息管理", "member", display_cols)
        self.store_mgr = None
        self._add_membership_buttons()

    def _add_membership_buttons(self):
        """在工具栏追加会籍卡相关按钮"""
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Frame):
                        btn_frame = sub
                        self.btn_membership_sell = tk.Button(
                            btn_frame, text="\U0001f383 售卡",
                            font=("微软雅黑", 10),
                            bg="#FF6B35", fg="white",
                            padx=12, pady=3, bd=0, cursor="hand2",
                            command=self.on_sell_membership)
                        self.btn_membership_sell.pack(side=tk.LEFT, padx=2)

                        self.btn_membership_view = tk.Button(
                            btn_frame, text="\U0001f4cb 会籍卡",
                            font=("微软雅黑", 10),
                            bg="#9B59B6", fg="white",
                            padx=12, pady=3, bd=0, cursor="hand2",
                            command=self.on_view_memberships)
                        self.btn_membership_view.pack(side=tk.LEFT, padx=2)
                        return

    def on_sell_membership(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = MembershipDialog(self.winfo_toplevel(), self.biz,
                                  f"\U0001f383 售卡 - {row.get('姓名', '')}",
                                  member_data=row, store_mgr=self.store_mgr)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_view_memberships(self):
        row = self.get_selected_row()
        if not row:
            return
        member_id = row.get("会员编号", "")
        member_name = row.get("姓名", "")
        dialog = MembershipListDialog(self.winfo_toplevel(), self.biz,
                                      member_id, member_name)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def _fetch_data(self):
        members = self.biz.get_all_members()
        for m in members:
            mid = m.get("会员编号", "")
            if mid:
                summary = self.biz.get_member_membership_summary(mid)
                m.update(summary)
        return members

    def on_add(self):
        dialog = MemberDialog(self.winfo_toplevel(), self.biz, "新增会员", store_mgr=self.store_mgr)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = MemberDialog(self.winfo_toplevel(), self.biz, "编辑会员", row, store_mgr=self.store_mgr)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        name = row.get("姓名", "")
        member_id = row.get("会员编号", "")
        self.confirm_and_delete(
            delete_func=lambda: self.biz.delete_member(row["_row"], member_id),
            item_desc=f"会员 {name} ({member_id})"
        )

    def on_search(self):
        keyword = self.search_var.get().strip()
        if keyword:
            results = self.biz.search_members(keyword)
            self._populate_tree(results)
        else:
            self.refresh_data()


class MemberDialog(tk.Toplevel):
    """会员新增/编辑对话框（V2.16.0 加入照片功能）"""

    def __init__(self, parent, biz, title, data=None, store_mgr=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.store_mgr = store_mgr
        self.result = None
        self._photo_image = None
        self.current_photo_pil = None
        self._bound_band_id = None  # 当前绑定的手环编号
        self._bound_band_data = None  # 手环完整信息
        self.title(title)
        self.geometry("780x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.build_ui()
        if self.is_edit:
            self.load_data()
        self.load_photo()
        self.load_band_info()

    def build_ui(self):
        """构建界面 — 左照片 + 右表单"""
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 左栏：照片
        left = ttk.Frame(main, width=200)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left.pack_propagate(False)

        ttk.Label(left, text="会员头像", font=("微软雅黑", 10, "bold"),
                  foreground="#555").pack(pady=(0, 8))

        self.photo_canvas = tk.Canvas(left, width=160, height=160,
                                      bg="#F0F0F0", highlightthickness=1,
                                      highlightbackground="#DDD", bd=0)
        self.photo_canvas.pack()
        self._draw_placeholder()

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        self.btn_capture = tk.Button(btn_frame, text="\U0001f4f7 拍照",
                                     font=("微软雅黑", 9),
                                     bg="#4472C4", fg="white",
                                     padx=8, pady=2, bd=0, cursor="hand2",
                                     command=self._on_capture)
        self.btn_capture.pack(side=tk.LEFT, padx=2)

        self.btn_upload = tk.Button(btn_frame, text="\U0001f4c1 上传",
                                    font=("微软雅黑", 9),
                                    bg="#27AE60", fg="white",
                                    padx=8, pady=2, bd=0, cursor="hand2",
                                    command=self._on_upload)
        self.btn_upload.pack(side=tk.LEFT, padx=2)

        self.btn_del_photo = tk.Button(btn_frame, text="\U0001f5d1 删除",
                                       font=("微软雅黑", 9),
                                       bg="#E74C3C", fg="white",
                                       padx=8, pady=2, bd=0, cursor="hand2",
                                       command=self._on_delete_photo)
        self.btn_del_photo.pack(side=tk.LEFT, padx=2)

        # ── 手环绑定区 ──
        band_sep = ttk.Separator(left, orient=tk.HORIZONTAL)
        band_sep.pack(fill=tk.X, pady=(15, 8))

        band_header = ttk.Label(left, text="\U0001f3f7 手环绑定",
                                font=("微软雅黑", 9, "bold"), foreground="#555")
        band_header.pack()

        self.band_info_var = tk.StringVar(value="未绑定手环")
        band_info_label = ttk.Label(left, textvariable=self.band_info_var,
                                    font=("微软雅黑", 8), foreground="#777",
                                    wraplength=180)
        band_info_label.pack(pady=(3, 5))

        band_btn_frame = ttk.Frame(left)
        band_btn_frame.pack(fill=tk.X)

        self.btn_bind_band = tk.Button(band_btn_frame, text="\U0001f3af 绑定手环",
                                       font=("微软雅黑", 8),
                                       bg="#27AE60", fg="white",
                                       padx=6, pady=1, bd=0, cursor="hand2",
                                       command=self._on_bind_band)
        self.btn_bind_band.pack(side=tk.LEFT, padx=2)

        self.btn_unbind_band = tk.Button(band_btn_frame, text="\U0001f517 解绑",
                                         font=("微软雅黑", 8),
                                         bg="#E67E22", fg="white",
                                         padx=6, pady=1, bd=0, cursor="hand2",
                                         command=self._on_unbind_band)
        self.btn_unbind_band.pack(side=tk.LEFT, padx=2)

        # 右栏：表单
        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        fields = [
            ("姓名", tk.Entry, {}),
            ("性别", ttk.Combobox, {"values": ["男", "女"], "state": "readonly"}),
            ("手机号", tk.Entry, {}),
            ("生日", tk.Entry, {}),
            ("邮箱", tk.Entry, {}),
            ("会员等级", ttk.Combobox, {"values": ["普通", "银卡", "金卡", "钻石"], "state": "readonly"}),
            ("入会日期", tk.Entry, {}),
            ("跟进状态", ttk.Combobox, {"values": ["正常", "需回访", "流失预警", "已流失"], "state": "readonly"}),
            ("介绍人", tk.Entry, {}),
            ("备注", tk.Entry, {}),
        ]

        self.widgets = {}
        for i, (label, widget_type, options) in enumerate(fields):
            ttk.Label(right, text=label + "\uff1a",
                      font=("微软雅黑", 10)).grid(row=i, column=0, sticky=tk.W, pady=4)

            if widget_type == ttk.Combobox:
                w = widget_type(right, font=("微软雅黑", 10), width=30, **options)
            else:
                w = widget_type(right, font=("微软雅黑", 10), width=32)
            w.grid(row=i, column=1, sticky=tk.W, pady=4, padx=(5, 0))
            self.widgets[label] = w

        if not self.is_edit:
            self.widgets["性别"].set("男")
            self.widgets["会员等级"].set("普通")
            self.widgets["跟进状态"].set("正常")
            self.widgets["入会日期"].insert(0, date.today().strftime("%Y-%m-%d"))
            self.widgets["生日"].insert(0, "1990-01-01")

        # 门店
        store_label = ttk.Label(right, text="所属门店：", font=("微软雅黑", 10))
        store_label.grid(row=len(fields), column=0, sticky=tk.W, pady=4)

        store_frame = ttk.Frame(right)
        store_frame.grid(row=len(fields), column=1, sticky=tk.W, pady=4, padx=(5, 0))

        self.store_listbox = tk.Listbox(store_frame, height=3, selectmode=tk.MULTIPLE,
                                        font=("微软雅黑", 9), width=35, exportselection=False)
        self.store_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        store_scroll = ttk.Scrollbar(store_frame, orient=tk.VERTICAL, command=self.store_listbox.yview)
        store_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.store_listbox.configure(yscrollcommand=store_scroll.set)

        self.store_items = []
        if self.store_mgr:
            stores = self.store_mgr.get_all_stores()
            for s in stores:
                sid = s.get("门店编号", "")
                sname = s.get("门店名称", "")
                if sid and sname:
                    self.store_items.append((sid, sname))
                    self.store_listbox.insert(tk.END, f"{sname} ({sid})")

        # 按钮
        btn2 = ttk.Frame(right)
        btn2.grid(row=len(fields) + 1, column=0, columnspan=2, pady=15)
        tk.Button(btn2, text="保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn2, text="取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    # ── 照片操作 ──

    def _draw_placeholder(self):
        self.photo_canvas.delete("all")
        c = self.photo_canvas
        c.create_text(80, 70, text="\U0001f464", font=("微软雅黑", 48), fill="#BBB")
        c.create_text(80, 130, text="暂无头像", font=("微软雅黑", 9), fill="#AAA")

    def _display_photo(self, pil_image):
        self.current_photo_pil = pil_image
        if pil_image is None:
            self._draw_placeholder()
            return
        from utils.photo_utils import make_circular_photo
        photo = make_circular_photo(pil_image, diameter=140)
        self._photo_image = photo
        self.photo_canvas.delete("all")
        self.photo_canvas.create_image(80, 80, image=photo)

    def load_photo(self):
        if not self.is_edit:
            return
        member_id = self.data.get("会员编号", "")
        if not member_id:
            return
        from utils.photo_utils import get_photo_path, load_photo_for_display
        if get_photo_path(member_id):
            _, pil_img = load_photo_for_display(member_id, display_size=(200, 200))
            if pil_img:
                self._display_photo(pil_img)

    def _on_capture(self):
        from utils.photo_utils import capture_from_camera
        img = capture_from_camera(parent_window=self)
        if img:
            self._display_photo(img)

    def _on_upload(self):
        from utils.photo_utils import pick_from_file
        img = pick_from_file(parent_window=self)
        if img:
            self._display_photo(img)

    def _on_delete_photo(self):
        if self.is_edit:
            if not messagebox.askyesno("确认删除", "确定要删除该会员的头像吗？", parent=self):
                return
            member_id = self.data.get("会员编号", "")
            if member_id:
                from utils.photo_utils import delete_photo
                delete_photo(member_id)
                self.biz.update_member_photo_path(self.data["_row"], "")
        self._display_photo(None)

    # ── 手环绑定 ──

    def load_band_info(self):
        """加载会员的手环绑定信息"""
        member_id = self.data.get("会员编号", "") if self.data else ""
        if not member_id:
            return
        band = self.biz.get_member_wristband(member_id)
        if band:
            self._bound_band_id = band.get("手环编号", "")
            self._bound_band_data = band
            self.band_info_var.set(
                f"手环: {band.get('手环编号','')}\n"
                f"读卡器: {band.get('读卡器写入值','')}\n"
                f"自定义: {band.get('自定义编号','')}"
            )
            self.btn_bind_band.configure(state=tk.DISABLED)
            self.btn_unbind_band.configure(state=tk.NORMAL)
        else:
            self._bound_band_id = None
            self._bound_band_data = None
            self.band_info_var.set("未绑定手环")
            self.btn_bind_band.configure(state=tk.NORMAL)
            self.btn_unbind_band.configure(state=tk.DISABLED)

    def _on_bind_band(self):
        """绑定手环：弹出未绑定手环列表供选择"""
        bands = self.biz.get_unbound_wristbands()
        if not bands:
            messagebox.showinfo("提示", "没有可用的未绑定手环，请先在手环管理中注册", parent=self)
            return

        dialog = BandSelectDialog(self, self.biz, bands)
        self.wait_window(dialog)

        selected_band_id = getattr(dialog, 'selected_band_id', None)
        if selected_band_id:
            member_id = self.data.get("会员编号", "")
            member_name = self.data.get("姓名", "")
            result = self.biz.bind_wristband(selected_band_id, member_id, member_name)
            if result["success"]:
                messagebox.showinfo("成功", result["message"], parent=self)
                self.load_band_info()
            else:
                messagebox.showerror("错误", result.get("message", "绑定失败"), parent=self)

    def _on_unbind_band(self):
        """解绑手环"""
        if not self._bound_band_id:
            return
        if not messagebox.askyesno("确认解绑", f"确定要解绑手环 {self._bound_band_id} 吗？", parent=self):
            return
        member_id = self.data.get("会员编号", "")
        result = self.biz.unbind_wristband(self._bound_band_id, member_id)
        if result["success"]:
            messagebox.showinfo("成功", result["message"], parent=self)
            self.load_band_info()
        else:
            messagebox.showerror("错误", result.get("message", "解绑失败"), parent=self)

    # ── 表单 ──

    def load_data(self):
        field_map = {
            "姓名": "姓名", "性别": "性别", "手机号": "手机号",
            "生日": "生日", "邮箱": "邮箱", "会员等级": "会员等级",
            "入会日期": "入会日期", "跟进状态": "跟进状态",
            "介绍人": "介绍人", "备注": "备注",
        }
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if isinstance(val, (date, datetime)):
                val = val.strftime("%Y-%m-%d")
            if val:
                w = self.widgets[label]
                if isinstance(w, ttk.Combobox):
                    w.set(str(val))
                else:
                    w.delete(0, tk.END)
                    w.insert(0, str(val))

        if self.store_mgr and self.data:
            member_id = self.data.get("会员编号", "")
            if member_id:
                mapped = self.store_mgr.get_data_ids_for_store(None, "member")
                member_maps = [m for m in mapped if m.get("数据编号") == member_id]
                mapped_store_ids = set(m.get("门店编号", "") for m in member_maps)
                for idx, (sid, _) in enumerate(self.store_items):
                    if sid in mapped_store_ids:
                        self.store_listbox.selection_set(idx)

    def get_form_data(self):
        data = {}
        for label, w in self.widgets.items():
            val = w.get()
            if isinstance(w, tk.Entry):
                val = val.strip()
            if label in ("生日", "入会日期") and val:
                try:
                    val = datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    val = date.today()
            elif label == "会员等级":
                if val not in ("普通", "银卡", "金卡", "钻石"):
                    val = "普通"
            elif label == "跟进状态":
                if val not in ("正常", "需回访", "流失预警", "已流失"):
                    val = "正常"
            data[label] = val
        return {
            "姓名": data.get("姓名", ""),
            "性别": data.get("性别", ""),
            "手机号": data.get("手机号", ""),
            "生日": data.get("生日", date.today()),
            "邮箱": data.get("邮箱", ""),
            "会员等级": data.get("会员等级", "普通"),
            "入会日期": data.get("入会日期", date.today()),
            "跟进状态": data.get("跟进状态", "正常"),
            "介绍人": data.get("介绍人", ""),
            "备注": data.get("备注", ""),
        }

    def on_save(self):
        form_data = self.get_form_data()
        if not form_data["姓名"]:
            messagebox.showwarning("提示", "姓名不能为空")
            return
        if not form_data["手机号"]:
            messagebox.showwarning("提示", "手机号不能为空")
            return

        try:
            if self.is_edit:
                result = self.biz.update_member(self.data["_row"], form_data)
            else:
                result = self.biz.add_member(form_data)

            if result["success"]:
                # 保存照片
                if self.current_photo_pil is not None:
                    member_id = result.get("member_id", "")
                    if not member_id:
                        members = self.biz.search_members(form_data["姓名"])
                        if members:
                            member_id = members[0].get("会员编号", "")
                    if member_id:
                        from utils.photo_utils import save_photo, get_photo_rel_path
                        save_photo(member_id, self.current_photo_pil)
                        rel_path = get_photo_rel_path(member_id)
                        if self.is_edit:
                            self.biz.update_member_photo_path(self.data["_row"], rel_path)
                        else:
                            m = self.biz.get_member(member_id)
                            if m:
                                self.biz.update_member_photo_path(m["_row"], rel_path)

                if self.store_mgr:
                    member_id = result.get("member_id", "") or form_data.get("会员编号", "")
                    if not member_id:
                        members = self.biz.search_members(form_data["姓名"])
                        if members:
                            member_id = members[0].get("会员编号", "")
                    if member_id:
                        self.store_mgr.remove_mapping("member", member_id)
                        selected_indices = self.store_listbox.curselection()
                        for idx in selected_indices:
                            sid, _ = self.store_items[idx]
                            self.store_mgr.map_data_to_store("member", member_id, sid)

                messagebox.showinfo("成功", result.get("message", "操作成功"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("message", "操作成功"))
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")


class MembershipListDialog(tk.Toplevel):
    """会籍卡列表弹窗"""

    def __init__(self, parent, biz, member_id, member_name):
        super().__init__(parent)
        self.biz = biz
        self.member_id = member_id
        self.member_name = member_name
        self.title(f"\U0001f4cb 会籍卡 - {member_name}")
        self.geometry("850x450")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, text=f"\U0001f4cb {self.member_name} 的会籍卡",
                  font=("微软雅黑", 14, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)
        tk.Button(header, text="\U0001f383 新售会籍卡", font=("微软雅黑", 10),
                  bg="#FF6B35", fg="white", padx=12, pady=2, bd=0, cursor="hand2",
                  command=self._on_sell_new).pack(side=tk.RIGHT)

        table_frame = ttk.Frame(main)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ["会籍卡编号", "卡类型", "卡名称", "状态",
                    "总次数", "剩余次数", "余额", "售价",
                    "开卡日期", "有效期起", "有效期止", "销售员工"]
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")
        col_widths = [140, 60, 100, 60, 60, 60, 60, 60, 90, 90, 90, 80]
        for col, w in zip(columns, col_widths):
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

        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, pady=10)

        self.btn_refund = tk.Button(action_frame, text="\U0001f5d1 退费", font=("微软雅黑", 10),
                                    bg="#FF0000", fg="white", padx=15, pady=3, bd=0, cursor="hand2",
                                    command=self._on_refund)
        self.btn_refund.pack(side=tk.LEFT, padx=2)

        self.btn_refresh = tk.Button(action_frame, text="\U0001f504 刷新", font=("微软雅黑", 10),
                                     bg="#E0E0E0", fg="#333333", padx=15, pady=3, bd=0, cursor="hand2",
                                     command=self.refresh_data)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(action_frame, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        tk.Button(action_frame, text="\u274c 关闭", font=("微软雅黑", 10),
                  bg="#E0E0E0", fg="#333333", padx=15, pady=3, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.RIGHT, padx=2)

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        cards = self.biz.get_member_memberships(self.member_id)
        for c in cards:
            valid_start = c.get("有效期起", "")
            valid_end = c.get("有效期止", "")
            if isinstance(valid_start, (date, datetime)):
                valid_start = valid_start.strftime("%Y-%m-%d")
            if isinstance(valid_end, (date, datetime)):
                valid_end = valid_end.strftime("%Y-%m-%d")
            sale_date = c.get("开卡日期", "")
            if isinstance(sale_date, (date, datetime)):
                sale_date = sale_date.strftime("%Y-%m-%d")
            values = [
                c.get("会籍卡编号", ""),
                c.get("卡类型", ""),
                c.get("卡名称", ""),
                c.get("状态", ""),
                c.get("总次数", ""),
                c.get("剩余次数", ""),
                c.get("余额", ""),
                c.get("售价", ""),
                sale_date,
                str(valid_start),
                str(valid_end),
                c.get("销售员工", ""),
            ]
            item = self.tree.insert("", tk.END, values=values)
            status = c.get("状态", "")
            if status == "已退费":
                self.tree.item(item, tags=("refunded",))
            elif status in ("已过期", "已用完"):
                self.tree.item(item, tags=("expired",))
        self.tree.tag_configure("refunded", foreground="#999999")
        self.tree.tag_configure("expired", foreground="#FF0000")
        self.status_label.config(text=f"共 {len(cards)} 张会籍卡")

    def _on_sell_new(self):
        member = self.biz.get_member(self.member_id)
        if not member:
            messagebox.showerror("错误", "未找到会员信息")
            return
        dialog = MembershipDialog(self.winfo_toplevel(), self.biz,
                                  f"\U0001f383 售卡 - {self.member_name}",
                                  member_data=member)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def _on_refund(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一张会籍卡")
            return
        item = selection[0]
        index = self.tree.index(item)
        cards = self.biz.get_member_memberships(self.member_id)
        if index >= len(cards):
            return
        card = cards[index]
        card_id = card.get("会籍卡编号", "")
        status = card.get("状态", "")
        if status == "已退费":
            messagebox.showinfo("提示", "该卡已经退费")
            return
        if not messagebox.askyesno("确认退费", f"确定要退还会籍卡 {card_id} 吗？\n此操作会回滚对会员的影响。"):
            return
        result = self.biz.refund_membership(card["_row"], card_id)
        if result["success"]:
            messagebox.showinfo("成功", result.get("message", "操作成功"))
            self.refresh_data()
        else:
            messagebox.showerror("错误", result.get("error", "退费失败"))


class BandSelectDialog(tk.Toplevel):
    """选择未绑定手环对话框（由会员编辑对话框调用）"""

    def __init__(self, parent, biz, bands):
        super().__init__(parent)
        self.biz = biz
        self.bands = bands or []
        self.selected_band_id = None
        self.title("选择未绑定手环")
        self.geometry("500x350")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="选择一个未绑定的手环绑定给当前会员：",
                  font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(0, 10))

        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("手环编号", "读卡器写入值", "自定义编号")
        self.tree = ttk.Treeview(list_frame, columns=columns,
                                 show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("手环编号", width=150)
        self.tree.column("读卡器写入值", width=130)
        self.tree.column("自定义编号", width=120)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        for b in self.bands:
            self.tree.insert("", tk.END, values=(
                b.get("手环编号", ""),
                b.get("读卡器写入值", ""),
                b.get("自定义编号", ""),
            ))

        if self.bands:
            self.tree.selection_set(self.tree.get_children()[0])
        else:
            ttk.Label(main, text="暂无可用手环，请先在手环管理中注册",
                      font=("微软雅黑", 10), foreground="#999").pack()

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="\U0001f3af 确认绑定",
                  font=("微软雅黑", 11),
                  bg="#27AE60", fg="white", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self._on_confirm).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="\u274c 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _on_confirm(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个手环")
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        self.selected_band_id = values[0]
        self.destroy()
