# -*- coding: utf-8 -*-
"""
合同管理 — GUI
V2.6.0
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from gui.base_frame import BaseDataFrame
from core.contract import ContractManager


class ContractFrame(BaseDataFrame):
    """合同管理界面"""

    def __init__(self, parent, biz):
        self.contract_mgr = ContractManager(biz)
        super().__init__(parent, biz, "合同管理", "contract", [])
        self._build_custom_ui()

    def _build_custom_ui(self):
        # Clear default content and rebuild
        for w in self.winfo_children():
            w.destroy()

        # ── 顶部工具栏 ──
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=8)

        ttk.Button(toolbar, text="➕ 新增合同", command=self._add_contract).pack(side="left", padx=2)
        ttk.Button(toolbar, text="✅ 签署", command=self._sign).pack(side="left", padx=2)
        ttk.Button(toolbar, text="❌ 作废", command=self._void).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔄 刷新", command=self._load_data).pack(side="left", padx=2)

        ttk.Label(toolbar, text="搜索:").pack(side="left", padx=(20, 5))
        self._search_entry = ttk.Entry(toolbar, width=20)
        self._search_entry.pack(side="left")
        self._search_entry.bind("<Return>", lambda e: self._search())
        ttk.Button(toolbar, text="搜索", command=self._search).pack(side="left", padx=2)
        ttk.Button(toolbar, text="清空", command=self._load_data).pack(side="left", padx=2)

        # ── 统计信息 ──
        self._stats_label = ttk.Label(toolbar, text="", font=("微软雅黑", 9))
        self._stats_label.pack(side="right", padx=10)

        # ── 合同表格 ──
        cols = ("合同编号", "会员姓名", "合同类型", "合同金额", "签署状态",
                "签署日期", "有效期起", "有效期止", "签署方式", "备注")
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        widths = [120, 80, 100, 80, 80, 100, 100, 100, 80, 120]
        for col, w in zip(cols, widths):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="center")
        self._tree.column("合同金额", anchor="e")
        self._tree.column("备注", anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._tree.bind("<Double-1>", lambda e: self._edit())

        # ── 底部到期提醒 ──
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(bottom, text="📅 近30天到期合同:", font=("微软雅黑", 9, "bold")).pack(side="left")
        self._expiring_label = ttk.Label(bottom, text="", font=("微软雅黑", 9))
        self._expiring_label.pack(side="left", padx=10)

        self._load_data()

    def _load_data(self):
        self._all_contracts = self.contract_mgr.get_all_contracts()

        for item in self._tree.get_children():
            self._tree.delete(item)

        for c in self._all_contracts:
            amount = c.get("合同金额", 0) or 0
            try:
                amount_str = f"¥{float(amount):.2f}"
            except (ValueError, TypeError):
                amount_str = str(amount)
            self._tree.insert("", "end", values=(
                c.get("合同编号", ""),
                c.get("会员姓名", ""),
                c.get("合同类型", ""),
                amount_str,
                c.get("签署状态", ""),
                str(c.get("签署日期", ""))[:10] if c.get("签署日期") else "",
                str(c.get("有效期起", ""))[:10] if c.get("有效期起") else "",
                str(c.get("有效期止", ""))[:10] if c.get("有效期止") else "",
                c.get("签署方式", ""),
                (c.get("备注", "") or "")[:15],
            ))

        # 更新统计
        stats = self.contract_mgr.get_contract_stats()
        self._stats_label.config(
            text=f"共 {stats['total']} 份 | 已签署 {stats['signed']} | "
                 f"待签署 {stats['pending']} | 已作废 {stats['voided']}"
        )

        # 到期提醒
        expiring = self.contract_mgr.get_expiring_contracts(30)
        if expiring:
            expired = [e for e in expiring if e.get("剩余天数", 0) == 0]
            upcoming = [e for e in expiring if e.get("剩余天数", 0) > 0]
            parts = []
            if expired:
                parts.append(f"🔴 {len(expired)}份已到期")
            if upcoming:
                parts.append(f"🟡 {len(upcoming)}份即将到期")
            self._expiring_label.config(text=", ".join(parts))
        else:
            self._expiring_label.config(text="无")

    def _search(self):
        kw = self._search_entry.get().strip()
        if not kw:
            self._load_data()
            return
        results = self.contract_mgr.search_contracts(kw)
        for item in self._tree.get_children():
            self._tree.delete(item)
        for c in results:
            amount = c.get("合同金额", 0) or 0
            try:
                amount_str = f"¥{float(amount):.2f}"
            except (ValueError, TypeError):
                amount_str = str(amount)
            self._tree.insert("", "end", values=(
                c.get("合同编号", ""), c.get("会员姓名", ""),
                c.get("合同类型", ""), amount_str,
                c.get("签署状态", ""),
                str(c.get("签署日期", ""))[:10] if c.get("签署日期") else "",
                str(c.get("有效期起", ""))[:10] if c.get("有效期起") else "",
                str(c.get("有效期止", ""))[:10] if c.get("有效期止") else "",
                c.get("签署方式", ""),
                (c.get("备注", "") or "")[:15],
            ))

    def _get_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择一条合同")
            return None
        item = self._tree.item(sel[0])
        contract_id = item["values"][0]
        return self.contract_mgr.get_contract(contract_id)

    def _add_contract(self):
        dlg = ContractEditDialog(self, self.biz, None)
        self.wait_window(dlg)
        if dlg.result:
            self.contract_mgr.add_contract(dlg.result)
            self._load_data()

    def _edit(self):
        c = self._get_selected()
        if not c:
            return
        dlg = ContractEditDialog(self, self.biz, c)
        self.wait_window(dlg)
        if dlg.result:
            self.contract_mgr.update_contract(c["_row"], dlg.result)
            self._load_data()

    def _sign(self):
        c = self._get_selected()
        if not c:
            return
        if c.get("签署状态") == "已签署":
            messagebox.showinfo("提示", "该合同已签署")
            return
        if messagebox.askyesno("确认签署", f"确认签署合同 {c['合同编号']}?"):
            self.contract_mgr.sign_contract(c["合同编号"])
            self._load_data()

    def _void(self):
        c = self._get_selected()
        if not c:
            return
        if c.get("签署状态") == "已作废":
            messagebox.showinfo("提示", "该合同已作废")
            return
        if messagebox.askyesno("确认作废", f"确认作废合同 {c['合同编号']}?"):
            self.contract_mgr.void_contract(c["合同编号"])
            self._load_data()


class ContractEditDialog(tk.Toplevel):
    """合同编辑/新增弹窗"""

    def __init__(self, parent, biz, contract=None):
        super().__init__(parent)
        self.biz = biz
        self.contract = contract
        self.result = None
        self.title("编辑合同" if contract else "新增合同")
        self.geometry("500x560")
        self.resizable(False, False)
        self._build()

    def _build(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill="both", expand=True)

        fields = [
            ("合同类型", ttk.Combobox),
            ("会员编号", ttk.Entry),
            ("会员姓名", ttk.Entry),
            ("合同金额", ttk.Entry),
            ("合同内容摘要", ttk.Entry),
            ("有效期起", ttk.Entry),
            ("有效期止", ttk.Entry),
            ("签署方式", ttk.Combobox),
            ("门店编号", ttk.Entry),
            ("操作员", ttk.Entry),
            ("备注", ttk.Entry),
            ("附件路径", ttk.Entry),
        ]

        self._widgets = {}
        row = 0
        for label, wtype in fields:
            ttk.Label(f, text=label + ":").grid(row=row, column=0, sticky="w", pady=3, padx=(0, 5))
            if wtype == ttk.Combobox:
                if label == "合同类型":
                    values = ["入会协议", "私教合同", "商品购买", "免责声明", "其他"]
                elif label == "签署方式":
                    values = ["纸质", "电子", "扫码"]
                else:
                    values = []
                w = wtype(f, values=values, state="readonly" if values else "normal", width=25)
            else:
                w = wtype(f, width=28)
            w.grid(row=row, column=1, sticky="w", pady=3)
            self._widgets[label] = w
            row += 1

        # Populate if editing
        if self.contract:
            for label, w in self._widgets.items():
                key = label.replace(" ", "")
                val = self.contract.get(key, "")
                if isinstance(val, datetime.datetime):
                    val = val.strftime("%Y-%m-%d")
                if w.__class__.__name__ == "Combobox":
                    if str(val) in w["values"]:
                        w.set(str(val))
                else:
                    w.delete(0, tk.END)
                    w.insert(0, str(val) if val else "")

        # Buttons
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="保存", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side="left", padx=10)

    def _save(self):
        data = {}
        key_map = {
            "合同类型": "合同类型", "会员编号": "会员编号", "会员姓名": "会员姓名",
            "合同金额": "合同金额", "合同内容摘要": "合同内容摘要",
            "有效期起": "有效期起", "有效期止": "有效期止",
            "签署方式": "签署方式", "门店编号": "门店编号",
            "操作员": "操作员", "备注": "备注", "附件路径": "附件路径",
        }
        for label, w in self._widgets.items():
            key = key_map.get(label, label)
            if w.__class__.__name__ == "Combobox":
                val = w.get()
            else:
                val = w.get().strip()
            if key == "合同金额":
                try:
                    val = float(val) if val else 0
                except ValueError:
                    messagebox.showwarning("输入错误", "合同金额必须为数字")
                    return
            data[key] = val

        if not data.get("合同类型"):
            messagebox.showwarning("输入错误", "请选择合同类型")
            return
        if not data.get("会员姓名"):
            messagebox.showwarning("输入错误", "请输入会员姓名")
            return

        self.result = data
        self.destroy()
