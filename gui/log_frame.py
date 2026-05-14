"""
操作日志模块
"""
import tkinter as tk
from tkinter import ttk
from gui.base_frame import BaseDataFrame


class LogFrame(ttk.Frame):
    """操作日志查看"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))

        ttk.Label(header, text="📝 操作日志",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        tk.Button(header, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.load_log).pack(side=tk.RIGHT, padx=5)
        tk.Button(header, text="🗑️ 清空日志", font=("微软雅黑", 9),
                  bg="#FF0000", fg="white", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self.clear_log).pack(side=tk.RIGHT, padx=5)

        # 操作类型筛选
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(filter_frame, text="操作类型：",
                  font=("微软雅黑", 10)).pack(side=tk.LEFT)

        self.filter_var = tk.StringVar(value="全部")
        filter_menu = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                   values=["全部", "新增", "修改", "删除", "查询"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        filter_menu.pack(side=tk.LEFT, padx=5)
        filter_menu.bind("<<ComboboxSelected>>", lambda e: self.load_log())

        ttk.Label(filter_frame, text="模块：",
                  font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(15, 0))

        self.module_var = tk.StringVar(value="全部")
        module_menu = ttk.Combobox(filter_frame, textvariable=self.module_var,
                                   values=["全部", "会员", "员工", "课程", "售课", "上课", "充值"],
                                   state="readonly", width=10, font=("微软雅黑", 9))
        module_menu.pack(side=tk.LEFT, padx=5)
        module_menu.bind("<<ComboboxSelected>>", lambda e: self.load_log())

        # 表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("序号", "操作类型", "操作模块", "操作描述", "操作时间", "详情")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        col_widths = [50, 80, 80, 250, 150, 300]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=50)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_label = ttk.Label(self, text="共 0 条日志",
                                      font=("微软雅黑", 9), foreground="#999999")
        self.status_label.pack(anchor=tk.W, padx=15, pady=5)

        self.load_log()

    def load_log(self):
        """加载日志"""
        try:
            logs = self.biz.logger.get_all_logs()
        except Exception:
            logs = []

        filter_type = self.filter_var.get()
        filter_module = self.module_var.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        count = 0
        for log in logs:
            log_type = str(log.get("操作类型", ""))
            log_module = str(log.get("操作模块", ""))

            if filter_type != "全部" and log_type != filter_type:
                continue
            if filter_module != "全部" and log_module != filter_module:
                continue

            log_id = log.get("日志编号", "")
            description = log.get("操作描述", "")
            time_str = log.get("操作时间", "")
            detail = log.get("详细内容", "")

            self.tree.insert("", tk.END, values=(
                log_id, log_type, log_module, description, time_str,
                (detail[:80] + "...") if len(str(detail)) > 80 else detail,
            ))
            count += 1

        self.status_label.config(text=f"共 {count} 条日志")

    def clear_log(self):
        """清空日志"""
        import tkinter.messagebox as msg
        if msg.askyesno("确认", "确定要清空所有操作日志吗？"):
            try:
                from config import SHEETS
                # 保留表头，清空数据
                headers = self.biz.engine.get_headers(SHEETS["log"])
                self.biz.engine.clear_sheet(SHEETS["log"], headers=headers)
                # 写入表头
                self.biz.engine.write_row(SHEETS["log"], 1, {h: h for h in headers})
                # 重新调整样式
                self.biz.engine.format_header_row(SHEETS["log"], 1, len(headers))
                self.load_log()
                msg.showinfo("成功", "日志已清空")
            except Exception as e:
                msg.showerror("错误", f"清空失败: {str(e)}")
