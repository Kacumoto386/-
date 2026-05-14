"""
课程管理模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from gui.base_frame import BaseDataFrame


class CourseFrame(BaseDataFrame):
    """课程管理"""

    def __init__(self, parent, biz):
        display_cols = [
            ("课程编号", 100), ("课程名称", 120), ("运动项目", 100),
            ("课程类型", 120), ("标准售价", 80), ("标准课时数", 80),
            ("课程有效期(天)", 100), ("课程状态", 70),
        ]
        super().__init__(parent, biz, "📚 课程管理", "course", display_cols)

    def _fetch_data(self):
        return self.biz.get_all_courses()

    def on_add(self):
        dialog = CourseDialog(self.winfo_toplevel(), self.biz, "新增课程")
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = CourseDialog(self.winfo_toplevel(), self.biz, "编辑课程", row)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        name = row.get("课程名称", "")
        cid = row.get("课程编号", "")
        self.confirm_and_delete(
            delete_func=lambda: self._do_delete_course(row, cid, name),
            item_desc=f"课程 {name} ({cid})"
        )

    def _do_delete_course(self, row, cid, name):
        """执行课程删除"""
        from config import SHEETS
        self.biz.engine.delete_row(SHEETS["course"], row["_row"])
        self.biz.logger.log("删除", "课程", f"删除课程 {cid} - {name}")
        return True


class CourseDialog(tk.Toplevel):
    """课程新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.title(title)
        self.geometry("550x550")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.build_ui()
        if self.is_edit:
            self.load_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("课程名称", tk.Entry, {}),
            ("运动项目", ttk.Combobox, {"values": ["力量训练", "瑜伽", "普拉提", "游泳", "拳击", "有氧操", "动感单车", "拉伸康复", "体态矫正", "其他"], "state": "readonly"}),
            ("课程类型", ttk.Combobox, {"values": ["1对1私教", "1对2", "小班课(3-8人)", "大班课(9人+)", "团课", "体验课"], "state": "readonly"}),
            ("单节课时长(分钟)", tk.Entry, {}),
            ("标准课时数", tk.Entry, {}),
            ("标准售价", tk.Entry, {}),
            ("最低售价", tk.Entry, {}),
            ("课程有效期(天)", tk.Entry, {}),
            ("最大预约人数", tk.Entry, {}),
            ("是否支持试课", ttk.Combobox, {"values": ["是", "否"], "state": "readonly"}),
            ("试课消耗课时", tk.Entry, {}),
            ("课程描述", tk.Entry, {}),
        ]

        self.widgets = {}
        for i, (label, widget_type, options) in enumerate(fields):
            ttk.Label(main, text=label + "：",
                      font=("微软雅黑", 10)).grid(row=i, column=0, sticky=tk.W, pady=4)
            if widget_type == ttk.Combobox:
                w = widget_type(main, font=("微软雅黑", 10), width=28, **options)
            else:
                w = widget_type(main, font=("微软雅黑", 10), width=30)
            w.grid(row=i, column=1, sticky=tk.W, pady=4, padx=(5, 0))
            self.widgets[label] = w

        if not self.is_edit:
            self.widgets["运动项目"].set("力量训练")
            self.widgets["课程类型"].set("1对1私教")
            self.widgets["是否支持试课"].set("否")
            self.widgets["单节课时长(分钟)"].insert(0, "60")
            self.widgets["标准课时数"].insert(0, "1")
            self.widgets["标准售价"].insert(0, "0")
            self.widgets["课程有效期(天)"].insert(0, "180")
            self.widgets["最大预约人数"].insert(0, "1")
            self.widgets["试课消耗课时"].insert(0, "0")

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        field_map = {"课程名称": "课程名称", "运动项目": "运动项目", "课程类型": "课程类型",
                     "单节课时长(分钟)": "单节课时长(分钟)", "标准课时数": "标准课时数",
                     "标准售价": "标准售价", "最低售价": "最低售价",
                     "课程有效期(天)": "课程有效期(天)", "最大预约人数": "最大预约人数",
                     "是否支持试课": "是否支持试课", "试课消耗课时": "试课消耗课时",
                     "课程描述": "课程描述"}
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if val is not None:
                w = self.widgets[label]
                if isinstance(w, ttk.Combobox):
                    w.set(str(val))
                else:
                    w.delete(0, tk.END)
                    w.insert(0, str(val))

    def on_save(self):
        data = {}
        for label, w in self.widgets.items():
            val = w.get().strip() if isinstance(w, tk.Entry) else w.get()
            if label in ("单节课时长(分钟)", "标准课时数", "最大预约人数", "课程有效期(天)", "试课消耗课时"):
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    val = 0
            elif label in ("标准售价", "最低售价"):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = 0
            data[label] = val

        if not data.get("课程名称"):
            messagebox.showwarning("提示", "课程名称不能为空")
            return

        try:
            if self.is_edit:
                from config import SHEETS
                self.biz.engine.update_row(SHEETS["course"], self.data["_row"], data)
                self.biz._course_cache = None  # 清除课程缓存
                self.biz.logger.log("修改", "课程", f"更新课程 {data.get('课程名称', '')}")
            else:
                self.biz.add_course(data)
            messagebox.showinfo("成功", "课程保存成功")
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
