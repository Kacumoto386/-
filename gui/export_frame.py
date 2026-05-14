"""
数据导出/报表打印界面 - 支持多种数据类型导出为CSV
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS


class ExportFrame(ttk.Frame):
    """数据导出界面"""

    # 可导出的数据类型配置 (show_name, sheet_key, has_date_filter, date_col)
    EXPORT_TYPES = [
        ("会员列表", "member", False, ""),
        ("员工列表", "staff", False, ""),
        ("售课记录", "sale", True, "售课日期"),
        ("上课记录", "class_record", True, "上课日期"),
        ("课程包汇总", "lesson_package", False, ""),
        ("预约记录", "booking", True, "预约日期"),
        ("商品列表", "product", False, ""),
        ("零售记录", "product_sale", True, "零售日期"),
        ("体测记录", "body_measurement", True, "体测日期"),
        ("会员充值", "recharge", True, "充值日期"),
        ("操作日志", "log", True, "操作时间"),
    ]

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.build_ui()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📤 数据导出",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)
        ttk.Label(header, text="将数据导出为CSV文件",
                  font=("微软雅黑", 9), foreground="#999").pack(side=tk.LEFT, padx=15)

        # 导出配置卡片
        config_frame = ttk.LabelFrame(self, text="导出设置", padding=15)
        config_frame.pack(fill=tk.X, padx=15, pady=10)

        # 导出类型
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=5)

        ttk.Label(row1, text="导出类型：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.type_combo = ttk.Combobox(row1, font=("微软雅黑", 10), width=25, state="readonly")
        self.type_combo["values"] = [t[0] for t in self.EXPORT_TYPES]
        self.type_combo.pack(side=tk.LEFT, padx=5)
        if self.EXPORT_TYPES:
            self.type_combo.set(self.EXPORT_TYPES[0][0])
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # 时间范围（默认隐藏）
        self.date_frame = ttk.Frame(config_frame)
        self.date_frame.pack(fill=tk.X, pady=5)
        self.date_frame.pack_forget()  # 初始隐藏

        ttk.Label(self.date_frame, text="起始日期：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.start_date_entry = tk.Entry(self.date_frame, font=("微软雅黑", 10), width=14)
        self.start_date_entry.pack(side=tk.LEFT, padx=2)
        self.start_date_entry.insert(0, (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))

        ttk.Label(self.date_frame, text="结束日期：", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(10, 0))
        self.end_date_entry = tk.Entry(self.date_frame, font=("微软雅黑", 10), width=14)
        self.end_date_entry.pack(side=tk.LEFT, padx=2)
        self.end_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        # 快捷日期按钮
        tk.Button(self.date_frame, text="今天", font=("微软雅黑", 9),
                  bg="#E0E0E0", fg="#333", padx=8, pady=1, bd=0, cursor="hand2",
                  command=lambda: self._set_date_range(0)).pack(side=tk.LEFT, padx=2)
        tk.Button(self.date_frame, text="近7天", font=("微软雅黑", 9),
                  bg="#E0E0E0", fg="#333", padx=8, pady=1, bd=0, cursor="hand2",
                  command=lambda: self._set_date_range(7)).pack(side=tk.LEFT, padx=2)
        tk.Button(self.date_frame, text="近30天", font=("微软雅黑", 9),
                  bg="#E0E0E0", fg="#333", padx=8, pady=1, bd=0, cursor="hand2",
                  command=lambda: self._set_date_range(30)).pack(side=tk.LEFT, padx=2)
        tk.Button(self.date_frame, text="本月", font=("微软雅黑", 9),
                  bg="#E0E0E0", fg="#333", padx=8, pady=1, bd=0, cursor="hand2",
                  command=self._set_this_month).pack(side=tk.LEFT, padx=2)

        # 导出格式
        row3 = ttk.Frame(config_frame)
        row3.pack(fill=tk.X, pady=5)

        ttk.Label(row3, text="导出格式：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.format_combo = ttk.Combobox(row3, font=("微软雅黑", 10), width=10, state="readonly")
        self.format_combo["values"] = ["CSV (.csv)"]
        self.format_combo.pack(side=tk.LEFT, padx=5)
        self.format_combo.set("CSV (.csv)")

        # 预览区
        preview_frame = ttk.LabelFrame(self, text="数据预览（最多10条）", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 预览表格
        table_frame = ttk.Frame(preview_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_tree = ttk.Treeview(table_frame, show="headings", height=8)
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.preview_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 底部操作
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=15, pady=8)

        self.btn_preview = tk.Button(action_frame, text="👁️ 预览数据",
                                     font=("微软雅黑", 10), bg="#5B9BD5", fg="white",
                                     padx=15, pady=4, bd=0, cursor="hand2",
                                     command=self.on_preview)
        self.btn_preview.pack(side=tk.LEFT, padx=3)

        self.btn_export = tk.Button(action_frame, text="📤 导出CSV",
                                    font=("微软雅黑", 10, "bold"), bg="#4472C4", fg="white",
                                    padx=20, pady=4, bd=0, cursor="hand2",
                                    command=self.on_export)
        self.btn_export.pack(side=tk.LEFT, padx=3)

        self.status_label = ttk.Label(action_frame, text="准备就绪",
                                      font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(side=tk.RIGHT)

        # 初始化预览
        self._on_type_change()

    def _on_type_change(self, event=None):
        """导出类型切换"""
        export_name = self.type_combo.get()
        for name, key, has_date, date_col in self.EXPORT_TYPES:
            if name == export_name:
                if has_date:
                    self.date_frame.pack(fill=tk.X, pady=5, before=self.date_frame.master.winfo_children()[-2]
                                         if len(self.date_frame.master.winfo_children()) > 2 else None)
                else:
                    self.date_frame.pack_forget()
                break

    def _set_date_range(self, days_back):
        """设置日期范围"""
        end = date.today()
        start = end - timedelta(days=days_back)
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, start.strftime("%Y-%m-%d"))
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, end.strftime("%Y-%m-%d"))

    def _set_this_month(self):
        """设置为本月"""
        today = date.today()
        start = date(today.year, today.month, 1)
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, start.strftime("%Y-%m-%d"))
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, today.strftime("%Y-%m-%d"))

    def _get_export_config(self):
        """获取当前导出配置"""
        export_name = self.type_combo.get()
        for name, key, has_date, date_col in self.EXPORT_TYPES:
            if name == export_name:
                return name, key, has_date, date_col
        return None, None, False, ""

    def on_preview(self):
        """预览数据"""
        name, sheet_key, has_date, date_col = self._get_export_config()
        if not sheet_key:
            messagebox.showwarning("提示", "请选择导出类型")
            return

        # 获取数据
        try:
            data = self.biz.engine.get_all_data(SHEETS[sheet_key])
        except Exception:
            data = []

        # 时间过滤
        if has_date:
            start_str = self.start_date_entry.get().strip()
            end_str = self.end_date_entry.get().strip()
            if start_str and end_str:
                try:
                    start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
                    end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()
                    filtered = []
                    for d in data:
                        val = d.get(date_col, "")
                        if val:
                            if isinstance(val, datetime):
                                d_date = val.date()
                            elif isinstance(val, date):
                                d_date = val
                            else:
                                try:
                                    d_date = datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
                                except ValueError:
                                    continue
                            if start_dt <= d_date <= end_dt:
                                filtered.append(d)
                    data = filtered
                except ValueError:
                    messagebox.showwarning("提示", "日期格式错误，请使用 YYYY-MM-DD")

        # 获取列名
        headers = self.biz.get_sheet_column_names(sheet_key)
        if not headers:
            headers = list(data[0].keys()) if data else []

        # 更新预览表格
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree["columns"] = headers

        for col in headers:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=100, minwidth=60)

        # 最多显示10条
        preview_data = data[:10]
        for row in preview_data:
            values = [str(row.get(h, "")) for h in headers]
            self.preview_tree.insert("", tk.END, values=values)

        self.status_label.config(text=f"共 {len(data)} 条记录（预览前{min(10, len(data))}条）")

    def on_export(self):
        """导出数据"""
        name, sheet_key, has_date, date_col = self._get_export_config()
        if not sheet_key:
            messagebox.showwarning("提示", "请选择导出类型")
            return

        # 选择保存路径
        suggested_name = f"{name}_{date.today().strftime('%Y%m%d')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=suggested_name,
            title="选择导出路径"
        )
        if not filepath:
            return

        # 构建过滤器
        filters = {}
        if has_date:
            start_str = self.start_date_entry.get().strip()
            end_str = self.end_date_entry.get().strip()
            if start_str and end_str:
                filters[date_col + "_start"] = start_str
                filters[date_col + "_end"] = end_str

        # 导出
        result = self.biz.export_to_csv(sheet_key, filepath, filters)
        if result["success"]:
            self.status_label.config(text=f"✅ {result.get("message", "操作成功")}")
            messagebox.showinfo("导出成功", f"成功导出 {result['count']} 条记录到:\n{filepath}")
        else:
            self.status_label.config(text=f"❌ {result.get("message", "操作成功")}")
            messagebox.showerror("导出失败", result.get("message", "操作成功"))
