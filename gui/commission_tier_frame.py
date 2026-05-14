"""
梯度提成配置管理界面
支持新增/编辑/删除梯度规则，预览计算结果
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from config import COMMISSION_TIER_TYPES


class CommissionTierFrame(ttk.Frame):
    """梯度提成配置管理"""

    def __init__(self, parent, biz):
        super().__init__(parent)
        self.biz = biz
        self.build_ui()
        self.load_data()

    def build_ui(self):
        # 顶部标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="📊 梯度提成配置",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        tk.Button(header, text="➕ 新增规则", font=("微软雅黑", 9),
                  bg="#4472C4", fg="white", padx=12, pady=2, bd=0, cursor="hand2",
                  command=self.on_add).pack(side=tk.RIGHT, padx=5)
        tk.Button(header, text="🔄 刷新", font=("微软雅黑", 9),
                  bg="#70AD47", fg="white", padx=12, pady=2, bd=0, cursor="hand2",
                  command=self.load_data).pack(side=tk.RIGHT, padx=5)

        # 类型切换
        type_frame = ttk.Frame(self)
        type_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(type_frame, text="提成类型：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.type_var = tk.StringVar(value=COMMISSION_TIER_TYPES[0])
        type_menu = ttk.Combobox(type_frame, textvariable=self.type_var,
                                 values=COMMISSION_TIER_TYPES, state="readonly",
                                 width=12, font=("微软雅黑", 10))
        type_menu.pack(side=tk.LEFT, padx=5)
        type_menu.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        # 预览区
        preview_frame = ttk.Frame(self)
        preview_frame.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(preview_frame, text="预览计算：",
                  font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.preview_entry = tk.Entry(preview_frame, font=("微软雅黑", 10), width=12)
        self.preview_entry.pack(side=tk.LEFT, padx=5)
        self.preview_entry.insert(0, "50000")

        tk.Button(preview_frame, text="🔍 试算", font=("微软雅黑", 9),
                  bg="#FFC000", fg="#333", padx=10, pady=1, bd=0, cursor="hand2",
                  command=self.on_preview).pack(side=tk.LEFT, padx=3)

        self.preview_label = tk.Label(preview_frame, text="",
                                      font=("微软雅黑", 9), fg="#4472C4", anchor=tk.W)
        self.preview_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # 说明文字
        info_text = "💡 规则说明：梯度按「分段累进」计算，先匹配低档再匹配高档，同档次内全部按该档提成率计算"
        ttk.Label(self, text=info_text, font=("微软雅黑", 9),
                  foreground="#666666").pack(anchor=tk.W, padx=15, pady=(0, 5))

        # 主表格
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("梯度名称", "类型", "下限", "上限", "提成率", "排序号", "状态")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)

        col_widths = [150, 100, 100, 100, 100, 80, 80]
        col_anchors = [tk.W, tk.W, tk.E, tk.E, tk.E, tk.CENTER, tk.CENTER]
        for col, w, anc in zip(columns, col_widths, col_anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=60, anchor=anc)

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

        tk.Button(btn_frame, text="✏️ 编辑", font=("微软雅黑", 10),
                  bg="#4472C4", fg="white", padx=15, pady=3, bd=0, cursor="hand2",
                  command=self.on_edit).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ 删除", font=("微软雅黑", 10),
                  bg="#D9534F", fg="white", padx=15, pady=3, bd=0, cursor="hand2",
                  command=self.on_delete).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """加载当前类型的梯度规则"""
        tier_type = self.type_var.get()
        rules = self.biz.get_tier_rules(tier_type, only_enabled=False)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in rules:
            lower = r.get("下限", 0)
            upper = r.get("上限", "")
            rate = r.get("提成率", 0)
            sort_order = r.get("排序号", 99)

            # 格式化
            lower_str = f"{self._to_num(lower):,.0f}" if lower else "0"
            upper_str = f"{self._to_num(upper):,.0f}" if upper and str(upper).strip() else "∞"
            rate_str = f"{self._to_num(rate)*100:.1f}%"

            values = (
                r.get("梯度名称", ""),
                r.get("类型", ""),
                lower_str,
                upper_str,
                rate_str,
                int(self._to_num(sort_order)),
                r.get("状态", "启用"),
            )
            self.tree.insert("", tk.END, values=values, tags=(r.get("_row"),))

        self.tree.tag_configure("even", background="#F5F5F5")

    def _to_num(self, val):
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0

    def get_selected_row(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条梯度规则")
            return None
        item = selection[0]
        index = self.tree.index(item)
        rules = self.biz.get_tier_rules(self.type_var.get(), only_enabled=False)
        if 0 <= index < len(rules):
            return rules[index]
        return None

    def on_add(self):
        dialog = CommissionTierDialog(self.winfo_toplevel(), self.biz, "新增梯度规则",
                                      default_type=self.type_var.get())
        self.winfo_toplevel().wait_window(dialog)
        self.load_data()

    def on_edit(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = CommissionTierDialog(self.winfo_toplevel(), self.biz, "编辑梯度规则", row)
        self.winfo_toplevel().wait_window(dialog)
        self.load_data()

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return
        name = row.get("梯度名称", "")
        if not messagebox.askyesno("确认删除", f"确定删除梯度规则「{name}」吗？"):
            return
        result = self.biz.delete_tier_rule(row["_row"])
        messagebox.showinfo("成功", result.get("message", "已删除"))
        self.load_data()

    def on_preview(self):
        """预览计算"""
        try:
            value = float(self.preview_entry.get().strip() or "0")
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的数字")
            return

        tier_type = self.type_var.get()
        if value <= 0:
            self.preview_label.config(text="请输入大于0的数值")
            return

        # 快速匹配
        name, rate = self.biz.match_tier_rate(tier_type, value)[:2]
        # 精确计算
        result = self.biz.calculate_tier_commission(tier_type, value)

        segments_text = " + ".join(
            f"{s['range']}×{s['rate']*100:.1f}%=¥{s['commission']:,.0f}"
            for s in result["segments"]
        )
        self.preview_label.config(
            text=f"试算结果：{value:,.0f} → 综合提成率 {result['rate']*100:.1f}% → "
                 f"提成 ¥{result['total_commission']:,.0f} | {segments_text}"
        )


class CommissionTierDialog(tk.Toplevel):
    """梯度规则新增/编辑对话框"""

    def __init__(self, parent, biz, title, data=None, default_type=None):
        super().__init__(parent)
        self.biz = biz
        self.data = data
        self.is_edit = data is not None
        self.title(title)
        self.geometry("450x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.default_type = default_type
        self.build_ui()
        if self.is_edit:
            self.load_data()

    def build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        fields = [
            ("梯度名称", tk.Entry, {}),
            ("类型", ttk.Combobox, {
                "values": COMMISSION_TIER_TYPES, "state": "readonly"}),
            ("下限", tk.Entry, {"tip": "该档次的最小值（含）"}),
            ("上限", tk.Entry, {"tip": "该档次的最大值（不含），留空表示无上限"}),
            ("提成率", tk.Entry, {"tip": "例如输入 0.08 表示 8%"}),
            ("排序号", tk.Entry, {"tip": "数字越小越优先匹配"}),
            ("状态", ttk.Combobox, {
                "values": ["启用", "停用"], "state": "readonly"}),
            ("备注", tk.Entry, {}),
        ]

        self.widgets = {}
        for i, (label, widget_type, options) in enumerate(fields):
            frame = ttk.Frame(main)
            frame.pack(fill=tk.X, pady=3)

            left = ttk.Frame(frame, width=80)
            left.pack(side=tk.LEFT, fill=tk.X)
            ttk.Label(left, text=label + "：",
                      font=("微软雅黑", 10), anchor=tk.W).pack(anchor=tk.W)

            right = ttk.Frame(frame)
            right.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

            if widget_type == ttk.Combobox:
                w = widget_type(right, font=("微软雅黑", 10), width=28, **options)
            else:
                w = widget_type(right, font=("微软雅黑", 10), width=30)

            w.pack(fill=tk.X)

            if "tip" in options:
                tip_label = ttk.Label(frame, text=options["tip"],
                                      font=("微软雅黑", 8), foreground="#999")
                tip_label.pack(anchor=tk.W, padx=(85, 0))

            self.widgets[label] = w

        # 初始化默认值
        if not self.is_edit:
            if self.default_type:
                self.widgets["类型"].set(self.default_type)
            else:
                self.widgets["类型"].set(COMMISSION_TIER_TYPES[0])
            self.widgets["状态"].set("启用")
            self.widgets["排序号"].delete(0, tk.END)
            self.widgets["排序号"].insert(0, "10")

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="✅ 保存", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ 取消", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """加载现有数据到表单"""
        field_map = {
            "梯度名称": "梯度名称", "类型": "类型", "下限": "下限",
            "上限": "上限", "提成率": "提成率", "排序号": "排序号",
            "状态": "状态", "备注": "备注",
        }
        for label, field in field_map.items():
            val = self.data.get(field, "")
            if val is None:
                val = ""
            w = self.widgets[label]
            if isinstance(w, ttk.Combobox):
                w.set(str(val))
            else:
                w.delete(0, tk.END)
                if field == "提成率":
                    w.insert(0, str(val))
                elif field == "排序号":
                    w.insert(0, str(int(val)) if val else "10")
                else:
                    w.insert(0, str(val))

    def on_save(self):
        """保存"""
        data = {}
        for label, w in self.widgets.items():
            val = w.get().strip() if isinstance(w, tk.Entry) else w.get()
            data[label] = val

        # 校验
        if not data.get("梯度名称"):
            messagebox.showwarning("提示", "梯度名称不能为空")
            return

        # 数字字段转换
        try:
            data["下限"] = float(data.get("下限", 0) or 0)
        except ValueError:
            data["下限"] = 0.0

        try:
            data["提成率"] = float(data.get("提成率", 0) or 0)
        except ValueError:
            data["提成率"] = 0.0

        try:
            data["排序号"] = int(data.get("排序号", 99) or 99)
        except ValueError:
            data["排序号"] = 99

        if data["提成率"] <= 0:
            messagebox.showwarning("提示", "提成率必须大于0")
            return

        try:
            if self.is_edit:
                result = self.biz.update_tier_rule(self.data["_row"], data)
            else:
                result = self.biz.add_tier_rule(data)
            if result.get("success"):
                messagebox.showinfo("成功", result.get("message", "保存成功"))
                self.destroy()
            else:
                messagebox.showerror("错误", result.get("error", "保存失败"))
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
