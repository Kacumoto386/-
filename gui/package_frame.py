"""
课程包管理模块 - 查看会员的课程包及消耗进度
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS, PACKAGE_STATUSES


class PackageFrame(ttk.Frame):
    """课程包管理主界面"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self._all_packages = []
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📦 课程包管理",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=15, pady=5)

        # 左侧操作按钮
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)

        self.btn_refresh = tk.Button(btn_frame, text="🔄 刷新",
                                     font=("微软雅黑", 10),
                                     bg="#E0E0E0", fg="#333333",
                                     padx=12, pady=3, bd=0, cursor="hand2",
                                     command=self.refresh_data)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        self.btn_reactivate = tk.Button(btn_frame, text="🔄 重新激活（已过期/已用完→有效）",
                                        font=("微软雅黑", 10),
                                        bg="#E67E22", fg="white",
                                        padx=12, pady=3, bd=0, cursor="hand2",
                                        command=self.on_reactivate)
        self.btn_reactivate.pack(side=tk.LEFT, padx=2)

        # 右侧筛选
        filter_frame = ttk.Frame(toolbar)
        filter_frame.pack(side=tk.RIGHT)

        ttk.Label(filter_frame, text="按会员筛选：", font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=2)
        self.member_var = tk.StringVar()
        members = self.biz.get_member_id_names()
        member_values = ["全部"] + list(members.values())
        self.member_combo = ttk.Combobox(filter_frame, textvariable=self.member_var,
                                          values=member_values, font=("微软雅黑", 9),
                                          width=25, state="readonly")
        self.member_combo.set("全部")
        self.member_combo.pack(side=tk.LEFT, padx=2)
        self.member_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_data())

        # 课程包表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ["课程包编号", "售课编号", "会员姓名", "课程名称",
                    "总课时", "已消耗课时", "剩余课时", "有效期起", "有效期止", "状态"]
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        col_widths = [150, 150, 80, 130, 60, 80, 60, 90, 90, 60]
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

        # 状态栏
        self.status_label = ttk.Label(self, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(fill=tk.X, padx=15, pady=5)

    def refresh_data(self):
        """刷新数据"""
        try:
            self._all_packages = self.biz.get_all_packages()
            # 自动更新状态
            self.biz.update_package_status()
            self._all_packages = self.biz.get_all_packages()
        except Exception:
            self._all_packages = self.biz.get_all_packages()
        
        self._filter_data()

    def _filter_data(self):
        """按筛选条件显示"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        member_filter = self.member_var.get()
        packages = self._all_packages
        if member_filter and member_filter != "全部":
            # 提取会员编号
            mid = member_filter.split(" - ")[0] if " - " in member_filter else ""
            packages = [p for p in packages if p.get("会员编号") == mid]

        # 按状态排序：有效 > 已用完 > 已过期
        def sort_key(p):
            status = p.get("状态", "")
            order = {"有效": 0, "已用完": 1, "已过期": 2}
            return order.get(status, 9)

        packages.sort(key=sort_key)

        for p in packages:
            valid_start = p.get("有效期起", "")
            valid_end = p.get("有效期止", "")
            if valid_start:
                valid_start = str(valid_start)[:10]
            if valid_end:
                valid_end = str(valid_end)[:10]

            values = [
                p.get("课程包编号", ""),
                p.get("售课编号", ""),
                p.get("会员姓名", ""),
                p.get("课程名称", ""),
                p.get("总课时", ""),
                p.get("已消耗课时", ""),
                p.get("剩余课时", ""),
                valid_start,
                valid_end,
                p.get("状态", ""),
            ]
            item = self.tree.insert("", tk.END, values=values)

            # 状态颜色标记
            status = p.get("状态", "")
            tag = None
            if status == "已用完":
                tag = "done"
            elif status == "已过期":
                tag = "expired"
            if tag:
                self.tree.item(item, tags=(tag,))

        self.tree.tag_configure("done", foreground="#999999")
        self.tree.tag_configure("expired", foreground="#FF0000")

        self.status_label.config(text=f"📊 {len(packages)} 个课程包")

    def get_selected_package(self):
        """获取选中的课程包记录"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个课程包")
            return None
        index = self.tree.index(selection[0])
        if index < len(self._all_packages):
            return self._all_packages[index]
        return None

    def on_reactivate(self):
        """重新激活已过期/已用完的课程包"""
        pkg = self.get_selected_package()
        if not pkg:
            return

        status = pkg.get("状态", "")
        if status not in ("已过期", "已用完"):
            messagebox.showinfo("提示", f"当前状态为 '{status}'，无需重新激活")
            return

        pkg_id = pkg.get("课程包编号", "")
        member_name = pkg.get("会员姓名", "")
        course_name = pkg.get("课程名称", "")

        if not messagebox.askyesno("确认重新激活",
                                   f"确定要重新激活课程包 {pkg_id} 吗？\n"
                                   f"会员：{member_name}\n"
                                   f"课程：{course_name}\n"
                                   f"当前状态：{status}\n\n"
                                   f"将重置为有效状态并延长有效期一年。"):
            return

        result = self.biz.reactivate_package(pkg["_row"])
        if result.get("success"):
            messagebox.showinfo("成功", result.get("message", "操作成功"))
            self.refresh_data()
        else:
            messagebox.showerror("错误", result.get("error", "重新激活失败"))
