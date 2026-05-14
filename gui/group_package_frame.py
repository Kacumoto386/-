# -*- coding: utf-8 -*-
"""
团课打包产品管理 - GUI
V2.12.0
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.base_frame import BaseDataFrame
from config import SHEETS, GROUP_PACKAGE_TYPES, GROUP_PACKAGE_STATUSES


class GroupPackageFrame(BaseDataFrame):
    """团课打包产品管理界面"""

    def __init__(self, parent, biz):
        super().__init__(parent, biz, "📦 团课打包产品", "group_package", [
            ("打包编号", 140), ("打包名称", 140), ("课程名称列表", 240),
            ("打包类型", 80), ("总次数", 60),
            ("标准售价", 80), ("优惠售价", 80), ("有效期(天)", 80),
            ("状态", 60), ("创建日期", 100),
        ])
        self._add_custom_toolbar()

    def _add_custom_toolbar(self):
        """在工具栏追加按钮"""
        # 找工具栏frame
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Frame):
                        btn_frame = sub
                        tk.Button(btn_frame, text="🔗 售出打包",
                                  font=("微软雅黑", 10),
                                  bg="#E67E22", fg="white",
                                  padx=10, pady=3, bd=0, cursor="hand2",
                                  command=self._on_sell).pack(side=tk.LEFT, padx=2)
                        return

    def _fetch_data(self):
        return self.biz.get_all_group_packages()

    def on_add(self):
        dlg = GroupPackageEditDialog(self.winfo_toplevel(), self.biz, "新增团课打包产品")
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result:
            self.refresh_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dlg = GroupPackageEditDialog(self.winfo_toplevel(), self.biz,
                                      "编辑团课打包产品", row)
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result:
            self.refresh_data()

    def _on_sell(self):
        row = self.get_selected_row()
        if not row:
            messagebox.showinfo("提示", "请先选择一个打包产品")
            return
        dlg = GroupPackageSellDialog(self.winfo_toplevel(), self.biz, row)
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result:
            messagebox.showinfo("成功", dlg.result)
            self.refresh_data()


class GroupPackageEditDialog(tk.Toplevel):
    """团课打包产品编辑弹窗"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.result = None
        self.title(title)
        self.geometry("550x500")
        self.resizable(False, False)
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill="both", expand=True)

        fields = [
            ("打包名称", ttk.Entry, ""),
            ("打包类型", ttk.Combobox, GROUP_PACKAGE_TYPES),
            ("总次数", ttk.Entry, "0"),
            ("标准售价", ttk.Entry, "0"),
            ("优惠售价", ttk.Entry, "0"),
            ("有效期(天)", ttk.Entry, "30"),
            ("状态", ttk.Combobox, GROUP_PACKAGE_STATUSES),
            ("备注", ttk.Entry, ""),
        ]

        self._widgets = {}
        for i, (label, wtype, extra) in enumerate(fields):
            ttk.Label(f, text=label + ":").grid(row=i, column=0, sticky="w", pady=3, padx=(0, 5))
            if wtype == ttk.Combobox:
                w = ttk.Combobox(f, values=extra, state="readonly", width=30)
                if extra:
                    w.set(extra[0])
            else:
                w = ttk.Entry(f, width=33)
            w.grid(row=i, column=1, sticky="w", pady=3)
            self._widgets[label] = w

        # 课程多选区域
        ttk.Label(f, text="包含课程(团课):").grid(row=len(fields), column=0, sticky="nw", pady=5)
        self._course_frame = ttk.Frame(f)
        self._course_frame.grid(row=len(fields), column=1, sticky="w", pady=5)
        self._course_vars = {}
        courses = self.biz.get_all_courses()
        for c in courses:
            ctype = c.get("课程类型", "")
            # 只显示团课类型
            if "团课" in ctype or "大班" in ctype or "小班" in ctype:
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(self._course_frame, text=f"{c.get('课程名称','')} ({c.get('课程编号','')})",
                                     variable=var)
                cb.pack(anchor="w")
                self._course_vars[c.get("课程编号", "")] = (var, c.get("课程名称", ""))

        # 填充已有数据
        if self.data:
            self._widgets["打包名称"].insert(0, self.data.get("打包名称", ""))
            self._widgets["打包类型"].set(self.data.get("打包类型", ""))
            self._widgets["总次数"].delete(0, "end")
            self._widgets["总次数"].insert(0, str(self.data.get("总次数", 0)))
            self._widgets["标准售价"].delete(0, "end")
            self._widgets["标准售价"].insert(0, str(self.data.get("标准售价", 0)))
            self._widgets["优惠售价"].delete(0, "end")
            self._widgets["优惠售价"].insert(0, str(self.data.get("优惠售价", 0)))
            self._widgets["有效期(天)"].delete(0, "end")
            self._widgets["有效期(天)"].insert(0, str(self.data.get("有效期(天)", 30)))
            self._widgets["状态"].set(self.data.get("状态", "上架"))
            self._widgets["备注"].insert(0, self.data.get("备注", ""))
            # 勾选已有课程
            exist_ids = [x.strip() for x in self.data.get("包含课程", "").split(",") if x.strip()]
            for cid, (var, _) in self._course_vars.items():
                if cid in exist_ids:
                    var.set(True)

        # 打包类型切换：计次打包显示次数，不限次数隐藏次数
        self._widgets["打包类型"].bind("<<ComboboxSelected>>", self._on_type_change)
        self._on_type_change()

        btn_frame = ttk.Frame(f)
        row = len(fields) + 1
        btn_frame.grid(row=row, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="left", padx=10)

    def _on_type_change(self, event=None):
        ptype = self._widgets["打包类型"].get()
        if ptype == "不限次数":
            self._widgets["总次数"].config(state="disabled")
        else:
            self._widgets["总次数"].config(state="normal")

    def _save(self):
        name = self._widgets["打包名称"].get().strip()
        if not name:
            messagebox.showwarning("输入错误", "打包名称不能为空")
            return

        # 收集选中的课程
        selected = []
        for cid, (var, cname) in self._course_vars.items():
            if var.get():
                selected.append(cid)
        if not selected:
            messagebox.showwarning("输入错误", "请至少选择一个课程")
            return

        ptype = self._widgets["打包类型"].get()
        total = self._widgets["总次数"].get().strip() or "0"

        data = {
            "打包名称": name,
            "包含课程": ",".join(selected),
            "打包类型": ptype,
            "总次数": int(total) if total else 0,
            "标准售价": float(self._widgets["标准售价"].get().strip() or 0),
            "优惠售价": float(self._widgets["优惠售价"].get().strip() or 0),
            "有效期(天)": int(self._widgets["有效期(天)"].get().strip() or 30),
            "状态": self._widgets["状态"].get(),
            "备注": self._widgets["备注"].get().strip(),
        }

        if self.data:
            row_num = self.data.get("_row")
            self.biz.update_group_package(row_num, data)
            self.result = True
        else:
            result = self.biz.add_group_package(data)
            if result.get("success"):
                self.result = True
            else:
                messagebox.showwarning("错误", result.get("error", "未知错误"))
                return
        self.destroy()


