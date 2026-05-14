"""
通用数据管理框架 - 提供增删改查基础UI
会员/员工/课程管理模块继承此类
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS as CONFIG_SHEETS
from core.exceptions import GymSystemError, ValidationError, confirm_action, show_success, show_error, safe_catch


class BaseDataFrame(ttk.Frame):
    """通用数据管理框架"""

    def __init__(self, parent, biz, title, sheet_key, display_cols):
        """
        Args:
            parent: 父容器
            biz: 业务层实例
            title: 模块标题
            sheet_key: 配置中的键名
            display_cols: 表格显示列列表 [(字段名, 列宽), ...]
        """
        super().__init__(parent)
        self.biz = biz
        self.title = title
        self.sheet_key = sheet_key
        self.display_cols = display_cols
        self.row_data = []  # 当前显示的数据行
        self.current_row = None  # 当前选中的行号
        self._sheet_name = CONFIG_SHEETS.get(sheet_key, sheet_key)
        self.build_ui()

    def build_ui(self):
        """构建基础界面"""
        # 标题栏
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))

        ttk.Label(header, text=self.title,
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=15, pady=5)

        # 左侧按钮组
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)

        self.btn_add = tk.Button(btn_frame, text="➕ 新增",
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

        # 右侧搜索栏
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

        # 数据表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = [col[0] for col in self.display_cols]
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        # 设置列
        for col_name, col_width in self.display_cols:
            self.tree.heading(col_name, text=col_name, command=lambda c=col_name: self._sort_by(c))
            self.tree.column(col_name, width=col_width, minwidth=80)

        # 滚动条
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 选中事件
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # 统计数据
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(fill=tk.X, padx=15, pady=5)

        self.status_label = ttk.Label(self.status_bar, text="共 0 条记录",
                                      font=("微软雅黑", 9), foreground="#999999")
        self.status_label.pack(side=tk.LEFT)

        # 加载数据
        self.refresh_data()

    def refresh_data(self):
        """刷新数据"""
        self.row_data = self._fetch_data()
        self._populate_tree()

    def _fetch_data(self):
        """获取数据（子类可覆写）"""
        return self.biz.engine.get_all_data(self._sheet_name)

    def _populate_tree(self, data=None):
        """填充表格"""
        # 清空
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = data if data else self.row_data
        for row in rows:
            values = []
            for col_name, _ in self.display_cols:
                val = row.get(col_name, "")
                if val is None:
                    val = ""
                values.append(str(val))
            self.tree.insert("", tk.END, values=values)

        self.status_label.config(text=f"共 {len(rows)} 条记录")
        self.current_row = None

    def _on_select(self, event):
        """选中行事件"""
        selection = self.tree.selection()
        if selection:
            # 获取选中的数据行
            item = selection[0]
            values = self.tree.item(item, "values")
            index = self.tree.index(item)
            if index < len(self.row_data):
                self.current_row = self.row_data[index].get("_row")

    def _sort_by(self, col_name):
        """按列排序"""
        col_idx = None
        for i, (name, _) in enumerate(self.display_cols):
            if name == col_name:
                col_idx = i
                break

        if col_idx is not None:
            try:
                self.row_data.sort(
                    key=lambda r: str(r.get(col_name, "") or "")
                )
            except TypeError:
                pass
            self._populate_tree()

    def get_selected_row(self):
        """获取选中的行号"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条记录")
            return None

        item = selection[0]
        index = self.tree.index(item)
        if index >= len(self.row_data):
            return None
        row = self.row_data[index]
        return row

    @safe_catch(title="删除操作")
    def confirm_and_delete(self, delete_func, item_desc=None):
        """统一确认删除流程
        
        Args:
            delete_func: 删除操作的可调用对象
            item_desc: 删除项的描述文本
        """
        name = item_desc or "选中的记录"
        if not confirm_action("确认删除", f"确定要删除「{name}」吗？此操作不可撤销。"):
            return False
        
        result = delete_func()
        if result is not False:
            show_success("删除成功", f"「{name}」已删除")
            self.refresh_data()
            return True
        return False

    # ========== 子类需覆写的方法 ==========

    def on_add(self):
        """新增（子类覆写）"""
        messagebox.showinfo("提示", "此功能待实现")

    def on_edit(self):
        """编辑（子类覆写）"""
        row = self.get_selected_row()
        if not row:
            return
        messagebox.showinfo("提示", f"此功能待实现: 编辑 {row.get('编号', '')}")

    def on_delete(self):
        """删除（子类覆写）"""
        row = self.get_selected_row()
        if not row:
            return
        messagebox.showinfo("提示", "此功能待实现")

    def on_search(self):
        """搜索（子类可覆写）"""
        keyword = self.search_var.get().strip()
        if keyword:
            results = self.biz.engine.search_rows(self._sheet_name, keyword)
            self._populate_tree(results)
        else:
            self.refresh_data()
