"""
上课记录管理模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gui.base_frame import BaseDataFrame


class ClassFrame(BaseDataFrame):
    """上课记录"""

    def __init__(self, parent, biz):
        display_cols = [
            ("上课编号", 160), ("上课日期", 100), ("上课时间", 70),
            ("授课教练", 80), ("会员姓名", 80), ("课程名称", 120),
            ("消耗课时数", 80), ("上课状态", 70), ("上课评价", 80),
        ]
        super().__init__(parent, biz, "🎓 上课记录管理", "class_record", display_cols)

    def _fetch_data(self):
        return self.biz.get_all_class_records()

    def on_add(self):
        dialog = ClassDialog(self.winfo_toplevel(), self.biz, "新增上课记录")
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = ClassDialog(self.winfo_toplevel(), self.biz, "编辑上课记录", row)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        class_id = row.get("上课编号", "")
        if messagebox.askyesno("确认删除", f"确定要删除上课记录 {class_id} 吗？\n此操作不可恢复！"):
            result = self.biz.delete_class_record(row["_row"])
            messagebox.showinfo("提示", result.get("message", "操作成功"))
            self.refresh_data()


class ClassDialog(tk.Toplevel):
    """上课记录新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.title(title)
        self.geometry("600x550")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.members = self.biz.get_member_id_names()
        self.courses = self.biz.get_course_id_names()
        self.staff = self.biz.get_staff_id_names()
        self.build_ui()
        if self.is_edit:
            self.load_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("会员", ttk.Combobox,
             {"values": list(self.members.values()) if self.members else ["无"], "state": "readonly"}),
            ("授课教练", ttk.Combobox,
             {"values": list(self.staff.values()) if self.staff else ["无"], "state": "readonly"}),
            ("课程", ttk.Combobox,
             {"values": list(self.courses.values()) if self.courses else ["无"], "state": "readonly"}),
            ("上课时间", tk.Entry, {}),
            ("下课时间", tk.Entry, {}),
            ("消耗课时数", tk.Entry, {}),
            ("上课评价", ttk.Combobox, {"values": ["非常满意", "满意", "一般", "不满意"], "state": "readonly"}),
            ("会员反馈", tk.Entry, {}),
            ("课程内容摘要", tk.Entry, {}),
        ]

        self.widgets = {}
        for i, (label, wtype, opts) in enumerate(fields):
            ttk.Label(main, text=label + "：", font=("微软雅黑", 10)).grid(row=i, column=0, sticky=tk.W, pady=4)
            if wtype == ttk.Combobox:
                w = wtype(main, font=("微软雅黑", 10), width=35, **opts)
            else:
                w = wtype(main, font=("微软雅黑", 10), width=37)
            w.grid(row=i, column=1, sticky=tk.W, pady=4, padx=(5, 0))
            self.widgets[label] = w

        # 默认值
        self.widgets["消耗课时数"].insert(0, "1")
        self.widgets["上课评价"].set("满意")
        if not self.is_edit:
            self.widgets["上课时间"].insert(0, "09:00")
            self.widgets["下课时间"].insert(0, "10:00")

        # 信息提示
        ttk.Label(main, text=f"📅 上课日期：{date.today().strftime('%Y-%m-%d')}",
                  font=("微软雅黑", 9), foreground="#666666").grid(
            row=len(fields), column=0, columnspan=2, pady=10)

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """加载现有数据到表单"""
        member_id = self.data.get("会员编号", "")
        member_val = self.members.get(member_id, "")
        if member_val:
            self.widgets["会员"].set(member_val)

        coach_name = self.data.get("授课教练", "")
        if coach_name and coach_name in self.staff.values():
            self.widgets["授课教练"].set(coach_name)

        course_id = self.data.get("课程编号", "")
        course_val = self.courses.get(course_id, "")
        if course_val:
            self.widgets["课程"].set(course_val)

        field_map = {"上课时间": "上课时间", "下课时间": "下课时间",
                     "消耗课时数": "消耗课时数", "会员反馈": "会员反馈",
                     "课程内容摘要": "课程内容摘要"}
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if val is not None:
                w = self.widgets[label]
                w.delete(0, tk.END)
                w.insert(0, str(val))

        rating = self.data.get("上课评价", "")
        if rating in ["非常满意", "满意", "一般", "不满意"]:
            self.widgets["上课评价"].set(rating)

    def on_save(self):
        member_str = self.widgets["会员"].get()
        coach_str = self.widgets["授课教练"].get()
        course_str = self.widgets["课程"].get()

        if not member_str or not course_str:
            messagebox.showwarning("提示", "请选择会员和课程")
            return

        try:
            data = {
                "会员编号": next((m for m, n in self.members.items() if n == member_str), ""),
                "会员姓名": member_str.split(" - ")[-1] if " - " in member_str else member_str,
                "授课教练": coach_str,
                "课程编号": next((c for c, n in self.courses.items() if n == course_str), ""),
                "课程名称": course_str.split(" - ")[-1] if " - " in course_str else course_str,
                "上课时间": self.widgets["上课时间"].get(),
                "下课时间": self.widgets["下课时间"].get(),
                "消耗课时数": float(self.widgets["消耗课时数"].get() or 1),
                "上课评价": self.widgets["上课评价"].get(),
                "会员反馈": self.widgets["会员反馈"].get(),
                "课程内容摘要": self.widgets["课程内容摘要"].get(),
                "教练上课提成比例": 0.07,
            }
            if self.is_edit:
                result = self.biz.update_class_record(self.data["_row"], data)
            else:
                result = self.biz.add_class_record(data)
            if result["success"]:
                messagebox.showinfo("成功", result.get("message", "操作成功"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("message", "操作成功"))
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
