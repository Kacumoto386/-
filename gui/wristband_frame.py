"""
手环管理界面
V2.16.1
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from gui.base_frame import BaseDataFrame


class WristbandFrame(BaseDataFrame):
    """手环管理页面"""

    def __init__(self, parent, biz):
        display_cols = [
            ("手环编号", 150), ("读卡器写入值", 130),
            ("自定义编号", 120), ("绑定会员编号", 130),
            ("绑定会员姓名", 100), ("绑定状态", 80),
            ("绑定时间", 100), ("注册时间", 100),
        ]
        super().__init__(parent, biz, "\U0001f3f7 手环管理", "wristband", display_cols)
        # 追加绑定/解绑按钮
        self._add_band_buttons()

    def _add_band_buttons(self):
        """在工具栏追加绑定/解绑按钮"""
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Frame):
                        btn_frame = sub
                        self.btn_bind = tk.Button(
                            btn_frame, text="\U0001f3af 绑定会员",
                            font=("微软雅黑", 10),
                            bg="#27AE60", fg="white",
                            padx=12, pady=3, bd=0, cursor="hand2",
                            command=self._on_bind_member)
                        self.btn_bind.pack(side=tk.LEFT, padx=2)

                        self.btn_unbind = tk.Button(
                            btn_frame, text="\U0001f517 解绑",
                            font=("微软雅黑", 10),
                            bg="#E67E22", fg="white",
                            padx=12, pady=3, bd=0, cursor="hand2",
                            command=self._on_unbind)
                        self.btn_unbind.pack(side=tk.LEFT, padx=2)
                        return

    def on_add(self):
        """注册新手环"""
        dialog = WristbandRegisterDialog(self.winfo_toplevel(), self.biz, "注册新手环")
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        """编辑手环"""
        row = self.get_selected_row()
        if not row:
            return
        dialog = WristbandRegisterDialog(self.winfo_toplevel(), self.biz,
                                         "编辑手环", data=row)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        band_id = row.get("手环编号", "")
        status = row.get("绑定状态", "")
        if status == "已绑定":
            if not messagebox.askyesno("确认删除", f"手环 {band_id} 已绑定会员，确定要删除吗？\n（不会自动解绑会员）"):
                return
        self.confirm_and_delete(
            delete_func=lambda: self.biz.delete_wristband(row["_row"]),
            item_desc=f"手环 {band_id}"
        )

    def on_search(self):
        keyword = self.search_var.get().strip()
        if keyword:
            all_data = self.biz.get_all_wristbands()
            results = [d for d in all_data if keyword in str(d.get("手环编号", ""))
                       or keyword in str(d.get("读卡器写入值", ""))
                       or keyword in str(d.get("自定义编号", ""))
                       or keyword in str(d.get("绑定会员姓名", ""))]
            self._populate_tree(results)
        else:
            self.refresh_data()

    def _on_bind_member(self):
        """绑定手环到会员"""
        row = self.get_selected_row()
        if not row:
            return
        band_id = row.get("手环编号", "")
        status = row.get("绑定状态", "")
        if status == "已绑定":
            messagebox.showinfo("提示", f"手环 {band_id} 已绑定给 {row.get('绑定会员姓名','')}")
            return

        dialog = BindMemberDialog(self.winfo_toplevel(), self.biz, band_id)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def _on_unbind(self):
        """解绑手环"""
        row = self.get_selected_row()
        if not row:
            return
        band_id = row.get("手环编号", "")
        member_id = row.get("绑定会员编号", "")
        if not member_id:
            messagebox.showinfo("提示", "该手环未绑定会员")
            return

        if not messagebox.askyesno("确认解绑", f"确定要解绑手环 {band_id} 与会员 {row.get('绑定会员姓名','')} 的绑定吗？"):
            return

        result = self.biz.unbind_wristband(band_id, member_id)
        if result["success"]:
            messagebox.showinfo("成功", result["message"])
            self.refresh_data()
        else:
            messagebox.showerror("错误", result.get("error", "解绑失败"))


class WristbandRegisterDialog(tk.Toplevel):
    """手环注册/编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.title(title)
        self.geometry("400x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.build_ui()
        if self.is_edit:
            self.load_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("读卡器写入值", "10位数字，由读卡器写入"),
            ("自定义编号", "如储物柜编号"),
            ("备注", "可选"),
        ]
        self.widgets = {}
        for i, (label, hint) in enumerate(fields):
            ttk.Label(main, text=label + "\uff1a",
                      font=("微软雅黑", 10)).grid(row=i, column=0, sticky=tk.W, pady=6)
            entry = tk.Entry(main, font=("微软雅黑", 10), width=30)
            entry.grid(row=i, column=1, sticky=tk.W, pady=6, padx=(5, 0))
            self.widgets[label] = entry

        # 提示文字
        if not self.is_edit:
            self.widgets["读卡器写入值"].insert(0, "")
            self.widgets["自定义编号"].insert(0, "")

        ttk.Label(main, text="读卡器值由刷卡设备写入，自定义编号可自由输入",
                  font=("微软雅黑", 8), foreground="#999").grid(
            row=len(fields), column=0, columnspan=2, pady=(0, 10))

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="\U0001f4be 注册" if not self.is_edit else "\u2705 保存",
                  font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="\u274c 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        self.widgets["读卡器写入值"].insert(0, self.data.get("读卡器写入值", ""))
        self.widgets["自定义编号"].insert(0, self.data.get("自定义编号", ""))
        self.widgets["备注"].insert(0, self.data.get("备注", ""))

    def on_save(self):
        reader_val = self.widgets["读卡器写入值"].get().strip()
        custom_id = self.widgets["自定义编号"].get().strip()

        if not reader_val:
            messagebox.showwarning("提示", "读卡器写入值不能为空")
            return
        if not custom_id:
            messagebox.showwarning("提示", "自定义编号不能为空")
            return

        data = {
            "读卡器写入值": reader_val,
            "自定义编号": custom_id,
            "备注": self.widgets["备注"].get().strip(),
        }

        try:
            if self.is_edit:
                result = self.biz.update_wristband(self.data["_row"], data)
            else:
                result = self.biz.add_wristband(data)

            if result["success"]:
                messagebox.showinfo("成功", result["message"])
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("message", "操作失败"))
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)}")


