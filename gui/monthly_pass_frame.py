# -*- coding: utf-8 -*-
"""
包月团课 - GUI
V2.12.0
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


class MonthlyPassFrame(ttk.Frame):
    """包月团课管理界面"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self._all_passes = []
        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="🎫 包月团课管理",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=15, pady=5)

        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.LEFT)

        tk.Button(btn_frame, text="➕ 购买月卡",
                  font=("微软雅黑", 10),
                  bg="#9B59B6", fg="white",
                  padx=12, pady=3, bd=0, cursor="hand2",
                  command=self._on_buy).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔄 刷新",
                  font=("微软雅黑", 10),
                  bg="#E0E0E0", fg="#333333",
                  padx=12, pady=3, bd=0, cursor="hand2",
                  command=self.refresh_data).pack(side=tk.LEFT, padx=2)

        # 会员筛选
        filter_frame = ttk.Frame(toolbar)
        filter_frame.pack(side=tk.RIGHT)
        ttk.Label(filter_frame, text="按会员:").pack(side=tk.LEFT, padx=2)
        self._member_var = tk.StringVar()
        members = self.biz.get_member_id_names()
        member_values = ["全部"] + list(members.values())
        self._member_combo = ttk.Combobox(filter_frame, textvariable=self._member_var,
                                           values=member_values, width=20, state="readonly")
        self._member_combo.set("全部")
        self._member_combo.pack(side=tk.LEFT, padx=2)
        self._member_combo.bind("<<ComboboxSelected>>", lambda e: self._filter_data())

        # 表格
        cols = ("月卡编号", "月卡名称", "会员姓名", "课程名称列表",
                "售价", "有效期起", "有效期止", "状态")
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        col_widths = [140, 120, 80, 250, 70, 90, 90, 70]
        for col, w in zip(cols, col_widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, minwidth=60)

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_label = ttk.Label(self, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(fill=tk.X, padx=15, pady=5)

        self.refresh_data()

    def refresh_data(self):
        self._all_passes = self.biz.get_all_monthly_passes()
        # 自动更新过期状态
        try:
            self.biz.update_monthly_pass_status()
            self._all_passes = self.biz.get_all_monthly_passes()
        except Exception:
            pass
        self._filter_data()

    def _filter_data(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        member_filter = self._member_var.get()
        passes = self._all_passes
        if member_filter and member_filter != "全部":
            # 从 member_id_names 查
            for mid, mname in self.biz.get_member_id_names().items():
                if mname == member_filter:
                    passes = [p for p in passes if p.get("会员编号") == mid]
                    break

        def sort_key(p):
            status = p.get("状态", "")
            order = {"有效": 0, "已过期": 1, "已停用": 2}
            return order.get(status, 9)

        passes.sort(key=sort_key)

        for p in passes:
            valid_from = str(p.get("有效期起", ""))[:10]
            valid_to = str(p.get("有效期止", ""))[:10]
            values = (
                p.get("月卡编号", ""),
                p.get("月卡名称", ""),
                p.get("会员姓名", ""),
                p.get("课程名称列表", ""),
                f"¥{float(p.get('售价',0) or 0):.0f}",
                valid_from,
                valid_to,
                p.get("状态", ""),
            )
            item = self._tree.insert("", tk.END, values=values)
            status = p.get("状态", "")
            if status == "已过期":
                self._tree.item(item, tags=("expired",))
            elif status == "已停用":
                self._tree.item(item, tags=("stopped",))

        self._tree.tag_configure("expired", foreground="#FF0000")
        self._tree.tag_configure("stopped", foreground="#999999")
        self.status_label.config(text=f"📊 {len(passes)} 条记录")

    def _on_buy(self):
        dlg = MonthlyPassBuyDialog(self.winfo_toplevel(), self.biz)
        self.winfo_toplevel().wait_window(dlg)
        if dlg.result:
            messagebox.showinfo("成功", dlg.result)
            self.refresh_data()


class MonthlyPassBuyDialog(tk.Toplevel):
    """购买包月团课弹窗"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.result = None
        self.title("🎫 购买包月团课")
        self.geometry("500x400")
        self.resizable(False, False)
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill="both", expand=True)

        # 会员选择
        ttk.Label(f, text="选择会员:").pack(anchor="w", pady=(0, 2))
        self._member_var = tk.StringVar()
        members = self.biz.get_member_id_names()
        member_values = list(members.values())
        self._member_combo = ttk.Combobox(f, textvariable=self._member_var,
                                           values=member_values,
                                           width=30, state="readonly")
        self._member_combo.pack(anchor="w")

        # 月卡名称
        ttk.Label(f, text="月卡名称:").pack(anchor="w", pady=(10, 2))
        self._name_entry = ttk.Entry(f, width=33)
        self._name_entry.pack(anchor="w")
        self._name_entry.insert(0, "团课月卡")

        # 售价
        ttk.Label(f, text="售价:").pack(anchor="w", pady=(10, 2))
        self._price_entry = ttk.Entry(f, width=33)
        self._price_entry.pack(anchor="w")
        self._price_entry.insert(0, "399")

        # 有效期(天)
        ttk.Label(f, text="有效期(天):").pack(anchor="w", pady=(10, 2))
        self._days_entry = ttk.Entry(f, width=33)
        self._days_entry.pack(anchor="w")
        self._days_entry.insert(0, "30")

        # 课程选择
        ttk.Label(f, text="选择包含的课程(可多选):").pack(anchor="w", pady=(10, 2))
        self._course_frame = ttk.Frame(f)
        self._course_frame.pack(anchor="w", fill="x")
        self._course_vars = {}
        courses = self.biz.get_all_courses()
        for c in courses:
            ctype = c.get("课程类型", "")
            # 团课/大班课/小班课
            if "团课" in ctype or "大班" in ctype or "小班" in ctype:
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(self._course_frame,
                                     text=f"{c.get('课程名称','')} ({c.get('课程编号','')})",
                                     variable=var)
                cb.pack(anchor="w")
                self._course_vars[c.get("课程编号", "")] = var

        btn_frame = ttk.Frame(f)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="购买", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="left", padx=10)

    def _save(self):
        name = self._member_var.get()
        if not name:
            messagebox.showwarning("提示", "请选择会员")
            return

        members = self.biz.get_all_members()
        mid = mname = ""
        for m in members:
            if m.get("姓名") == name or f"{m.get('姓名')} - {m.get('会员编号')}" == name:
                mid = m.get("会员编号", "")
                mname = m.get("姓名", "")
                break

        if not mid:
            for k, v in self.biz.get_member_id_names().items():
                if v == name:
                    mid = k
                    mname = v.rsplit(" - ", 1)[0] if " - " in v else v
                    break

        if not mid:
            messagebox.showwarning("错误", "无法识别会员")
            return

        selected = [cid for cid, var in self._course_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("提示", "请至少选择一个课程")
            return

        pass_name = self._name_entry.get().strip() or "团课月卡"
        price = self._price_entry.get().strip() or "0"
        days = self._days_entry.get().strip() or "30"

        data = {
            "月卡名称": pass_name,
            "会员编号": mid,
            "会员姓名": mname,
            "包含课程": ",".join(selected),
            "售价": float(price),
            "有效期(天)": int(days),
        }
        result = self.biz.add_monthly_pass(data)
        if result.get("success"):
            self.result = result.get("message", "购买成功")
        else:
            messagebox.showwarning("错误", result.get("error", "购买失败"))
            return
        self.destroy()
