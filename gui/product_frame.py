"""
商品管理界面 - 商品增删改查 + 库存显示
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS, PRODUCT_CATEGORIES
from gui.base_frame import BaseDataFrame


class ProductFrame(ttk.Frame):
    """商品管理主界面"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self._all_products = []
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="🏪 商品管理",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=15, pady=5)

        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)

        self.btn_add = tk.Button(btn_frame, text="➕ 新增商品",
                                 font=("微软雅黑", 10),
                                 bg="#4472C4", fg="white",
                                 padx=12, pady=3, bd=0, cursor="hand2",
                                 command=self.on_add)
        self.btn_add.pack(side=tk.LEFT, padx=2)

        self.btn_edit = tk.Button(btn_frame, text="✏️ 编辑",
                                  font=("微软雅黑", 10),
                                  bg="#70AD47", fg="white",
                                  padx=12, pady=3, bd=0, cursor="hand2",
                                  command=self.on_edit)
        self.btn_edit.pack(side=tk.LEFT, padx=2)

        self.btn_delete = tk.Button(btn_frame, text="🗑️ 删除",
                                    font=("微软雅黑", 10),
                                    bg="#FF0000", fg="white",
                                    padx=12, pady=3, bd=0, cursor="hand2",
                                    command=self.on_delete)
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        self.btn_refresh = tk.Button(btn_frame, text="🔄 刷新",
                                     font=("微软雅黑", 10),
                                     bg="#E0E0E0", fg="#333333",
                                     padx=12, pady=3, bd=0, cursor="hand2",
                                     command=self.refresh_data)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        # 搜索栏
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("微软雅黑", 10), width=20,
                                     relief="solid", bd=1)
        self.search_entry.pack(side=tk.LEFT, padx=2)
        self.search_entry.bind("<Return>", lambda e: self.on_search())

        self.btn_search = tk.Button(search_frame, text="🔍 搜索",
                                    font=("微软雅黑", 9),
                                    bg="#5B9BD5", fg="white",
                                    padx=8, pady=2, bd=0, cursor="hand2",
                                    command=self.on_search)
        self.btn_search.pack(side=tk.LEFT, padx=2)

        # 库存统计栏
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill=tk.X, padx=15, pady=2)
        self.stock_label = ttk.Label(stats_frame, text="", font=("微软雅黑", 9), foreground="#666")
        self.stock_label.pack(side=tk.LEFT)

        # 商品表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ["商品编号", "商品名称", "商品类别", "进价", "售价", "库存数量", "单位", "供应商", "备注"]
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        col_widths = [120, 150, 100, 80, 80, 80, 60, 120, 150]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60)

        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self.on_edit())

        # 状态栏
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(fill=tk.X, padx=15, pady=5)

        self.status_label = ttk.Label(self.status_bar, text="共 0 件商品",
                                      font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(side=tk.LEFT)

        self.current_row = None
        self.row_data = []

    def refresh_data(self):
        """刷新数据"""
        try:
            self._all_products = self.biz.get_all_products()
        except Exception:
            self._all_products = []
        self._populate_tree()
        self._update_stock_stats()

    def _populate_tree(self, data=None):
        """填充表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = data if data is not None else self._all_products
        for row in rows:
            values = []
            for col in ["商品编号", "商品名称", "商品类别", "进价", "售价", "库存数量", "单位", "供应商", "备注"]:
                val = row.get(col, "")
                if val is None:
                    val = ""
                values.append(str(val))
            self.tree.insert("", tk.END, values=values)

        self.status_label.config(text=f"共 {len(rows)} 件商品")
        self.current_row = None
        self.row_data = rows

    def _update_stock_stats(self):
        """更新库存统计"""
        total_items = sum(self._safe_int(p.get("库存数量", 0)) for p in self._all_products)
        low_stock = [p for p in self._all_products if self._safe_int(p.get("库存数量", 0)) <= 5]
        low_stock_names = ", ".join([p.get("商品名称", "") for p in low_stock[:5]])
        stock_text = f"📦 总库存: {total_items} 件"
        if low_stock:
            stock_text += f" | ⚠️ 库存不足: {low_stock_names}"
            self.stock_label.config(text=stock_text, foreground="#CC4400")
        else:
            self.stock_label.config(text=stock_text, foreground="#666")

    @staticmethod
    def _safe_int(val, default=0):
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def _on_select(self, event):
        """选中行事件"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.row_data):
                self.current_row = self.row_data[index].get("_row")

    def get_selected_row(self):
        """获取选中的行"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条记录")
            return None
        item = selection[0]
        index = self.tree.index(item)
        if index < len(self.row_data):
            return self.row_data[index]
        return None

    def on_add(self):
        """新增商品"""
        dialog = ProductEditDialog(self.winfo_toplevel(), self.biz, "新增商品")
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        """编辑商品"""
        row = self.get_selected_row()
        if not row:
            return
        dialog = ProductEditDialog(self.winfo_toplevel(), self.biz, "编辑商品", row)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        """删除商品"""
        row = self.get_selected_row()
        if not row:
            return
        name = row.get("商品名称", "")
        if messagebox.askyesno("确认删除", f"确定要删除商品「{name}」吗？\n此操作不可撤销。"):
            result = self.biz.delete_product(row.get("_row"))
            messagebox.showinfo("提示", result.get("message", "删除成功"))
            self.refresh_data()()

    def on_search(self):
        """搜索商品"""
        keyword = self.search_var.get().strip()
        if keyword:
            results = self.biz.search_products(keyword)
            self._populate_tree(results)
        else:
            self.refresh_data()


class ProductEditDialog(tk.Toplevel):
    """商品编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.title(title)
        self.geometry("500x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("商品名称", tk.Entry),
            ("商品类别", ttk.Combobox),
            ("进价", tk.Entry),
            ("售价", tk.Entry),
            ("库存数量", tk.Entry),
            ("单位", tk.Entry),
            ("供应商", tk.Entry),
            ("备注", tk.Entry),
        ]

        self.widgets = {}
        for i, (label, wtype) in enumerate(fields):
            ttk.Label(main, text=label + "：", font=("微软雅黑", 10)).grid(row=i, column=0, sticky=tk.W, pady=5)

            if wtype == ttk.Combobox:
                w = wtype(main, font=("微软雅黑", 10), width=30,
                          values=PRODUCT_CATEGORIES, state="readonly")
            else:
                w = wtype(main, font=("微软雅黑", 10), width=32)
            w.grid(row=i, column=1, sticky=tk.W, pady=5, padx=(5, 0))
            self.widgets[label] = w

        # 预填数据
        if self.data:
            mapping = {
                "商品名称": "商品名称", "商品类别": "商品类别",
                "进价": "进价", "售价": "售价",
                "库存数量": "库存数量", "单位": "单位",
                "供应商": "供应商", "备注": "备注",
            }
            for field, key in mapping.items():
                val = self.data.get(key, "")
                if val is not None:
                    if field in self.widgets:
                        if isinstance(self.widgets[field], ttk.Combobox):
                            self.widgets[field].set(str(val))
                        else:
                            self.widgets[field].insert(0, str(val))

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=15)

        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def on_save(self):
        """保存"""
        name = self.widgets["商品名称"].get().strip()
        if not name:
            messagebox.showwarning("提示", "商品名称不能为空")
            return

        data = {
            "商品名称": name,
            "商品类别": self.widgets["商品类别"].get(),
            "进价": self._safe_float(self.widgets["进价"].get()),
            "售价": self._safe_float(self.widgets["售价"].get()),
            "库存数量": self._safe_int(self.widgets["库存数量"].get()),
            "单位": self.widgets["单位"].get().strip() or "个",
            "供应商": self.widgets["供应商"].get().strip(),
            "备注": self.widgets["备注"].get().strip(),
        }

        if self.data:
            # 编辑
            result = self.biz.update_product(self.data.get("_row"), data)
        else:
            # 新增
            result = self.biz.add_product(data)

        if result["success"]:
            messagebox.showinfo("成功", result.get("message", "操作成功"))
            self.destroy()
        else:
            messagebox.showerror("错误", result.get("message", "操作成功"))

    @staticmethod
    def _safe_float(val, default=0.0):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_int(val, default=0):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default
