"""
商品零售界面 - 购物车模式
支持多商品选购加入购物车、优惠金额、会员储值余额支付
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SHEETS, PAYMENT_METHODS


class ProductSaleFrame(ttk.Frame):
    """商品零售管理界面（购物车模式）"""

    def __init__(self, parent, biz, store_mgr=None, store_id=None):
        super().__init__(parent)
        self.biz = biz
        self.store_mgr = store_mgr or getattr(biz, 'store_mgr', None)
        self.store_id = store_id
        self._all_sales = []
        # 购物车数据
        self.cart = []  # [{商品编号, 商品名称, 数量, 单价, 小计, 库存剩余}, ...]
        self._products_cache = {}
        self._members_cache = []
        self.build_ui()
        self.refresh_data()

    # ==================== UI 构建 ====================

    def build_ui(self):
        """构建界面"""
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        ttk.Label(header, text="🛒 商品零售（购物车模式）",
                  font=("微软雅黑", 16, "bold"), foreground="#1F4E79").pack(side=tk.LEFT)

        # ========= 购物车操作区（三栏布局） =========
        cart_container = ttk.Frame(self)
        cart_container.pack(fill=tk.X, padx=15, pady=5)

        # --- 左栏：商品选择区 ---
        self._build_select_panel(cart_container)

        # --- 中栏：购物车列表 ---
        self._build_cart_panel(cart_container)

        # --- 右栏：结算区 ---
        self._build_checkout_panel(cart_container)

        # 分隔线
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=8)

        # ========= 零售记录表格 =========
        self._build_history_table()

    def _build_select_panel(self, container):
        """左侧：商品选择区"""
        frame = ttk.LabelFrame(container, text="① 选择商品", padding=10)
        frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        # 商品下拉
        ttk.Label(frame, text="商品：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.product_combo = ttk.Combobox(frame, font=("微软雅黑", 10), state="readonly")
        self.product_combo.pack(fill=tk.X, pady=2)
        self.product_combo.bind("<<ComboboxSelected>>", self._on_product_select)

        # 商品信息
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, pady=3)
        self.stock_label = ttk.Label(info_frame, text="库存：--", font=("微软雅黑", 9), foreground="#666")
        self.stock_label.pack(side=tk.LEFT, padx=(0, 10))
        self.price_label = ttk.Label(info_frame, text="单价：--", font=("微软雅黑", 9), foreground="#CC4400")
        self.price_label.pack(side=tk.LEFT)

        # 数量
        qty_frame = ttk.Frame(frame)
        qty_frame.pack(fill=tk.X, pady=5)
        ttk.Label(qty_frame, text="数量：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.quantity_spin = tk.Spinbox(qty_frame, from_=1, to=999, font=("微软雅黑", 10), width=8)
        self.quantity_spin.pack(side=tk.LEFT, padx=2)
        self.quantity_spin.delete(0, tk.END)
        self.quantity_spin.insert(0, "1")

        # 加入购物车按钮
        self.btn_add_cart = tk.Button(frame, text="🛒 加入购物车",
                                      font=("微软雅黑", 10, "bold"),
                                      bg="#4472C4", fg="white",
                                      padx=10, pady=5, bd=0, cursor="hand2",
                                      command=self._add_to_cart)
        self.btn_add_cart.pack(fill=tk.X, pady=(10, 2))

        # 快捷刷新商品
        tk.Button(frame, text="🔄 刷新商品", font=("微软雅黑", 9),
                  bg="#E0E0E0", fg="#333", padx=5, pady=2, bd=0, cursor="hand2",
                  command=self._refresh_product_combo).pack(fill=tk.X, pady=2)

    def _build_cart_panel(self, container):
        """中间：购物车列表"""
        frame = ttk.LabelFrame(container, text="② 购物车", padding=5)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 购物车表格
        columns = ["商品名称", "数量", "单价", "小计"]
        self.cart_tree = ttk.Treeview(frame, columns=columns, show="headings",
                                      height=8, selectmode="browse")
        col_widths = [150, 60, 70, 80]
        for col, w in zip(columns, col_widths):
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=w, minwidth=50)

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=scroll.set)
        self.cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 购物车操作
        cart_btn_frame = ttk.Frame(frame)
        cart_btn_frame.pack(fill=tk.X, pady=3)
        tk.Button(cart_btn_frame, text="🗑️ 删除选中", font=("微软雅黑", 9),
                  bg="#FF6B6B", fg="white", padx=8, pady=2, bd=0, cursor="hand2",
                  command=self._remove_from_cart).pack(side=tk.LEFT, padx=2)
        tk.Button(cart_btn_frame, text="🧹 清空购物车", font=("微软雅黑", 9),
                  bg="#E0E0E0", fg="#333", padx=8, pady=2, bd=0, cursor="hand2",
                  command=self._clear_cart).pack(side=tk.LEFT, padx=2)

    def _build_checkout_panel(self, container):
        """右侧：结算区"""
        frame = ttk.LabelFrame(container, text="③ 结算", padding=10)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # 会员选择
        ttk.Label(frame, text="会员：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.member_combo = ttk.Combobox(frame, font=("微软雅黑", 10), state="readonly")
        self.member_combo.pack(fill=tk.X, pady=2)
        self.member_combo.bind("<<ComboboxSelected>>", self._on_member_select)

        # 会员储值余额
        self.balance_label = ttk.Label(frame, text="储值余额：--",
                                       font=("微软雅黑", 9), foreground="#2E75B6")
        self.balance_label.pack(anchor=tk.W, pady=2)

        # 金额汇总
        summary_frame = ttk.Frame(frame)
        summary_frame.pack(fill=tk.X, pady=5)

        ttk.Label(summary_frame, text="合计金额：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.total_label = ttk.Label(summary_frame, text="¥0",
                                     font=("微软雅黑", 12, "bold"), foreground="#CC4400")
        self.total_label.pack(side=tk.LEFT, padx=5)

        # 优惠金额
        disc_frame = ttk.Frame(frame)
        disc_frame.pack(fill=tk.X, pady=2)
        ttk.Label(disc_frame, text="优惠金额：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
        self.discount_entry = tk.Entry(disc_frame, font=("微软雅黑", 10), width=12)
        self.discount_entry.pack(side=tk.LEFT, padx=2)
        self.discount_entry.insert(0, "0")
        self.discount_entry.bind("<KeyRelease>", self._on_discount_change)

        # 应付金额
        pay_frame = ttk.Frame(frame)
        pay_frame.pack(fill=tk.X, pady=2)
        ttk.Label(pay_frame, text="应付金额：", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
        self.pay_label = ttk.Label(pay_frame, text="¥0",
                                   font=("微软雅黑", 14, "bold"), foreground="#CC4400")
        self.pay_label.pack(side=tk.LEFT, padx=5)

        # 支付方式
        ttk.Label(frame, text="支付方式：", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(5, 0))
        self.payment_combo = ttk.Combobox(frame, font=("微软雅黑", 10),
                                          values=PAYMENT_METHODS, state="readonly")
        self.payment_combo.pack(fill=tk.X, pady=2)
        self.payment_combo.set("微信")

        # 使用储值复选框
        self.use_balance_var = tk.BooleanVar(value=False)
        self.use_balance_cb = tk.Checkbutton(frame, text="使用储值余额支付",
                                             variable=self.use_balance_var,
                                             font=("微软雅黑", 9),
                                             command=self._on_balance_toggle)
        self.use_balance_cb.pack(anchor=tk.W, pady=3)

        # 操作员
        ttk.Label(frame, text="操作员：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.operator_entry = tk.Entry(frame, font=("微软雅黑", 10))
        self.operator_entry.pack(fill=tk.X, pady=2)

        # 备注
        ttk.Label(frame, text="备注：", font=("微软雅黑", 10)).pack(anchor=tk.W)
        self.remark_entry = tk.Entry(frame, font=("微软雅黑", 10))
        self.remark_entry.pack(fill=tk.X, pady=2)

        # 确认结算按钮
        self.btn_checkout = tk.Button(frame, text="💵 确认结算",
                                      font=("微软雅黑", 11, "bold"),
                                      bg="#4472C4", fg="white",
                                      padx=15, pady=6, bd=0, cursor="hand2",
                                      command=self._on_checkout)
        self.btn_checkout.pack(fill=tk.X, pady=(8, 0))

    def _build_history_table(self):
        """底部：零售记录历史表格"""
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        ttk.Label(table_frame, text="📋 零售记录", font=("微软雅黑", 12, "bold"),
                  foreground="#1F4E79").pack(anchor=tk.W, pady=(0, 3))

        columns = ["零售编号", "零售日期", "会员姓名", "商品名称", "数量", "单价", "总价",
                    "优惠金额", "支付方式", "操作员", "备注"]
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        col_widths = [150, 95, 80, 130, 55, 55, 75, 70, 80, 70, 120]
        for col, w in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, minwidth=50)

        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # 底部操作栏
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=15, pady=(0, 8))

        self.btn_delete = tk.Button(action_frame, text="🗑️ 删除记录",
                                    font=("微软雅黑", 10), bg="#FF0000", fg="white",
                                    padx=12, pady=3, bd=0, cursor="hand2",
                                    command=self._on_delete_history)
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        self.btn_refresh = tk.Button(action_frame, text="🔄 刷新",
                                     font=("微软雅黑", 10), bg="#E0E0E0", fg="#333",
                                     padx=12, pady=3, bd=0, cursor="hand2",
                                     command=self.refresh_data)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(action_frame, text="", font=("微软雅黑", 9), foreground="#999")
        self.status_label.pack(side=tk.RIGHT)

        self.current_row = None
        self.row_data = []

    # ==================== 购物车逻辑 ====================

    def _add_to_cart(self):
        """将商品加入购物车"""
        name = self.product_combo.get()
        if not name:
            messagebox.showwarning("提示", "请先选择商品")
            return
        if name not in self._products_cache:
            messagebox.showerror("错误", "商品数据异常，请刷新")
            return

        product = self._products_cache[name]
        product_id = product.get("商品编号", "")
        stock = float(product.get("库存数量", 0) or 0)

        try:
            qty_str = self.quantity_spin.get().strip()
            qty = int(float(qty_str)) if qty_str else 0
        except (ValueError, TypeError):
            qty = 1

        if qty <= 0:
            messagebox.showwarning("提示", "数量必须大于0")
            return

        # 检查购物车中已有的数量 + 新数量 <= 库存
        cart_qty = sum(item["数量"] for item in self.cart if item["商品名称"] == name)
        if cart_qty + qty > stock:
            messagebox.showwarning("库存不足",
                                   f"「{name}」库存剩余 {stock}，\n"
                                   f"购物车已有 {cart_qty}，最多还能加 {stock - cart_qty}")
            return

        price = float(product.get("售价", 0) or 0)

        # 如果购物车已有该商品，追加数量
        for item in self.cart:
            if item["商品名称"] == name:
                item["数量"] += qty
                item["小计"] = item["数量"] * item["单价"]
                item["库存剩余"] = stock
                self._refresh_cart_tree()
                self._update_checkout_summary()
                return

        # 新增到购物车
        self.cart.append({
            "商品编号": product_id,
            "商品名称": name,
            "数量": qty,
            "单价": price,
            "小计": qty * price,
            "库存剩余": stock,
        })
        self._refresh_cart_tree()
        self._update_checkout_summary()

    def _remove_from_cart(self):
        """从购物车删除选中项"""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先在购物车中选择要删除的商品")
            return
        idx = self.cart_tree.index(selection[0])
        if idx < len(self.cart):
            self.cart.pop(idx)
            self._refresh_cart_tree()
            self._update_checkout_summary()

    def _clear_cart(self):
        """清空购物车"""
        if not self.cart:
            return
        if messagebox.askyesno("确认", "确定要清空购物车吗？"):
            self.cart.clear()
            self._refresh_cart_tree()
            self._update_checkout_summary()

    def _refresh_cart_tree(self):
        """刷新购物车表格"""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        for item in self.cart:
            self.cart_tree.insert("", tk.END, values=[
                item["商品名称"],
                item["数量"],
                f'¥{item["单价"]:.0f}',
                f'¥{item["小计"]:.0f}',
            ])

    # ==================== 结算逻辑 ====================

    def _update_checkout_summary(self, event=None):
        """更新结算区的金额汇总"""
        total = sum(item["小计"] for item in self.cart)
        try:
            discount = float(self.discount_entry.get() or 0)
        except (ValueError, TypeError):
            discount = 0
        if discount < 0:
            discount = 0
        if discount > total:
            discount = total

        pay = total - discount
        self.total_label.config(text=f"¥{total:.0f}")
        self.pay_label.config(text=f"¥{pay:.0f}")

    def _on_discount_change(self, event=None):
        """优惠金额输入时更新应付金额"""
        self._update_checkout_summary()

    def _on_member_select(self, event=None):
        """选择会员时查储值余额"""
        member_str = self.member_combo.get()
        member_id = member_str.split(" - ")[0] if " - " in member_str else ""
        if member_id:
            balance = self.biz.get_member_balance(member_id)
            self.balance_label.config(text=f"储值余额：¥{balance:.0f}")
        else:
            self.balance_label.config(text="储值余额：--")

    def _on_balance_toggle(self):
        """切换储值支付时更新应付金额"""
        self._update_checkout_summary()

    def _on_checkout(self):
        """确认结算"""
        if not self.cart:
            messagebox.showwarning("提示", "购物车为空，请先添加商品")
            return

        # 校验会员
        member_str = self.member_combo.get()
        member_id = member_str.split(" - ")[0] if " - " in member_str else ""
        member_name = member_str.split(" - ")[-1] if " - " in member_str else ""

        # 获取金额
        total = sum(item["小计"] for item in self.cart)
        try:
            discount = float(self.discount_entry.get() or 0)
        except (ValueError, TypeError):
            discount = 0
        if discount < 0:
            discount = 0
        if discount > total:
            discount = total
        pay = total - discount

        payment_method = self.payment_combo.get()
        operator = self.operator_entry.get().strip()
        remark = self.remark_entry.get().strip()

        # 储值支付逻辑
        use_balance = self.use_balance_var.get()
        balance = 0
        if use_balance:
            if not member_id:
                messagebox.showwarning("提示", "使用储值支付必须选择会员")
                return
            balance = self.biz.get_member_balance(member_id)
            if pay > balance:
                messagebox.showwarning("储值余额不足",
                                       f"应付 ¥{pay:.0f}，储值余额仅 ¥{balance:.0f}，\n请调整优惠金额或更换支付方式")
                return
            payment_method = "储值卡"

        # 确认对话框
        cart_summary = "\n".join(
            [f"  {item['商品名称']} × {item['数量']} = ¥{item['小计']:.0f}" for item in self.cart]
        )
        receipt = (
            f"🛒 结算确认\n\n"
            f"会员：{member_name or '(非会员)'}\n"
            f"{cart_summary}\n"
            f"合计：¥{total:.0f}\n"
            f"优惠：-¥{discount:.0f}\n"
            f"应付：¥{pay:.0f}\n"
            f"支付方式：{payment_method}\n"
        )
        if use_balance:
            receipt += f"使用储值：¥{pay:.0f}（余额 ¥{balance:.0f}）\n"

        if not messagebox.askyesno("确认结算", receipt):
            return

        # 优惠分摊：按金额比例分配到各商品
        discount_per_item = {}
        if discount > 0 and total > 0:
            for item in self.cart:
                ratio = item["小计"] / total
                discount_per_item[item["商品名称"]] = round(discount * ratio, 2)
        else:
            for item in self.cart:
                discount_per_item[item["商品名称"]] = 0

        # 执行结算
        errors = []
        sale_ids = []
        today = date.today().strftime("%Y-%m-%d")
        for item in self.cart:
            item_discount = discount_per_item.get(item["商品名称"], 0)
            result = self.biz.add_cart_product_sale({
                "商品编号": item["商品编号"],
                "数量": item["数量"],
                "零售价": item["单价"],
                "优惠金额": item_discount,
                "零售日期": today,
                "会员编号": member_id,
                "会员姓名": member_name,
                "支付方式": payment_method,
                "销售人员": operator,
                "备注": remark,
            })
            if result["success"]:
                sale_ids.append(result["sale_id"])
            else:
                errors.append(f"  {item['商品名称']}: {result['error']}")

        # 储值扣减
        if use_balance and pay > 0 and not errors:
            self.biz.deduct_member_balance(member_id, pay, operator)

        if errors:
            messagebox.showerror("部分失败", "以下商品结算失败：\n" + "\n".join(errors))
        else:
            msg = f"✅ 结算成功！共 {len(sale_ids)} 笔交易"
            if discount > 0:
                msg += f"，优惠 ¥{discount:.0f}"
            if use_balance:
                new_balance = balance - pay
                msg += f"，储值扣减 ¥{pay:.0f}（剩余 ¥{new_balance:.0f}）"
            messagebox.showinfo("成功", msg)

        # 清空购物车和表单
        self.cart.clear()
        self._refresh_cart_tree()
        self.member_combo.set("")
        self.balance_label.config(text="储值余额：--")
        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, "0")
        self.remark_entry.delete(0, tk.END)
        self.use_balance_var.set(False)
        self.use_balance_cb.config(text="使用储值余额支付")
        self._update_checkout_summary()
        self.refresh_data()

    # ==================== 数据加载 ====================

    def refresh_data(self):
        """刷新所有数据"""
        try:
            self._all_sales = self.biz.get_all_product_sales()
        except Exception:
            self._all_sales = []
        self._refresh_product_combo()
        self._refresh_member_combo()
        self._populate_history_tree()

    def _refresh_product_combo(self):
        """刷新商品下拉列表"""
        try:
            products = self.biz.get_all_products()
            # 只显示上架商品
            product_names = [p.get("商品名称", "") for p in products
                             if p.get("商品名称") and p.get("商品状态", "") != "下架"]
            self.product_combo["values"] = product_names
            self._products_cache = {p.get("商品名称"): p for p in products if p.get("商品名称")}
        except Exception:
            self._products_cache = {}
            self.product_combo["values"] = []
        if self.product_combo.get():
            self._on_product_select()

    def _refresh_member_combo(self):
        """刷新会员下拉列表"""
        try:
            members = self.biz.get_all_members()
            member_options = [f"{m.get('会员编号', '')} - {m.get('姓名', '')}" for m in members if m.get("会员编号")]
            self.member_combo["values"] = member_options
            self._members_cache = member_options
        except Exception:
            self.member_combo["values"] = []

    def _on_product_select(self, event=None):
        """选择商品时更新库存和单价"""
        name = self.product_combo.get()
        if name and name in self._products_cache:
            p = self._products_cache[name]
            stock = p.get("库存数量", 0)
            price = float(p.get("售价", 0) or 0)
            self.stock_label.config(text=f"库存：{stock} {p.get('单位', '个')}")
            self.price_label.config(text=f"单价：¥{price:.0f}")
        else:
            self.stock_label.config(text="库存：--")
            self.price_label.config(text="单价：--")

    def _populate_history_tree(self):
        """填充零售记录表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self._all_sales
        for row in rows:
            cols_display = ["零售编号", "零售日期", "会员姓名", "商品名称",
                            "数量", "单价", "总价", "优惠金额", "支付方式", "操作员", "备注"]
            values = []
            for col in cols_display:
                val = row.get(col, "")
                if val is None:
                    val = ""
                values.append(str(val))
            self.tree.insert("", tk.END, values=values)

        self.status_label.config(text=f"共 {len(rows)} 条零售记录")
        self.current_row = None
        self.row_data = rows

    def _on_delete_history(self):
        """删除选中零售记录"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条记录")
            return

        item = selection[0]
        index = self.tree.index(item)
        if index >= len(self.row_data):
            return

        row = self.row_data[index]
        sale_id = row.get("零售编号", "")
        if messagebox.askyesno("确认删除", f"确定要删除零售记录 {sale_id} 吗？\n库存将自动恢复。"):
            result = self.biz.delete_product_sale(row.get("_row"))
            messagebox.showinfo("提示", result.get("message", "操作成功"))
            self.refresh_data()
