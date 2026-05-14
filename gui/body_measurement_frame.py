"""
体测记录管理模块 - 记录和追踪会员的体测数据
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS


class BodyMeasurementFrame(ttk.Frame):
    """体测记录管理主界面"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self._all_measurements = []
        self.current_row_num = None
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📊 会员体测记录",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=15, pady=5)

        # 左侧按钮
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)

        self.btn_add = tk.Button(btn_frame, text="➕ 新增体测",
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

        self.btn_chart = tk.Button(filter_frame, text="📈 查看趋势",
                                   font=("微软雅黑", 9),
                                   bg="#5B9BD5", fg="white",
                                   padx=8, pady=2, bd=0, cursor="hand2",
                                   command=self.on_show_chart)
        self.btn_chart.pack(side=tk.LEFT, padx=5)

        # 体测记录表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ["体测编号", "会员姓名", "体测日期", "身高(cm)", "体重(kg)",
                    "体脂率(%)", "BMI", "肌肉量(kg)", "基础代谢(kcal)", "体年龄", "备注"]
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        col_widths = [150, 70, 90, 60, 60, 60, 50, 60, 80, 50, 100]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=50)

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
        self.status_label = ttk.Label(self, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(fill=tk.X, padx=15, pady=5)

    def refresh_data(self):
        """刷新数据"""
        try:
            self._all_measurements = self.biz.get_all_measurements()
        except Exception:
            self._all_measurements = []
        self._filter_data()

    def _filter_data(self):
        """按筛选条件显示"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        member_filter = self.member_var.get()
        measurements = self._all_measurements
        if member_filter and member_filter != "全部":
            mid = member_filter.split(" - ")[0] if " - " in member_filter else ""
            measurements = [m for m in measurements if m.get("会员编号") == mid]

        # 按日期排序（最新在前）
        measurements.sort(key=lambda m: str(m.get("体测日期", "")), reverse=True)

        for m in measurements:
            m_date = m.get("体测日期", "")
            if m_date:
                m_date = str(m_date)[:10]

            values = [
                m.get("体测编号", ""),
                m.get("会员姓名", ""),
                m_date,
                m.get("身高(cm)", ""),
                m.get("体重(kg)", ""),
                m.get("体脂率(%)", ""),
                m.get("BMI", ""),
                m.get("肌肉量(kg)", ""),
                m.get("基础代谢(kcal)", ""),
                m.get("体年龄", ""),
                m.get("备注", ""),
            ]
            self.tree.insert("", tk.END, values=values)

        self.status_label.config(text=f"📊 {len(measurements)} 条体测记录")

    def _on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self._filtered_data()):
                pass
            self.current_row_num = self._get_row_num(index)

    def _filtered_data(self):
        member_filter = self.member_var.get()
        measurements = self._all_measurements
        if member_filter and member_filter != "全部":
            mid = member_filter.split(" - ")[0] if " - " in member_filter else ""
            measurements = [m for m in measurements if m.get("会员编号") == mid]
        measurements.sort(key=lambda m: str(m.get("体测日期", "")), reverse=True)
        return measurements

    def _get_row_num(self, index):
        data = self._filtered_data()
        if 0 <= index < len(data):
            return data[index].get("_row")
        return None

    def get_selected(self):
        """获取选中的体测记录"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条体测记录")
            return None
        item = selection[0]
        index = self.tree.index(item)
        data = self._filtered_data()
        if index < len(data):
            return data[index]
        return None

    def on_add(self):
        """新增体测记录"""
        dialog = BodyMeasurementDialog(self.winfo_toplevel(), self.biz, "新增体测记录")
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        """编辑体测记录"""
        row = self.get_selected()
        if not row:
            return
        dialog = BodyMeasurementDialog(self.winfo_toplevel(), self.biz, "编辑体测记录", row)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        """删除体测记录"""
        row = self.get_selected()
        if not row:
            return
        measurement_id = row.get("体测编号", "")
        if messagebox.askyesno("确认删除", f"确定删除体测记录 {measurement_id} 吗？"):
            result = self.biz.delete_body_measurement(row["_row"])
            msg = result.get("message", "体测记录已删除")
            messagebox.showinfo("成功", msg)
            self.refresh_data()

    def on_show_chart(self):
        """查看体测趋势图"""
        row = self.get_selected()
        if not row:
            return
        member_id = row.get("会员编号", "")
        member_name = row.get("会员姓名", "")
        if member_id:
            ChartDialog(self.winfo_toplevel(), self.biz, member_id, member_name)
        else:
            messagebox.showwarning("提示", "请选择有会员编号的记录")


