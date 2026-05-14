"""
门店权限管理UI - 用户角色管理与权限配置
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class StorePermissionFrame(ttk.Frame):
    """门店权限管理界面"""

    def __init__(self, parent, biz, store_mgr, perm_mgr):
        super().__init__(parent)
        self.biz = biz
        self.mgr = store_mgr
        self.perm_mgr = perm_mgr
        self.build_ui()
        self.load_data()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="🔐 门店权限管理",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 角色说明
        from config import STORE_ROLES
        role_frame = ttk.LabelFrame(self, text="角色说明", padding=8)
        role_frame.pack(fill=tk.X, padx=15, pady=5)
        for role_key, role_name in STORE_ROLES.items():
            from config import STORE_ROLE_DESCS
            desc = STORE_ROLE_DESCS.get(role_key, "")
            ttk.Label(role_frame, text=f"● {role_name}：{desc}",
                      font=("微软雅黑", 9), foreground="#555").pack(anchor=tk.W)

        # 操作按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=15, pady=8)
        tk.Button(btn_frame, text="➕ 新增用户", font=("微软雅黑", 10),
                  bg="#4472C4", fg="white", padx=12, pady=3, bd=0, cursor="hand2",
                  command=self._on_add).pack(side=tk.LEFT, padx=2)

        # 用户表格
        table_frame = ttk.LabelFrame(self, text="用户列表", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.tree = ttk.Treeview(table_frame, columns=(
            "用户编号", "姓名", "账号", "角色", "管辖门店列表", "状态", "创建时间"
        ), show="headings", height=10)

        col_widths = [100, 100, 120, 100, 200, 60, 150]
        for col, w in zip(self.tree["columns"], col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60)

        self.tree.bind("<Double-1>", lambda e: self._on_edit())

        # 右键菜单
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="✏️ 编辑", command=self._on_edit)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ 删除", command=self._on_delete)
        self.tree.bind("<Button-3>", lambda e: self._show_context(e))

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _show_context(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        users = self.perm_mgr.get_all_users()
        for u in users:
            self.tree.insert("", "end", values=(
                u.get("用户编号", ""),
                u.get("姓名", ""),
                u.get("账号", ""),
                u.get("角色", ""),
                u.get("管辖门店列表", ""),
                u.get("状态", ""),
                str(u.get("创建时间", ""))[:19],
            ))

    def _on_add(self):
        dialog = UserEditDialog(self.winfo_toplevel(), None, self.perm_mgr, self.mgr)
        self.wait_window(dialog.dialog)
        if dialog.result:
            self.load_data()

    def _on_edit(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择用户")
            return
        values = self.tree.item(selected[0], "values")
        users = self.perm_mgr.get_all_users()
        for u in users:
            if u.get("用户编号") == values[0]:
                dialog = UserEditDialog(self.winfo_toplevel(), u, self.perm_mgr, self.mgr)
                self.wait_window(dialog.dialog)
                if dialog.result:
                    self.load_data()
                return
        messagebox.showwarning("提示", "未找到该用户")

    def _on_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择用户")
            return
        values = self.tree.item(selected[0], "values")
        if messagebox.askyesno("确认删除", f"确定要删除用户「{values[1]}」吗？"):
            users = self.perm_mgr.get_all_users()
            for u in users:
                if u.get("用户编号") == values[0]:
                    self.perm_mgr.delete_user(u.get("_row", 0))
                    self.load_data()
                    return


class UserEditDialog:
    """用户编辑对话框"""

    def __init__(self, parent, user, perm_mgr, store_mgr):
        self.result = False
        self.is_edit = user is not None
        from config import STORE_ROLES

        dialog = tk.Toplevel(parent)
        self.dialog = dialog
        dialog.title("编辑用户" if self.is_edit else "新增用户")
        dialog.geometry("450x350")
        dialog.transient(parent)
        dialog.grab_set()
        dialog.resizable(False, False)

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 表单
        fields = [
            ("姓名", "entry"),
            ("账号", "entry"),
            ("密码", "entry"),
            ("角色", "combo", list(STORE_ROLES.keys())),
            ("管辖门店", "entry"),
        ]
        self.entries = {}
        for i, (label, ftype, *args) in enumerate(fields):
            ttk.Label(main, text=label + "：", font=("微软雅黑", 10)).grid(
                row=i, column=0, sticky="e", pady=4, padx=(0, 5))
            if ftype == "combo" and args:
                var = tk.StringVar(value=args[0][0] if not self.is_edit else "")
                w = ttk.Combobox(main, textvariable=var, values=args[0],
                                 state="readonly", width=25)
                w.grid(row=i, column=1, sticky="w", pady=4)
                self.entries[label] = var
            else:
                var = tk.StringVar()
                w = ttk.Entry(main, textvariable=var, width=28)
                w.grid(row=i, column=1, sticky="w", pady=4)
                self.entries[label] = var

        # 说明
        ttk.Label(main, text="管辖门店：多个门店用逗号分隔 (ST001,ST002)",
                  font=("微软雅黑", 8), foreground="#999").grid(
            row=5, column=0, columnspan=2, pady=(0, 10))

        # 填充数据
        if user:
            self.entries["姓名"].set(user.get("姓名", ""))
            self.entries["账号"].set(user.get("账号", ""))
            self.entries["密码"].set(user.get("密码", ""))
            self.entries["角色"].set(user.get("角色", ""))
            self.entries["管辖门店"].set(user.get("管辖门店列表", ""))

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        tk.Button(btn_frame, text="💾 保存", font=("微软雅黑", 10),
                  bg="#4472C4", fg="white", padx=20, pady=3, bd=0, cursor="hand2",
                  command=self._save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", font=("微软雅黑", 10),
                  bg="#E0E0E0", fg="#333", padx=20, pady=3, bd=0, cursor="hand2",
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        self.user = user
        self.perm_mgr = perm_mgr

    def _save(self):
        data = {
            "姓名": self.entries["姓名"].get().strip(),
            "账号": self.entries["账号"].get().strip(),
            "密码": self.entries["密码"].get().strip() or "123456",
            "角色": self.entries["角色"].get(),
            "管辖门店": self.entries["管辖门店"].get().strip(),
        }
        if not data["姓名"]:
            messagebox.showwarning("提示", "姓名不能为空")
            return
        if not data["账号"]:
            messagebox.showwarning("提示", "账号不能为空")
            return
        if not data["角色"]:
            messagebox.showwarning("提示", "请选择角色")
            return

        if self.is_edit and self.user:
            row_num = self.user.get("_row", 0)
            self.perm_mgr.update_user(row_num, {
                "姓名": data["姓名"],
                "账号": data["账号"],
                "密码": data["密码"],
                "角色": data["角色"],
                "管辖门店列表": data["管辖门店"],
            })
        else:
            self.perm_mgr.add_user(data)

        self.result = True
        self.dialog.destroy()
