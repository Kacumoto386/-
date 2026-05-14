"""
门店独立数据报表导出UI
- 按门店筛选导出
- 门店汇总报表
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta


class StoreExportFrame(ttk.Frame):
    """门店数据导出界面"""

    def __init__(self, parent, biz, store_mgr, export_mgr):
        super().__init__(parent)
        self.biz = biz
        self.mgr = store_mgr
        self.export_mgr = export_mgr
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📤 门店数据报表导出",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # ===== 左侧：门店导出 =====
        left = ttk.LabelFrame(self, text="门店数据导出", padding=12)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 5), pady=5)

        # 选择门店
        ttk.Label(left, text="选择门店：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.store_combo = ttk.Combobox(left, font=("微软雅黑", 10), state="readonly", width=28)
        self.store_combo.pack(fill=tk.X, pady=3)
        self._refresh_stores()

        # 数据类型
        ttk.Label(left, text="导出类型：", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(8, 0))
        self.type_combo = ttk.Combobox(left, font=("微软雅黑", 10), state="readonly", width=28)
        self.type_combo["values"] = [t[0] for t in self.export_mgr.EXPORT_TYPES]
        self.type_combo.current(0)
        self.type_combo.pack(fill=tk.X, pady=3)
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # 日期范围
        self.date_frame = ttk.Frame(left)
        self.date_frame.pack(fill=tk.X, pady=5)
        self.date_frame.pack_forget()

        ttk.Label(self.date_frame, text="起始日期：", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.start_entry = tk.Entry(self.date_frame, font=("微软雅黑", 9), width=12)
        self.start_entry.pack(side=tk.LEFT, padx=2)
        self.start_entry.insert(0, (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))

        ttk.Label(self.date_frame, text="结束：", font=("微软雅黑", 9)).pack(side=tk.LEFT)
        self.end_entry = tk.Entry(self.date_frame, font=("微软雅黑", 9), width=12)
        self.end_entry.pack(side=tk.LEFT, padx=2)
        self.end_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        for label, days in [("今天", 0), ("7天", 7), ("30天", 30)]:
            tk.Button(self.date_frame, text=label, font=("微软雅黑", 8),
                      bg="#E0E0E0", fg="#333", padx=6, pady=1, bd=0, cursor="hand2",
                      command=lambda d=days: self._set_date(d)).pack(side=tk.LEFT, padx=1)

        # 导出按钮
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="📤 导出CSV", font=("微软雅黑", 10, "bold"),
                  bg="#4472C4", fg="white", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self._on_export_store).pack(side=tk.LEFT, padx=2)

        # 状态
        self.status_label = ttk.Label(left, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(anchor=tk.W)

        # ===== 右侧：汇总报表 =====
        right = ttk.LabelFrame(self, text="门店汇总报表", padding=12)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 15), pady=5)

        ttk.Label(right, text="一键导出所有门店的经营汇总数据", font=("微软雅黑", 10),
                  foreground="#555").pack(anchor=tk.W)

        ttk.Label(right, text="包含维度：", font=("微软雅黑", 9, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W, pady=(8, 2))
        for dim in ["门店基本信息", "有效会员数", "员工数",
                     "本月售课额", "本月充值额", "本月零售额", "本月上课数"]:
            ttk.Label(right, text=f"  ● {dim}", font=("微软雅黑", 9),
                      foreground="#666").pack(anchor=tk.W)

        tk.Button(right, text="📊 导出汇总报表", font=("微软雅黑", 10, "bold"),
                  bg="#70AD47", fg="white", padx=20, pady=6, bd=0, cursor="hand2",
                  command=self._on_export_summary).pack(pady=(15, 5))

        self.summary_status = ttk.Label(right, text="", font=("微软雅黑", 9), foreground="#999")
        self.summary_status.pack(anchor=tk.W)

    def _refresh_stores(self):
        stores = self.mgr.get_all_stores()
        names = [s.get("门店名称", "") for s in stores if s.get("门店名称")]
        self.store_combo["values"] = names
        if names:
            self.store_combo.set(names[0])

    def _get_store_id(self):
        name = self.store_combo.get()
        stores = self.mgr.get_all_stores()
        for s in stores:
            if s.get("门店名称") == name:
                return s.get("门店编号", "")
        return ""

    def _on_type_change(self, event=None):
        name = self.type_combo.get()
        for n, key, has_date, _ in self.export_mgr.EXPORT_TYPES:
            if n == name:
                if has_date:
                    self.date_frame.pack(fill=tk.X, pady=5)
                else:
                    self.date_frame.pack_forget()
                break

    def _set_date(self, days_back):
        end = date.today()
        start = end - timedelta(days=days_back)
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, start.strftime("%Y-%m-%d"))
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, end.strftime("%Y-%m-%d"))

    def _on_export_store(self):
        store_name = self.store_combo.get()
        export_name = self.type_combo.get()
        if not store_name:
            messagebox.showwarning("提示", "请选择门店")
            return

        store_id = self._get_store_id()
        sheet_key = None
        has_date = False
        date_col = ""
        for n, key, hd, dc in self.export_mgr.EXPORT_TYPES:
            if n == export_name:
                sheet_key = key
                has_date = hd
                date_col = dc
                break

        if not sheet_key:
            return

        suggested = f"{store_name}_{export_name}_{date.today().strftime('%Y%m%d')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=suggested,
        )
        if not filepath:
            return

        start_str = self.start_entry.get().strip() if has_date else ""
        end_str = self.end_entry.get().strip() if has_date else ""

        result = self.export_mgr.export_store_data(
            store_id, sheet_key, filepath, start_str, end_str, date_col)

        if result["success"]:
            self.status_label.config(text=f"✅ {result.get("message", "操作成功")}")
            messagebox.showinfo("导出成功", result.get("message", "操作成功"))
        else:
            self.status_label.config(text=f"❌ {result.get("message", "操作成功")}")
            messagebox.showerror("导出失败", result.get("message", "操作成功"))

    def _on_export_summary(self):
        suggested = f"门店汇总报表_{date.today().strftime('%Y%m%d')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=suggested,
        )
        if not filepath:
            return

        result = self.export_mgr.export_all_stores_summary(filepath)
        if result["success"]:
            self.summary_status.config(text=f"✅ {result.get("message", "操作成功")}")
            messagebox.showinfo("导出成功", result.get("message", "操作成功"))
        else:
            self.summary_status.config(text=f"❌ {result.get("message", "操作成功")}")
            messagebox.showerror("导出失败", result.get("message", "操作成功"))
