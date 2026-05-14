"""
门店数据转移与合并UI
- 单条/批量数据转移
- 门店合并操作
- 转移日志查看
"""
import tkinter as tk
from tkinter import ttk, messagebox


class StoreTransferFrame(ttk.Frame):
    """门店数据转移管理界面"""

    def __init__(self, parent, biz, store_mgr, transfer_mgr):
        super().__init__(parent)
        self.biz = biz
        self.mgr = store_mgr
        self.transfer_mgr = transfer_mgr
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="🔄 门店数据转移与合并",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # ===== 左：数据转移 =====
        left = ttk.LabelFrame(self, text="数据转移", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 5), pady=5)

        # 源门店
        ttk.Label(left, text="源门店：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.src_combo = ttk.Combobox(left, font=("微软雅黑", 10), state="readonly", width=25)
        self.src_combo.pack(fill=tk.X, pady=2)
        self.src_combo.bind("<<ComboboxSelected>>", self._on_source_changed)

        # 数据类型
        ttk.Label(left, text="数据类型：", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(8, 0))
        self.type_combo = ttk.Combobox(left, font=("微软雅黑", 10), state="readonly", width=25)
        self.type_combo["values"] = ["member", "staff", "sale", "class_record",
                                      "recharge", "booking", "product", "product_sale"]
        self.type_combo.current(0)
        self.type_combo.pack(fill=tk.X, pady=2)

        # 可选择数据列表
        ttk.Label(left, text="待转移数据（可多选）：", font=("微软雅黑", 10)).pack(
            anchor=tk.W, pady=(8, 0))
        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.data_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED,
                                        font=("微软雅黑", 9), height=8)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.data_listbox.yview)
        self.data_listbox.configure(yscrollcommand=scroll.set)
        self.data_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 操作按钮
        btn_f1 = ttk.Frame(left)
        btn_f1.pack(fill=tk.X, pady=8)
        tk.Button(btn_f1, text="📋 刷新数据列表", font=("微软雅黑", 9),
                  bg="#5B9BD5", fg="white", padx=8, pady=2, bd=0, cursor="hand2",
                  command=self._refresh_data_list).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_f1, text="✅ 全选", font=("微软雅黑", 9),
                  bg="#70AD47", fg="white", padx=8, pady=2, bd=0, cursor="hand2",
                  command=self._select_all).pack(side=tk.LEFT, padx=2)

        # 目标门店
        ttk.Label(left, text="目标门店：", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(5, 0))
        self.dst_combo = ttk.Combobox(left, font=("微软雅黑", 10), state="readonly", width=25)
        self.dst_combo.pack(fill=tk.X, pady=2)

        # 转移按钮
        tk.Button(left, text="🚀 执行转移", font=("微软雅黑", 10, "bold"),
                  bg="#E74C3C", fg="white", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self._on_transfer).pack(pady=8)

        # ===== 右：门店合并 =====
        right = ttk.LabelFrame(self, text="门店合并", padding=10)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 5), pady=5)

        ttk.Label(right, text="⚠️ 合并操作将把源门店所有数据\n转移到目标门店，并关闭源门店。",
                  font=("微软雅黑", 9), foreground="#E74C3C", justify=tk.LEFT).pack(
            anchor=tk.W, pady=(0, 10))

        ttk.Label(right, text="源门店（将被关闭）：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.merge_src = ttk.Combobox(right, font=("微软雅黑", 10), state="readonly", width=25)
        self.merge_src.pack(fill=tk.X, pady=2)

        ttk.Label(right, text="目标门店（保留）：", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(8, 0))
        self.merge_dst = ttk.Combobox(right, font=("微软雅黑", 10), state="readonly", width=25)
        self.merge_dst.pack(fill=tk.X, pady=2)

        tk.Button(right, text="🔀 执行合并", font=("微软雅黑", 10, "bold"),
                  bg="#FF6600", fg="white", padx=20, pady=4, bd=0, cursor="hand2",
                  command=self._on_merge).pack(pady=(15, 5))

        # 转移日志
        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(right, text="最近转移记录", font=("微软雅黑", 11, "bold"),
                  foreground="#2E75B6").pack(anchor=tk.W)

        self.log_text = tk.Text(right, font=("微软雅黑", 9), height=8,
                                 bg="#FAFAFA", fg="#333", wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=2)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=2)

        # 加载门店列表
        self._refresh_store_lists()

    def _refresh_store_lists(self):
        stores = self.mgr.get_all_stores()
        names = [s.get("门店名称", "") for s in stores if s.get("门店名称")]
        self.src_combo["values"] = names
        self.dst_combo["values"] = names
        self.merge_src["values"] = names
        self.merge_dst["values"] = names
        if names:
            self.src_combo.set(names[0] if len(names) > 1 else "")
            self.dst_combo.set(names[-1] if len(names) > 1 else "")
            self.merge_src.set(names[0] if len(names) > 1 else "")
            self.merge_dst.set(names[-1] if len(names) > 1 else "")
        self._refresh_log()

    def _get_store_id(self, name):
        stores = self.mgr.get_all_stores()
        for s in stores:
            if s.get("门店名称") == name:
                return s.get("门店编号", "")
        return ""

    def _on_source_changed(self, event=None):
        self._refresh_data_list()

    def _refresh_data_list(self, event=None):
        self.data_listbox.delete(0, tk.END)
        store_name = self.src_combo.get()
        data_type = self.type_combo.get()
        if not store_name or not data_type:
            return

        store_id = self._get_store_id(store_name)
        mapped = self.mgr.get_data_ids_for_store(store_id, data_type)
        id_field = self.mgr.get_id_field(data_type)

        # 获取所有数据
        from config import SHEETS
        all_data = self.biz.engine.get_all_data(SHEETS.get(data_type, data_type))
        mapped_ids = set(m.get("数据编号", "") for m in mapped)

        for d in all_data:
            did = d.get(id_field, "")
            if did in mapped_ids:
                name = d.get("姓名", d.get("会员名称", d.get("课程名称", "")))
                display = f"{did} - {name}" if name else did
                self.data_listbox.insert(tk.END, display)

        # 也显示计数
        if self.data_listbox.size() > 0:
            self.data_listbox.selection_set(0, self.data_listbox.size() - 1)

    def _select_all(self):
        self.data_listbox.selection_set(0, tk.END)

    def _on_transfer(self):
        src_name = self.src_combo.get()
        dst_name = self.dst_combo.get()
        data_type = self.type_combo.get()

        if not src_name or not dst_name:
            messagebox.showwarning("提示", "请选择源门店和目标门店")
            return
        if src_name == dst_name:
            messagebox.showwarning("提示", "源门店和目标门店不能相同")
            return

        selected = self.data_listbox.curselection()
        if not selected:
            messagebox.showwarning("提示", "请选择要转移的数据")
            return

        store_id = self._get_store_id(dst_name)
        data_ids = []
        for idx in selected:
            text = self.data_listbox.get(idx)
            data_ids.append(text.split(" - ")[0])

        if not messagebox.askyesno("确认转移", f"确定将 {len(data_ids)} 条{data_type}数据\n"
                                             f"从「{src_name}」转移到「{dst_name}」？"):
            return

        result = self.transfer_mgr.transfer_data(data_type, data_ids, store_id,
                                                  operator="admin", reason="手动转移")
        if result["success"]:
            messagebox.showinfo("转移成功", result.get("message", "操作成功"))
            self._refresh_data_list()
            self._refresh_log()
        else:
            messagebox.showerror("转移失败", result.get("message", "操作成功"))

    def _on_merge(self):
        src_name = self.merge_src.get()
        dst_name = self.merge_dst.get()

        if not src_name or not dst_name:
            messagebox.showwarning("提示", "请选择源门店和目标门店")
            return
        if src_name == dst_name:
            messagebox.showwarning("提示", "源门店和目标门店不能相同")
            return

        if not messagebox.askyesno("确认合并",
                                   f"⚠️ 此操作将：\n"
                                   f"1. 把「{src_name}」所有数据转移到「{dst_name}」\n"
                                   f"2. 关闭「{src_name}」\n\n"
                                   f"确认执行？"):
            return

        result = self.transfer_mgr.merge_stores(
            self._get_store_id(src_name),
            self._get_store_id(dst_name),
            operator="admin",
        )

        if result["success"]:
            messagebox.showinfo("合并完成", result.get("message", "操作成功"))
            self._refresh_store_lists()
            self._refresh_data_list()
        else:
            messagebox.showerror("合并失败", result.get("message", "操作成功"))

    def _refresh_log(self):
        self.log_text.delete(1.0, tk.END)
        logs = self.transfer_mgr.get_transfer_logs(limit=20)
        if not logs:
            self.log_text.insert(tk.END, "暂无转移记录\n")
            return
        for log in reversed(logs):
            time_str = str(log.get("转移时间", ""))[:19]
            msg = f"[{time_str}] {log.get('数据类型','')} #{log.get('数据编号','')} → {log.get('目标门店编号','')}"
            self.log_text.insert(tk.END, msg + "\n")
