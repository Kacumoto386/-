"""
员工管理模块
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from gui.base_frame import BaseDataFrame


class StaffFrame(BaseDataFrame):
    """员工管理"""

    def __init__(self, parent, biz):
        display_cols = [
            ("员工编号", 100), ("姓名", 80), ("性别", 50),
            ("岗位", 100), ("手机号", 120), ("员工状态", 70),
            ("售课提成比例", 100), ("上课提成比例", 100), ("底薪", 80),
            ("本月售课金额", 110), ("本月上课节数", 100), ("本月总提成", 100),
        ]
        super().__init__(parent, biz, "👨💼 员工管理", "staff", display_cols)

    def _fetch_data(self):
        return self.biz.get_staff_with_stats()

    def on_add(self):
        dialog = StaffDialog(self.winfo_toplevel(), self.biz, "新增员工")
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = StaffDialog(self.winfo_toplevel(), self.biz, "编辑员工", row)
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        name = row.get("姓名", "")
        staff_id = row.get("员工编号", "")
        self.confirm_and_delete(
            delete_func=lambda: self.biz.delete_staff(row["_row"], staff_id),
            item_desc=f"员工 {name} ({staff_id})"
        )


class StaffDialog(tk.Toplevel):
    """员工新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.title(title)
        self.geometry("550x500")
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
            ("姓名", tk.Entry, {}),
            ("性别", ttk.Combobox, {"values": ["男", "女"], "state": "readonly"}),
            ("岗位", ttk.Combobox, {"values": ["销售顾问", "健身教练", "瑜伽教练", "游泳教练", "操课教练", "店长", "前台"], "state": "readonly"}),
            ("手机号", tk.Entry, {}),
            ("生日", tk.Entry, {}),
            ("入职日期", tk.Entry, {}),
            ("邮箱", tk.Entry, {}),
            ("授课资质", tk.Entry, {}),
            ("售课提成比例", tk.Entry, {}),
            ("上课提成比例", tk.Entry, {}),
            ("底薪", tk.Entry, {}),
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

        # 默认值
        if not self.is_edit:
            self.widgets["性别"].set("男")
            self.widgets["岗位"].set("健身教练")
            self.widgets["入职日期"].insert(0, date.today().strftime("%Y-%m-%d"))
            self.widgets["售课提成比例"].insert(0, "0.08")
            self.widgets["上课提成比例"].insert(0, "0.07")
            self.widgets["底薪"].insert(0, "3000")

        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        field_map = {"姓名": "姓名", "性别": "性别", "岗位": "岗位", "手机号": "手机号",
                     "生日": "生日", "入职日期": "入职日期", "邮箱": "邮箱",
                     "授课资质": "授课资质", "售课提成比例": "售课提成比例",
                     "上课提成比例": "上课提成比例", "底薪": "底薪"}
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if isinstance(val, (date, datetime)):
                val = val.strftime("%Y-%m-%d")
            if val is not None:
                w = self.widgets[label]
                if isinstance(w, ttk.Combobox):
                    w.set(str(val))
                else:
                    w.delete(0, tk.END)
                    w.insert(0, str(val))

    def get_form_data(self):
        data = {}
        for label, w in self.widgets.items():
            val = w.get().strip() if isinstance(w, tk.Entry) else w.get()
            if label in ("生日", "入职日期") and val:
                try:
                    val = datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    val = date.today()
            elif label in ("售课提成比例", "上课提成比例"):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = 0.08
            elif label == "底薪":
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = 0
            data[label] = val

        return {
            "姓名": data.get("姓名", ""),
            "性别": data.get("性别", ""),
            "岗位": data.get("岗位", ""),
            "手机号": data.get("手机号", ""),
            "生日": data.get("生日"),
            "入职日期": data.get("入职日期", date.today()),
            "邮箱": data.get("邮箱", ""),
            "授课资质": data.get("授课资质", ""),
            "售课提成比例": data.get("售课提成比例", 0.08),
            "上课提成比例": data.get("上课提成比例", 0.07),
            "底薪": data.get("底薪", 3000),
        }

    def on_save(self):
        form_data = self.get_form_data()
        if not form_data["姓名"]:
            messagebox.showwarning("提示", "姓名不能为空")
            return
        if not form_data["手机号"]:
            messagebox.showwarning("提示", "手机号不能为空")
            return
        try:
            if self.is_edit:
                result = self.biz.update_staff(self.data["_row"], form_data)
            else:
                result = self.biz.add_staff(form_data)
            if result["success"]:
                messagebox.showinfo("成功", result.get("message", "操作成功"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("message", "操作成功"))
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