class BindMemberDialog(tk.Toplevel):
    """选择会员绑定手环"""

    def __init__(self, parent, biz, band_id):
        super().__init__(parent)
        self.biz = biz
        self.band_id = band_id
        self.title(f"\U0001f3af 绑定手环 {band_id}")
        self.geometry("500x400")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.build_ui()
        self.load_members()

    def build_ui(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f"\U0001f3af 为手环 {self.band_id} 选择会员",
                  font=("微软雅黑", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # 搜索
        search_frame = ttk.Frame(main)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                font=("微软雅黑", 10))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.load_members())
        search_entry.focus_set()

        # 会员列表
        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("会员编号", "姓名", "性别", "手机号", "会员等级")
        self.tree = ttk.Treeview(list_frame, columns=columns,
                                 show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("会员编号", width=130)
        self.tree.column("姓名", width=80)
        self.tree.column("性别", width=50)
        self.tree.column("手机号", width=120)
        self.tree.column("会员等级", width=70)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="\U0001f3af 确认绑定",
                  font=("微软雅黑", 11),
                  bg="#27AE60", fg="white", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self._on_confirm).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="\u274c 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def load_members(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        keyword = self.search_var.get().strip()
        if keyword:
            members = self.biz.search_members(keyword)
        else:
            members = self.biz.get_all_members()
        for m in members:
            self.tree.insert("", tk.END, values=(
                m.get("会员编号", ""),
                m.get("姓名", ""),
                m.get("性别", ""),
                m.get("手机号", ""),
                m.get("会员等级", ""),
            ))

    def _on_confirm(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个会员")
            return
        item = sel[0]
        values = self.tree.item(item, "values")
        member_id = values[0]
        member_name = values[1]

        result = self.biz.bind_wristband(self.band_id, member_id, member_name)
        if result["success"]:
            messagebox.showinfo("成功", result["message"])
            self.destroy()
        else:
            messagebox.showerror("错误", result.get("message", "绑定失败"))
