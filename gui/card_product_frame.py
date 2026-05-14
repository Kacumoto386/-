"""
可售会籍卡产品目录管理 UI
用于门店自定义可售会籍卡（卡产品），售卡时可从已设置的卡中选择
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gui.base_frame import BaseDataFrame
from config import CARD_PRODUCT_STATUSES, CARD_PRODUCT_TYPES


class CardProductFrame(BaseDataFrame):
    """可售会籍卡管理"""

    def __init__(self, parent, biz):
        display_cols = [
            ("卡产品编号", 140), ("卡名称", 100), ("卡类型", 70),
            ("标准售价", 80), ("总次数", 70), ("有效天数", 70),
            ("储值金额", 80), ("状态", 60), ("创建日期", 100),
            ("所属门店", 80), ("备注", 150),
        ]
        super().__init__(parent, biz, "📋 可售会籍卡设置", "card_product", display_cols)

    def _fetch_data(self):
        """获取数据"""
        return self.biz.get_all_card_products()

    def on_add(self):
        """新增可售会籍卡"""
        dialog = CardProductDialog(
            self.winfo_toplevel(), self.biz, "新增可售会籍卡"
        )
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_edit(self):
        """编辑选中行"""
        row = self.get_selected_row()
        if not row:
            return
        dialog = CardProductDialog(
            self.winfo_toplevel(), self.biz, "编辑可售会籍卡", row
        )
        self.winfo_toplevel().wait_window(dialog)
        self.refresh_data()

    def on_delete(self):
        """删除选中行"""
        self.confirm_and_delete(
            "确认删除此卡产品？",
            "删除后售卡时不再可选，已售出的会籍卡不受影响",
        )

    def _do_delete(self, row):
        """执行删除"""
        self.biz.delete_card_product(row.get("_row"))


class CardProductDialog(tk.Toplevel):
    """可售会籍卡新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.title(title)
        self.geometry("460x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.build_ui()
        if data:
            self._load_data()

    def build_ui(self):
        """构建表单"""
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 卡名称
        ttk.Label(main, text="卡名称 *", font=("微软雅黑", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=4)
        self.name_var = tk.StringVar()
        tk.Entry(main, textvariable=self.name_var,
                 font=("微软雅黑", 10), width=32).grid(
            row=0, column=1, sticky=tk.W, pady=4, padx=(5, 0))

        # 卡类型
        ttk.Label(main, text="卡类型 *", font=("微软雅黑", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=4)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(main, textvariable=self.type_var,
                                        values=CARD_PRODUCT_TYPES,
                                        font=("微软雅黑", 10), width=30, state="readonly")
        self.type_combo.set("次卡")
        self.type_combo.grid(row=1, column=1, sticky=tk.W, pady=4, padx=(5, 0))
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

        # 标准售价
        ttk.Label(main, text="标准售价 *", font=("微软雅黑", 10)).grid(
            row=2, column=0, sticky=tk.W, pady=4)
        self.price_var = tk.StringVar(value="0")
        tk.Entry(main, textvariable=self.price_var,
                 font=("微软雅黑", 10), width=32).grid(
            row=2, column=1, sticky=tk.W, pady=4, padx=(5, 0))

        # 分隔线
        sep = ttk.Separator(main, orient=tk.HORIZONTAL)
        sep.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=8)

        ttk.Label(main, text="● 卡参数（按卡类型填写）",
                  font=("微软雅黑", 10, "bold"),
                  foreground="#1F4E79").grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # 动态参数区
        self.param_frame = ttk.LabelFrame(main, text="参数设置")
        self.param_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        # 总次数（次卡/通卡）
        self.count_label = ttk.Label(self.param_frame, text="总次数：", font=("微软雅黑", 10))
        self.count_var = tk.StringVar(value="0")
        self.count_entry = tk.Entry(self.param_frame, textvariable=self.count_var,
                                     font=("微软雅黑", 10), width=20)
        self.count_label2 = ttk.Label(self.param_frame, text="次", font=("微软雅黑", 9),
                                       foreground="#888")

        # 有效天数（期限卡/通卡）
        self.days_label = ttk.Label(self.param_frame, text="有效天数：", font=("微软雅黑", 10))
        self.days_var = tk.StringVar(value="0")
        self.days_entry = tk.Entry(self.param_frame, textvariable=self.days_var,
                                    font=("微软雅黑", 10), width=20)
        self.days_label2 = ttk.Label(self.param_frame, text="天", font=("微软雅黑", 9),
                                      foreground="#888")

        # 储值金额（现金卡/通卡）
        self.amount_label = ttk.Label(self.param_frame, text="储值金额：", font=("微软雅黑", 10))
        self.amount_var = tk.StringVar(value="0")
        self.amount_entry = tk.Entry(self.param_frame, textvariable=self.amount_var,
                                      font=("微软雅黑", 10), width=20)
        self.amount_label2 = ttk.Label(self.param_frame, text="元", font=("微软雅黑", 9),
                                        foreground="#888")

        self._on_type_change()

        # 状态
        ttk.Label(main, text="状态：", font=("微软雅黑", 10)).grid(
            row=6, column=0, sticky=tk.W, pady=4)
        self.status_var = tk.StringVar(value="上架")
        status_combo = ttk.Combobox(main, textvariable=self.status_var,
                                     values=CARD_PRODUCT_STATUSES,
                                     font=("微软雅黑", 10), width=30, state="readonly")
        status_combo.grid(row=6, column=1, sticky=tk.W, pady=4, padx=(5, 0))

        # 所属门店
        ttk.Label(main, text="所属门店：", font=("微软雅黑", 10)).grid(
            row=7, column=0, sticky=tk.W, pady=4)
        self.store_var = tk.StringVar()
        self.store_combo = ttk.Combobox(main, textvariable=self.store_var,
                                         font=("微软雅黑", 10), width=30, state="readonly")
        self.store_combo.grid(row=7, column=1, sticky=tk.W, pady=4, padx=(5, 0))
        self.store_combo["values"] = ["（全局可用）"]
        self.store_var.set("（全局可用）")

        # 备注
        ttk.Label(main, text="备  注：", font=("微软雅黑", 10)).grid(
            row=8, column=0, sticky=tk.W, pady=4)
        self.note_var = tk.StringVar()
        tk.Entry(main, textvariable=self.note_var,
                 font=("微软雅黑", 10), width=32).grid(
            row=8, column=1, sticky=tk.W, pady=4, padx=(5, 0))

        # 按钮区
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=15)

        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _on_type_change(self, event=None):
        """卡类型切换 → 显示/隐藏参数"""
        ct = self.type_var.get()

        # 先隐藏所有
        for w in [self.count_label, self.count_entry, self.count_label2,
                  self.days_label, self.days_entry, self.days_label2,
                  self.amount_label, self.amount_entry, self.amount_label2]:
            w.grid_forget()

        row = 0
        if ct in ("次卡", "通卡"):
            self.count_label.grid(row=row, column=0, sticky=tk.W, pady=3)
            self.count_entry.grid(row=row, column=1, sticky=tk.W, pady=3, padx=5)
            self.count_label2.grid(row=row, column=2, sticky=tk.W, pady=3)
            row += 1

        if ct in ("期限卡", "通卡"):
            self.days_label.grid(row=row, column=0, sticky=tk.W, pady=3)
            self.days_entry.grid(row=row, column=1, sticky=tk.W, pady=3, padx=5)
            self.days_label2.grid(row=row, column=2, sticky=tk.W, pady=3)
            row += 1

        if ct in ("现金卡", "通卡"):
            self.amount_label.grid(row=row, column=0, sticky=tk.W, pady=3)
            self.amount_entry.grid(row=row, column=1, sticky=tk.W, pady=3, padx=5)
            self.amount_label2.grid(row=row, column=2, sticky=tk.W, pady=3)

    def _load_data(self):
        """编辑模式：填入现有数据"""
        self.name_var.set(self.data.get("卡名称", ""))
        self.type_var.set(self.data.get("卡类型", ""))
        self.price_var.set(str(self.data.get("标准售价", 0)))
        self.count_var.set(str(self.data.get("总次数", 0)))
        self.days_var.set(str(self.data.get("有效天数", 0)))
        self.amount_var.set(str(self.data.get("储值金额", 0)))
        self.status_var.set(self.data.get("状态", "上架"))
        store = self.data.get("所属门店", "")
        self.store_var.set(store if store else "（全局可用）")
        self.note_var.set(self.data.get("备注", ""))
        self._on_type_change()

    def on_save(self):
        """保存"""
        name = self.name_var.get().strip()
        card_type = self.type_var.get()
        price_text = self.price_var.get().strip()

        if not name:
            messagebox.showwarning("提示", "请填写卡名称")
            return
        if not card_type:
            messagebox.showwarning("提示", "请选择卡类型")
            return

        try:
            price = float(price_text) if price_text else 0
        except ValueError:
            messagebox.showwarning("提示", "标准售价必须为数字")
            return

        count = 0
        days = 0
        amount = 0.0
        try:
            if card_type in ("次卡", "通卡"):
                count = int(self.count_var.get()) if self.count_var.get() else 0
            if card_type in ("期限卡", "通卡"):
                days = int(self.days_var.get()) if self.days_var.get() else 0
            if card_type in ("现金卡", "通卡"):
                amount = float(self.amount_var.get()) if self.amount_var.get() else 0
        except ValueError:
            messagebox.showwarning("提示", "参数必须为数字")
            return

        store = self.store_var.get()
        if store == "（全局可用）":
            store = ""

        data = {
            "卡名称": name,
            "卡类型": card_type,
            "标准售价": price,
            "总次数": count,
            "有效天数": days,
            "储值金额": amount,
            "状态": self.status_var.get(),
            "所属门店": store,
            "备注": self.note_var.get().strip(),
        }

        if self.data:
            result = self.biz.update_card_product(self.data["_row"], data)
        else:
            result = self.biz.add_card_product(data)

        if result.get("success"):
            messagebox.showinfo("成功", result.get("message", "操作成功"))
            self.destroy()
        else:
            messagebox.showerror("失败", result.get("error", "操作失败"))
