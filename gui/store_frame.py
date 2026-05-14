"""
门店管理界面 - 连锁门店配置与管理
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


class StoreFrame(ttk.Frame):
    """门店管理界面"""

    def __init__(self, parent, biz, store_mgr, on_store_changed=None):
        super().__init__(parent)
        self.biz = biz
        self.mgr = store_mgr
        self._on_store_changed = on_store_changed
        self.build_ui()
        self.load_data()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="🏪 门店管理",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)
        tk.Button(header, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.load_data).pack(side=tk.RIGHT, padx=2)

        # 主内容区
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # 操作按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Button(btn_frame, text="➕ 新增门店", font=("微软雅黑", 10),
                  bg="#4472C4", fg="white", padx=12, pady=4, bd=0, cursor="hand2",
                  command=self._on_add).pack(side=tk.LEFT, padx=2)

        # 表格
        self.tree = ttk.Treeview(main, columns=(
            "门店编号", "门店名称", "门店地址", "联系电话", "店长",
            "营业时间", "门店状态", "创建日期", "备注"
        ), show="headings", height=16)

        col_widths = [100, 120, 180, 120, 80, 100, 80, 100, 150]
        for col, w in zip(self.tree["columns"], col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60)

        # 绑定双击编辑
        self.tree.bind("<Double-1>", lambda e: self._on_edit())

        # 右键菜单
        self._setup_context_menu()

        scroll = ttk.Scrollbar(main, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部信息
        self.status_label = ttk.Label(self, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(pady=(5, 10))

    def _setup_context_menu(self):
        """右键菜单"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="✏️ 编辑门店", command=self._on_edit)
        self.context_menu.add_command(label="📋 复制门店编号", command=self._copy_id)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ 删除门店", command=self._on_delete)
        self.tree.bind("<Button-3>", lambda e: self._show_context_menu(e))

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def load_data(self):
        """加载门店数据"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        stores = self.mgr.get_all_stores()
        for s in stores:
            self.tree.insert("", "end", values=(
                s.get("门店编号", ""),
                s.get("门店名称", ""),
                s.get("门店地址", ""),
                s.get("联系电话", ""),
                s.get("店长", ""),
                s.get("营业时间", ""),
                s.get("门店状态", ""),
                str(s.get("创建日期", ""))[:10] if s.get("创建日期") else "",
                s.get("备注", ""),
            ))

        self.status_label.config(text=f"共 {len(stores)} 个门店")

    def _on_add(self):
        """新增门店"""
        dialog = StoreEditDialog(self.winfo_toplevel(), None, self.mgr)
        self.wait_window(dialog.dialog)
        if dialog.result:
            self.load_data()
            if self._on_store_changed:
                self._on_store_changed()

    def _on_edit(self):
        """编辑门店"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要编辑的门店")
            return
        values = self.tree.item(selected[0], "values")
        store_id = values[0]
        store = self.mgr.get_store(store_id)
        if store:
            dialog = StoreEditDialog(self.winfo_toplevel(), store, self.mgr)
            self.wait_window(dialog.dialog)
            if dialog.result:
                self.load_data()
                if self._on_store_changed:
                    self._on_store_changed()

    def _on_delete(self):
        """删除门店"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的门店")
            return
        values = self.tree.item(selected[0], "values")
        store_id, store_name = values[0], values[1]

        if not messagebox.askyesno("确认删除", f"确定要删除门店「{store_name}」吗？\n该门店的数据映射关系也将被清除。"):
            return

        store = self.mgr.get_store(store_id)
        if store:
            row_num = store.get("_row", 0)
            self.mgr.delete_store(row_num, store_id)
            self.load_data()
            if self._on_store_changed:
                self._on_store_changed()

    def _copy_id(self):
        """复制门店编号"""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], "values")
            self.clipboard_clear()
            self.clipboard_append(values[0])
            messagebox.showinfo("提示", f"门店编号 {values[0]} 已复制")


class StoreEditDialog:
    """门店编辑/新增对话框"""

    def __init__(self, parent, store, mgr):
        self.mgr = mgr
        self.result = False
        self.is_edit = store is not None

        from config import STORE_STATUSES
        dialog = tk.Toplevel(parent)
        self.dialog = dialog
        dialog.title("编辑门店" if self.is_edit else "新增门店")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 表单字段
        fields = [
            ("门店名称", "entry"),
            ("门店地址", "entry"),
            ("联系电话", "entry"),
            ("店长", "entry"),
            ("营业时间", "entry"),
            ("门店状态", "combo", STORE_STATUSES),
            ("备注", "entry"),
        ]

        self.entries = {}
        row = 0
        for field_def in fields:
            label_text = field_def[0]
            ttk.Label(main, text=label_text + "：", font=("微软雅黑", 10)).grid(
                row=row, column=0, sticky="e", pady=4, padx=(0, 5))

            if field_def[1] == "combo":
                var = tk.StringVar(value=field_def[2][0])
                widget = ttk.Combobox(main, textvariable=var,
                                      values=field_def[2], state="readonly", width=25)
                widget.grid(row=row, column=1, sticky="w", pady=4)
                self.entries[label_text] = var
            else:
                var = tk.StringVar()
                widget = ttk.Entry(main, textvariable=var, width=28)
                widget.grid(row=row, column=1, sticky="w", pady=4)
                self.entries[label_text] = var

            row += 1

        # 填充现有数据
        if store:
            self.entries["门店名称"].set(store.get("门店名称", ""))
            self.entries["门店地址"].set(store.get("门店地址", ""))
            self.entries["联系电话"].set(store.get("联系电话", ""))
            self.entries["店长"].set(store.get("店长", ""))
            self.entries["营业时间"].set(store.get("营业时间", ""))
            self.entries["门店状态"].set(store.get("门店状态", "营业中"))
            self.entries["备注"].set(store.get("备注", ""))

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row + 1, column=0, columnspan=2, pady=(15, 0))

        tk.Button(btn_frame, text="💾 保存", font=("微软雅黑", 10),
                  bg="#4472C4", fg="white", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self._save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", font=("微软雅黑", 10),
                  bg="#E0E0E0", fg="#333", padx=20, pady=4, bd=0, cursor="hand2",
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        self._store = store
        self._dialog = dialog

    def _save(self):
        """保存门店"""
        data = {
            "门店名称": self.entries["门店名称"].get().strip(),
            "门店地址": self.entries["门店地址"].get().strip(),
            "联系电话": self.entries["联系电话"].get().strip(),
            "店长": self.entries["店长"].get().strip(),
            "营业时间": self.entries["营业时间"].get().strip(),
            "门店状态": self.entries["门店状态"].get(),
            "备注": self.entries["备注"].get().strip(),
        }

        if not data["门店名称"]:
            messagebox.showwarning("提示", "门店名称不能为空")
            return

        if self.is_edit and self._store:
            row_num = self._store.get("_row", 0)
            self.mgr.update_store(row_num, data)
        else:
            self.mgr.add_store(data)

        self.result = True
        self._dialog.destroy()
