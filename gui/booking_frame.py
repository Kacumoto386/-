"""
预约管理模块 - 独立预约功能
V2.13.0 - 新增搜索框（会员/手机号/教练）+ 10分钟粒度时段
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS, BOOKING_STATUSES, BOOKING_TIME_OPTIONS
from gui.base_frame import BaseDataFrame


class BookingFrame(ttk.Frame):
    """预约管理主界面"""

    def __init__(self, parent, biz, store_mgr=None, store_id=None):
        super().__init__(parent)
        self.store_mgr = store_mgr or getattr(biz, 'store_mgr', None)
        self.store_id = store_id
        self.biz = biz
        self.current_date = date.today()
        self._all_bookings = []
        self._filtered_bookings = []  # 搜索过滤后的
        self.build_ui()
        self.refresh_data()

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📅 课程预约管理",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # 搜索栏
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, padx=15, pady=(0, 5))

        ttk.Label(search_frame, text="🔍 搜索:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._apply_search())
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var,
                                       font=("微软雅黑", 10), width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self._apply_search())

        ttk.Label(search_frame, text="按会员姓名/手机号/教练名", font=("微软雅黑", 9),
                  foreground="#999").pack(side=tk.LEFT, padx=(0, 10))

        self.search_clear_btn = tk.Button(search_frame, text="✕ 清除",
                                          font=("微软雅黑", 9),
                                          bg="#E0E0E0", fg="#333",
                                          padx=8, pady=1, bd=0, cursor="hand2",
                                          command=self._clear_search)
        self.search_clear_btn.pack(side=tk.LEFT, padx=2)

        # 日期导航栏
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, padx=15, pady=2)

        tk.Button(nav_frame, text="◀ 前一天", font=("微软雅黑", 10),
                  bg="#E0E0E0", fg="#333", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self._prev_day).pack(side=tk.LEFT, padx=2)

        self.date_label = ttk.Label(nav_frame, text="", font=("微软雅黑", 12, "bold"),
                                    foreground="#4472C4")
        self.date_label.pack(side=tk.LEFT, padx=15)

        tk.Button(nav_frame, text="后一天 ▶", font=("微软雅黑", 10),
                  bg="#E0E0E0", fg="#333", padx=10, pady=2, bd=0, cursor="hand2",
                  command=self._next_day).pack(side=tk.LEFT, padx=2)

        tk.Button(nav_frame, text="📆 今天", font=("微软雅黑", 10),
                  bg="#4472C4", fg="white", padx=12, pady=2, bd=0, cursor="hand2",
                  command=self._go_today).pack(side=tk.LEFT, padx=10)

        tk.Button(nav_frame, text="➕ 新增预约", font=("微软雅黑", 10),
                  bg="#70AD47", fg="white", padx=12, pady=2, bd=0, cursor="hand2",
                  command=self.on_add).pack(side=tk.RIGHT, padx=2)

        self.refresh_btn = tk.Button(nav_frame, text="🔄 刷新", font=("微软雅黑", 10),
                                     bg="#E0E0E0", fg="#333", padx=10, pady=2, bd=0, cursor="hand2",
                                     command=self.refresh_data)
        self.refresh_btn.pack(side=tk.RIGHT, padx=2)

        # 预约表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ["预约编号", "开始时间", "结束时间", "会员姓名", "会员手机号",
                    "课程名称", "教练姓名", "预约状态", "签到人数", "最大人数"]
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        col_widths = [160, 70, 70, 80, 110, 140, 80, 70, 65, 65]
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
        self.tree.bind("<Double-1>", lambda e: self.on_sign_in())

        # 底部操作按钮
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=15, pady=8)

        self.btn_sign_in = tk.Button(action_frame, text="✅ 签到（预约→上课）",
                                     font=("微软雅黑", 10), bg="#4472C4", fg="white",
                                     padx=15, pady=4, bd=0, cursor="hand2",
                                     command=self.on_sign_in)
        self.btn_sign_in.pack(side=tk.LEFT, padx=3)

        self.btn_complete = tk.Button(action_frame, text="✔️ 完成课程",
                                      font=("微软雅黑", 10), bg="#70AD47", fg="white",
                                      padx=15, pady=4, bd=0, cursor="hand2",
                                      command=self.on_complete)
        self.btn_complete.pack(side=tk.LEFT, padx=3)

        self.btn_cancel = tk.Button(action_frame, text="❌ 取消预约",
                                    font=("微软雅黑", 10), bg="#FF0000", fg="white",
                                    padx=15, pady=4, bd=0, cursor="hand2",
                                    command=self.on_cancel)
        self.btn_cancel.pack(side=tk.LEFT, padx=3)

        self.btn_batch_sign = tk.Button(action_frame, text="👥 团课批量签到",
                                         font=("微软雅黑", 10), bg="#7030A0", fg="white",
                                         padx=15, pady=4, bd=0, cursor="hand2",
                                         command=self.on_batch_sign_in)
        self.btn_batch_sign.pack(side=tk.LEFT, padx=3)

        self.status_label = ttk.Label(action_frame, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(side=tk.RIGHT)

        self.selected_row_num = None

    # ── 搜索相关 ──

    def _apply_search(self):
        """应用搜索过滤"""
        self._filter_by_date()

    def _clear_search(self):
        """清除搜索"""
        self.search_var.set("")
        self._filter_by_date()

    # ── 数据加载与显示 ──

    def refresh_data(self):
        """刷新数据"""
        try:
            self._all_bookings = self.biz.get_all_bookings()
        except Exception:
            self._all_bookings = []
        self._filter_by_date()

    def _filter_by_date(self):
        """按当前日期+搜索词显示"""
        self.date_label.config(text=self.current_date.strftime("%Y年%m月%d日  %A"))

        keyword = self.search_var.get().strip().lower()

        # 按日期过滤
        day_bookings = [
            b for b in self._all_bookings
            if b.get("预约日期") and str(b.get("预约日期"))[:10] == str(self.current_date)[:10]
        ]

        # 按搜索词过滤
        if keyword:
            day_bookings = [
                b for b in day_bookings
                if keyword in str(b.get("会员姓名", "")).lower()
                or keyword in str(b.get("会员手机号", "")).lower()
                or keyword in str(b.get("教练姓名", "")).lower()
                or keyword in str(b.get("课程名称", "")).lower()
            ]

        self._filtered_bookings = day_bookings

        # 清空表格后重填
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 按时间排序
        day_bookings.sort(key=lambda b: b.get("开始时间", "") or "")

        for b in day_bookings:
            values = [
                b.get("预约编号", ""),
                b.get("开始时间", ""),
                b.get("结束时间", ""),
                b.get("会员姓名", ""),
                b.get("会员手机号", ""),
                b.get("课程名称", ""),
                b.get("教练姓名", ""),
                b.get("预约状态", ""),
                b.get("签到人数", 0),
                b.get("最大人数", 0),
            ]
            self.tree.insert("", tk.END, values=values)

        total = len(self._all_bookings)
        shown = len(day_bookings)
        if keyword:
            self.status_label.config(text=f"📊 搜索: {shown}/{total} 条预约")
        else:
            self.status_label.config(text=f"📊 {shown} 条预约")
        self.selected_row_num = None

    def _prev_day(self):
        self.current_date -= timedelta(days=1)
        self._filter_by_date()

    def _next_day(self):
        self.current_date += timedelta(days=1)
        self._filter_by_date()

    def _go_today(self):
        self.current_date = date.today()
        self._filter_by_date()

    def _on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self._filtered_bookings):
                self.selected_row_num = self._filtered_bookings[index].get("_row")

            # 检查是否为团课，显示/隐藏批量签到按钮
            row = self._filtered_bookings[index] if index < len(self._filtered_bookings) else None
            if row:
                course_id = row.get("课程编号", "")
                course = self.biz.get_course(course_id) if course_id else None
                if course:
                    course_type = course.get("课程类型", "")
                    is_group = any(t in str(course_type) for t in ["小班课", "大班课", "训练营", "常规课", "特色课"])
                else:
                    is_group = False
                if is_group:
                    self.btn_batch_sign.pack(side=tk.LEFT, padx=3)
                else:
                    self.btn_batch_sign.pack_forget()

    def get_selected(self):
        """获取选中的预约记录"""
        if not self.selected_row_num:
            messagebox.showwarning("提示", "请先选择一条预约记录")
            return None
        try:
            row = self.biz.engine.row_to_dict(SHEETS["booking"], self.selected_row_num)
            return row
        except Exception:
            messagebox.showwarning("提示", "无法获取预约详情")
            return None

    # ── 操作按钮 ──

    def on_add(self):
        """新增预约"""
        dialog = BookingDialog(self.winfo_toplevel(), self.biz, "新增预约", self.current_date)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_sign_in(self):
        """签到（预约→上课）"""
        row = self.get_selected()
        if not row:
            return
        if row.get("预约状态") != "已预约":
            messagebox.showinfo("提示", f"当前状态为 '{row.get('预约状态')}'，无需签到")
            return
        if messagebox.askyesno("确认签到", f"确定将 {row.get('会员姓名','')} 的 {row.get('开始时间','')} 预约签到吗？\n将自动创建上课记录并消耗1课时。"):
            result = self.biz.sign_in_booking(self.selected_row_num)
            if result["success"]:
                messagebox.showinfo("成功", result.get("message", "操作成功"))
                self.refresh_data()
            else:
                messagebox.showerror("错误", result.get("message", "操作成功"))

    def on_complete(self):
        """完成课程"""
        row = self.get_selected()
        if not row:
            return
        if row.get("预约状态") != "已签到":
            messagebox.showinfo("提示", f"当前状态为 '{row.get('预约状态')}'，需先签到")
            return
        result = self.biz.complete_booking(self.selected_row_num)
        messagebox.showinfo("提示", result.get("message", "操作成功"))
        self.refresh_data()

    def on_cancel(self):
        """取消预约"""
        row = self.get_selected()
        if not row:
            return
        if row.get("预约状态") not in ("已预约", "已签到"):
            messagebox.showinfo("提示", f"当前状态为 '{row.get('预约状态')}'，无法取消")
            return
        if messagebox.askyesno("确认取消", f"确定取消 {row.get('会员姓名','')} 的 {row.get('开始时间','')} 预约吗？"):
            result = self.biz.cancel_booking(self.selected_row_num)
            messagebox.showinfo("提示", result.get("message", "操作成功"))
            self.refresh_data()

    def on_batch_sign_in(self):
        """团课/小班课批量签到"""
        row = self.get_selected()
        if not row:
            return

        course_id = row.get("课程编号", "")
        course_name = row.get("课程名称", "")
        book_date = row.get("预约日期", "")

        if not course_id:
            messagebox.showwarning("提示", "该预约记录没有课程信息")
            return

        # 检查课程类型
        course = self.biz.get_course(course_id)
        if course:
            course_type = course.get("课程类型", "")
            is_group = any(t in str(course_type) for t in ["小班课", "大班课", "训练营", "常规课", "特色课"])
        else:
            is_group = False

        if not is_group:
            messagebox.showinfo("提示", "批量签到仅支持团课（小班课/大班课/训练营等）")
            return

        # 获取该课程的所有已预约记录
        try:
            group_bookings = self.biz.get_group_bookings_by_date(book_date, course_id)
        except Exception:
            messagebox.showerror("错误", "获取预约数据失败")
            return

        # 过滤出已预约状态
        pending_bookings = [b for b in group_bookings if b.get("预约状态") == "已预约"]

        if not pending_bookings:
            messagebox.showinfo("提示", "该课程在该时段没有待签到的会员")
            return

        dialog = BatchSignInDialog(self.winfo_toplevel(), self.biz, course_name, book_date, pending_bookings)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()


class BatchSignInDialog(tk.Toplevel):
    """团课批量签到对话框"""

    def __init__(self, parent, biz, course_name, book_date, pending_bookings):
        super().__init__(parent)
        self.biz = biz
        self.course_name = course_name
        self.book_date = book_date
        self.pending_bookings = pending_bookings

        self.title(f"👥 批量签到 - {course_name}")
        self.geometry("550x450")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=f"课程：{self.course_name}",
                  font=("微软雅黑", 12, "bold"), foreground="#1F4E79").pack(anchor=tk.W)
        date_str = str(self.book_date)[:10] if not hasattr(self.book_date, 'strftime') else self.book_date.strftime("%Y-%m-%d")
        ttk.Label(main, text=f"日期：{date_str}   待签到：{len(self.pending_bookings)} 人",
                  font=("微软雅黑", 10), foreground="#666").pack(anchor=tk.W, pady=(0, 10))

        # 全选
        select_frame = ttk.Frame(main)
        select_frame.pack(fill=tk.X, pady=(0, 5))

        self.select_all_var = tk.BooleanVar(value=True)
        self.select_all_cb = tk.Checkbutton(select_frame, text="全选/取消全选",
                                            font=("微软雅黑", 10),
                                            variable=self.select_all_var,
                                            command=self._toggle_all)
        self.select_all_cb.pack(side=tk.LEFT)

        ttk.Label(select_frame, text=f"（已选 {len(self.pending_bookings)} 人）",
                  font=("微软雅黑", 9), foreground="#999").pack(side=tk.LEFT, padx=5)

        # 会员列表
        list_frame = ttk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ["选择", "会员姓名", "会员手机号", "开始时间", "教练"]
        self.tree = ttk.Treeview(list_frame, columns=columns,
                                 show="headings", selectmode="none")
        col_widths = [50, 100, 120, 80, 80]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=50, anchor="center" if col == "选择" else "w")

        v_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.check_vars = {}
        for i, booking in enumerate(self.pending_bookings):
            var = tk.BooleanVar(value=True)
            self.check_vars[i] = var
            values = ["☑", booking.get("会员姓名", ""), booking.get("会员手机号", ""),
                      booking.get("开始时间", ""), booking.get("教练姓名", "")]
            self.tree.insert("", tk.END, iid=str(i), values=values)

        self.tree.bind("<ButtonRelease-1>", self._toggle_check)

        # 底部
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Label(btn_frame, text="💡 签到后将自动创建上课记录",
                  font=("微软雅黑", 9), foreground="#666").pack(side=tk.LEFT)
        tk.Button(btn_frame, text="✅ 批量签到", font=("微软雅黑", 11, "bold"),
                  bg="#7030A0", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_sign_in).pack(side=tk.RIGHT, padx=3)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=20, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.RIGHT, padx=3)

    def _toggle_all(self):
        select_all = self.select_all_var.get()
        for i in range(len(self.pending_bookings)):
            self.check_vars[i].set(select_all)
            values = list(self.tree.item(str(i), "values"))
            values[0] = "☑" if select_all else "☐"
            self.tree.item(str(i), values=values)

    def _toggle_check(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        i = int(item)
        self.check_vars[i].set(not self.check_vars[i].get())
        values = list(self.tree.item(item, "values"))
        values[0] = "☑" if self.check_vars[i].get() else "☐"
        self.tree.item(item, values=values)
        self.select_all_var.set(all(self.check_vars[i].get() for i in range(len(self.pending_bookings))))

    def on_sign_in(self):
        selected_rows = []
        selected_names = []
        for i in range(len(self.pending_bookings)):
            if self.check_vars[i].get():
                selected_rows.append(self.pending_bookings[i].get("_row"))
                selected_names.append(self.pending_bookings[i].get("会员姓名", ""))
        if not selected_rows:
            messagebox.showwarning("提示", "请至少选择一位会员")
            return
        msg = f"确定要为以下 {len(selected_rows)} 位会员签到吗？\n"
        msg += "、".join(x for x in selected_names[:5])
        if len(selected_names) > 5:
            msg += f" 等{len(selected_rows)}人"
        if not messagebox.askyesno("确认批量签到", msg):
            return
        result = self.biz.batch_sign_in(selected_rows)
        if result.get("success") or result.get("success_count", 0) > 0:
            msg = f"成功签到 {result.get('success_count', 0)} 人"
            if result.get("errors"):
                msg += f"\n失败: {'; '.join(result['errors'][:3])}"
            messagebox.showinfo("批量签到完成", msg)
            self.destroy()
        else:
            messagebox.showerror("错误", result.get("message", "批量签到失败"))


class BookingDialog(tk.Toplevel):
    """新增预约对话框 - V2.13.0 支持10分钟粒度时间选择"""

    def __init__(self, parent, biz, title, default_date=None):
        super().__init__(parent)
        self.biz = biz
        self.title(title)
        self.geometry("520x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.default_date = default_date or date.today()
        self.members = self.biz.get_member_id_names()
        self.courses = self.biz.get_course_id_names()
        self.staff = self.biz.get_staff_id_names()
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("预约日期", tk.Entry, {"text": self.default_date.strftime("%Y-%m-%d")}),
            ("开始时间", ttk.Combobox, {
                "values": BOOKING_TIME_OPTIONS,
                "state": "readonly",
                "width": 28,
            }),
            ("会员", ttk.Combobox, {
                "values": list(self.members.values()) if self.members else ["无"],
                "state": "readonly",
                "width": 28,
            }),
            ("课程", ttk.Combobox, {
                "values": list(self.courses.values()) if self.courses else ["无"],
                "state": "readonly",
                "width": 28,
            }),
            ("授课教练", ttk.Combobox, {
                "values": list(self.staff.values()) if self.staff else ["无"],
                "state": "readonly",
                "width": 28,
            }),
            ("备注", tk.Entry, {}),
        ]

        self.widgets = {}
        for i, (label, wtype, opts) in enumerate(fields):
            ttk.Label(main, text=label + "：", font=("微软雅黑", 10)).grid(
                row=i, column=0, sticky=tk.W, pady=5)

            width = opts.pop("width", 30) if isinstance(opts, dict) else 30

            if wtype == ttk.Combobox:
                values = opts.pop("values", [])
                w = ttk.Combobox(main, font=("微软雅黑", 10), values=values,
                                 width=width, **opts)
                if values:
                    w.set(values[0])
            else:
                w = tk.Entry(main, font=("微软雅黑", 10), width=width + 2)
                if "text" in opts:
                    w.insert(0, opts.pop("text"))

            w.grid(row=i, column=1, sticky=tk.W, pady=5, padx=(5, 0))
            self.widgets[label] = w

        # 提示
        ttk.Label(main, text="💡 签到时会自动创建上课记录并消耗1课时",
                  font=("微软雅黑", 9), foreground="#666").grid(
            row=len(fields), column=0, columnspan=2, pady=8)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def on_save(self):
        """保存预约"""
        member_str = self.widgets["会员"].get()
        course_str = self.widgets["课程"].get()
        coach_str = self.widgets["授课教练"].get()
        time_slot = self.widgets["开始时间"].get()
        date_str = self.widgets["预约日期"].get()

        if not member_str or not course_str or not time_slot:
            messagebox.showwarning("提示", "请填写会员、课程和时间")
            return

        try:
            from datetime import datetime as dt
            book_date = dt.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("提示", "日期格式错误，请使用 YYYY-MM-DD")
            return

        # 取会员信息
        mid = ""
        mname = ""
        mphone = ""
        for k, v in self.members.items():
            if v == member_str or k in member_str:
                mid = k
                mname = v.split(" - ")[-1] if " - " in v else v
                break
        # 查手机号
        all_members = self.biz.get_all_members()
        for m in all_members:
            if m.get("会员编号") == mid:
                mphone = m.get("手机号", "") or m.get("会员手机号", "")
                break

        # 取课程信息
        cid = ""
        cname = ""
        for k, v in self.courses.items():
            if v == course_str or k in course_str:
                cid = k
                cname = v.split(" - ")[-1] if " - " in v else v
                break

        # 取教练信息
        coach_name = ""
        coach_id = ""
        for k, v in self.staff.items():
            if v == coach_str or k in coach_str:
                coach_id = k
                coach_name = v.split(" - ")[-1] if " - " in v else v
                break

        data = {
            "预约日期": book_date,
            "开始时间": time_slot,
            "会员编号": mid,
            "会员姓名": mname,
            "会员手机号": mphone,
            "课程编号": cid,
            "课程名称": cname,
            "教练编号": coach_id,
            "教练姓名": coach_name,
            "备注": self.widgets["备注"].get(),
        }

        result = self.biz.add_booking(data)
        if result["success"]:
            messagebox.showinfo("成功", result.get("message", "操作成功"))
            self.destroy()
        else:
            messagebox.showerror("错误", result.get("message", "操作成功"))