class BodyMeasurementDialog(tk.Toplevel):
    """体测记录新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.title(title)
        self.geometry("450x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.members = self.biz.get_member_id_names()
        self.build_ui()
        if self.is_edit:
            self.load_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 会员选择
        row = 0
        ttk.Label(main, text="选择会员：", font=("微软雅黑", 10)).grid(row=row, column=0, sticky=tk.W, pady=4)
        member_values = list(self.members.values()) if self.members else ["暂无会员"]
        self.member_combo = ttk.Combobox(main, values=member_values,
                                          font=("微软雅黑", 10), width=30, state="readonly")
        self.member_combo.grid(row=row, column=1, sticky=tk.W, pady=4, padx=(5, 0))

        # 体测日期
        row += 1
        ttk.Label(main, text="体测日期：", font=("微软雅黑", 10)).grid(row=row, column=0, sticky=tk.W, pady=4)
        self.date_entry = tk.Entry(main, font=("微软雅黑", 10), width=32)
        self.date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=row, column=1, sticky=tk.W, pady=4, padx=(5, 0))

        # 体测数据字段
        self.fields = {}
        field_list = [
            ("身高(cm)", "0"),
            ("体重(kg)", "0"),
            ("体脂率(%)", ""),
            ("肌肉量(kg)", ""),
            ("基础代谢(kcal)", ""),
            ("体年龄", ""),
            ("备注", ""),
        ]

        for i, (label, default) in enumerate(field_list):
            row += 1
            ttk.Label(main, text=label + "：", font=("微软雅黑", 10)).grid(row=row, column=0, sticky=tk.W, pady=3)
            w = tk.Entry(main, font=("微软雅黑", 10), width=32)
            w.grid(row=row, column=1, sticky=tk.W, pady=3, padx=(5, 0))
            if default:
                w.insert(0, default)
            self.fields[label] = w

        # 提示
        row += 1
        ttk.Label(main, text="💡 BMI将根据身高体重自动计算",
                  font=("微软雅黑", 9), foreground="#666").grid(
            row=row, column=0, columnspan=2, pady=5)

        # 按钮
        row += 1
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """加载现有数据"""
        member_id = self.data.get("会员编号", "")
        member_val = self.members.get(member_id, "")
        if member_val:
            self.member_combo.set(member_val)

        m_date = self.data.get("体测日期", "")
        if m_date:
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, str(m_date)[:10])

        field_map = {
            "身高(cm)": "身高(cm)",
            "体重(kg)": "体重(kg)",
            "体脂率(%)": "体脂率(%)",
            "肌肉量(kg)": "肌肉量(kg)",
            "基础代谢(kcal)": "基础代谢(kcal)",
            "体年龄": "体年龄",
            "备注": "备注",
        }
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if val is not None and val != "":
                w = self.fields[label]
                w.delete(0, tk.END)
                w.insert(0, str(val))

    def on_save(self):
        """保存"""
        member_name = self.member_combo.get()
        if not member_name:
            messagebox.showwarning("提示", "请选择会员")
            return

        member_id = ""
        for mid, name in self.members.items():
            if name == member_name:
                member_id = mid
                break

        try:
            m_date = datetime.strptime(self.date_entry.get(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("提示", "日期格式错误，请使用 YYYY-MM-DD")
            return

        data = {
            "会员编号": member_id,
            "会员姓名": member_name.split(" - ")[-1] if " - " in member_name else member_name,
            "体测日期": m_date,
            "身高(cm)": self._safe_float(self.fields["身高(cm)"].get()),
            "体重(kg)": self._safe_float(self.fields["体重(kg)"].get()),
            "体脂率(%)": self.fields["体脂率(%)"].get(),
            "肌肉量(kg)": self.fields["肌肉量(kg)"].get(),
            "基础代谢(kcal)": self.fields["基础代谢(kcal)"].get(),
            "体年龄": self.fields["体年龄"].get(),
            "备注": self.fields["备注"].get(),
        }

        if self.is_edit:
            result = self.biz.update_body_measurement(self.data["_row"], data)
        else:
            result = self.biz.add_body_measurement(data)

        if result.get("success"):
            msg = result.get("message", "保存成功")
            messagebox.showinfo("成功", msg)
            self.destroy()
        else:
            msg = result.get("error", result.get("message", "保存失败"))
            messagebox.showerror("错误", msg)

    @staticmethod
    def _safe_float(val):
        try:
            return float(val) if val else 0
        except (ValueError, TypeError):
            return 0


class ChartDialog(tk.Toplevel):
    """体测趋势图对话框"""

    def __init__(self, parent, biz, member_id, member_name):
        super().__init__(parent)
        self.biz = biz
        self.member_id = member_id
        self.member_name = member_name
        self.title(f"📈 {member_name} 体测趋势")
        self.geometry("650x500")
        self.transient(parent)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f"{self.member_name} 体测历史趋势",
                  font=("微软雅黑", 14, "bold"), foreground="#1F4E79").pack(pady=(0, 10))

        measurements = self.biz.get_member_measurements(self.member_id)

        if len(measurements) < 2:
            ttk.Label(main, text="历史记录不足2条，无法绘制趋势图（至少需要2次体测数据）",
                      font=("微软雅黑", 10), foreground="#999").pack(expand=True)
            tk.Button(main, text="关闭", font=("微软雅黑", 10),
                      bg="#E0E0E0", fg="#333", padx=20, pady=3, bd=0,
                      command=self.destroy).pack(pady=10)
            return

        # 使用matplotlib绘图
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure

            # 准备数据
            dates = []
            weights = []
            body_fats = []
            bmis = []

            for m in measurements:
                m_date = m.get("体测日期", "")
                if m_date:
                    try:
                        d = datetime.strptime(str(m_date)[:10], "%Y-%m-%d")
                        dates.append(d)
                    except ValueError:
                        dates.append(datetime.now())
                weight = m.get("体重(kg)", "")
                body_fat = m.get("体脂率(%)", "")
                bmi = m.get("BMI", "")

                try:
                    weights.append(float(weight) if weight else None)
                except (ValueError, TypeError):
                    weights.append(None)
                try:
                    body_fats.append(float(body_fat) if body_fat else None)
                except (ValueError, TypeError):
                    body_fats.append(None)
                try:
                    bmis.append(float(bmi) if bmi else None)
                except (ValueError, TypeError):
                    bmis.append(None)

            # 创建图表
            fig = Figure(figsize=(6, 4), dpi=90)
            fig.suptitle(f"{self.member_name} - 体测趋势", fontsize=12)

            # 体重
            ax1 = fig.add_subplot(311)
            valid_weights = [(d, w) for d, w in zip(dates, weights) if w is not None]
            if valid_weights:
                w_dates, w_vals = zip(*valid_weights)
                ax1.plot(w_dates, w_vals, "o-", color="#4472C4", linewidth=2)
                ax1.set_ylabel("体重(kg)", fontsize=9)
                ax1.tick_params(axis="x", labelsize=8)
                ax1.grid(True, alpha=0.3)

            # 体脂率
            ax2 = fig.add_subplot(312)
            valid_fats = [(d, f) for d, f in zip(dates, body_fats) if f is not None]
            if valid_fats:
                f_dates, f_vals = zip(*valid_fats)
                ax2.plot(f_dates, f_vals, "s-", color="#70AD47", linewidth=2)
                ax2.set_ylabel("体脂率(%)", fontsize=9)
                ax2.tick_params(axis="x", labelsize=8)
                ax2.grid(True, alpha=0.3)

            # BMI
            ax3 = fig.add_subplot(313)
            valid_bmis = [(d, b) for d, b in zip(dates, bmis) if b is not None]
            if valid_bmis:
                b_dates, b_vals = zip(*valid_bmis)
                ax3.plot(b_dates, b_vals, "^-", color="#FFC000", linewidth=2)
                ax3.set_ylabel("BMI", fontsize=9)
                ax3.tick_params(axis="x", labelsize=8)
                ax3.grid(True, alpha=0.3)

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=main)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # 数据表格
            table_frame = ttk.Frame(main)
            table_frame.pack(fill=tk.X, pady=(10, 0))

            columns = ["体测日期", "体重(kg)", "体脂率(%)", "BMI"]
            tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=4)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=80)

            for i, m in enumerate(measurements):
                m_date = str(m.get("体测日期", ""))[:10]
                tree.insert("", tk.END, values=[
                    m_date,
                    m.get("体重(kg)", ""),
                    m.get("体脂率(%)", ""),
                    m.get("BMI", ""),
                ])
            tree.pack(fill=tk.X)

        except ImportError:
            ttk.Label(main, text="matplotlib未安装，无法显示图表。\n请运行: pip install matplotlib",
                      font=("微软雅黑", 10), foreground="#FF0000").pack(expand=True)

        tk.Button(main, text="关闭", font=("微软雅黑", 10),
                  bg="#E0E0E0", fg="#333", padx=20, pady=3, bd=0,
                  command=self.destroy).pack(pady=10)