class GroupPackageSellDialog(tk.Toplevel):
    """售出打包产品弹窗"""

    def __init__(self, parent, biz, pkg_row):
        super().__init__(parent)
        self.biz = biz
        self.pkg_row = pkg_row
        self.result = None
        self.title(f"售出打包 - {pkg_row.get('打包名称', '')}")
        self.geometry("400x250")
        self.resizable(False, False)
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text=f"打包产品: {self.pkg_row.get('打包名称', '')}",
                  font=("微软雅黑", 11, "bold")).pack(anchor="w", pady=5)
        ttk.Label(f, text=f"包含: {self.pkg_row.get('课程名称列表', '')}").pack(anchor="w", pady=2)
        ttk.Label(f, text=f"总次数: {self.pkg_row.get('总次数', 0)} / 有效期: {self.pkg_row.get('有效期(天)', 30)}天").pack(anchor="w", pady=2)

        ttk.Label(f, text="选择会员:").pack(anchor="w", pady=(10, 2))
        self._member_var = tk.StringVar()
        members = self.biz.get_member_id_names()
        member_values = list(members.values())
        self._member_combo = ttk.Combobox(f, textvariable=self._member_var,
                                           values=member_values,
                                           width=30, state="readonly")
        self._member_combo.pack(anchor="w")

        btn_frame = ttk.Frame(f)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="售出", command=self._sell).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="left", padx=10)

    def _sell(self):
        name = self._member_var.get()
        if not name:
            messagebox.showwarning("提示", "请选择会员")
            return
        # 从 "姓名 - M编号" 格式提取
        members = self.biz.get_all_members()
        mid = ""
        mname = ""
        for m in members:
            if m.get("姓名") == name or f"{m.get('姓名')} - {m.get('会员编号')}" == name:
                mid = m.get("会员编号", "")
                mname = m.get("姓名", "")
                break
        if not mid:
            # 尝试从 member_id_names 解析
            for k, v in self.biz.get_member_id_names().items():
                if v == name:
                    mid = k
                    mname = v.rsplit(" - ", 1)[0] if " - " in v else v
                    break

        if not mid:
            messagebox.showwarning("错误", "无法识别会员")
            return

        result = self.biz.sell_group_package(mid, mname, self.pkg_row.get("打包编号", ""))
        if result.get("success"):
            self.result = result.get("message", "售出成功")
        else:
            messagebox.showwarning("错误", result.get("error", "售出失败"))
            return
        self.destroy()
