"""
进场核销面板 - 嵌入首页看板顶部
支持：次卡扣次数、现金卡扣余额、期限卡签到、无卡进场
"""
import tkinter as tk
from tkinter import ttk, messagebox


class CheckinPanel(ttk.LabelFrame):
    """进场核销面板"""

    def __init__(self, parent, biz, **kwargs):
        super().__init__(parent, text="🎯 会员进场", **kwargs)
        self.biz = biz
        self._member_cache = None  # 当前查询到的会员数据
        self._cards_cache = []     # 当前会员的有效会籍卡
        self.build_ui()

    def build_ui(self):
        """构建进场核销面板"""
        # 使用两列布局：左（查询区）| 右（结果+操作）
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=5)

        # ===== 左：查询区 =====
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="nsew", padx=(5, 5), pady=5)

        ttk.Label(left, text="会员编号：", font=("微软雅黑", 10)).pack(anchor=tk.W)

        search_frame = ttk.Frame(left)
        search_frame.pack(fill=tk.X, pady=(3, 5))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=("微软雅黑", 14), width=18, bd=2,
                                     relief="solid", insertbackground="#4472C4")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda e: self._on_search())
        self.search_entry.focus_set()

        tk.Button(search_frame, text="🔍", font=("微软雅黑", 12),
                  bg="#4472C4", fg="white", padx=8, pady=2, bd=0, cursor="hand2",
                  command=self._on_search).pack(side=tk.RIGHT, padx=(5, 0))

        # 会员信息快捷显示
        self.member_info_var = tk.StringVar(value="输入会员编号扫码或回车查询")
        ttk.Label(left, textvariable=self.member_info_var,
                  font=("微软雅黑", 9), foreground="#888888",
                  wraplength=200).pack(anchor=tk.W, pady=(2, 0))

        # ── 刷卡/手环查询区 ──
        band_sep = ttk.Separator(left, orient=tk.HORIZONTAL)
        band_sep.pack(fill=tk.X, pady=(8, 5))

        ttk.Label(left, text="刷手环进场：", font=("微软雅黑", 9)).pack(anchor=tk.W)

        band_frame = ttk.Frame(left)
        band_frame.pack(fill=tk.X, pady=(3, 0))

        self.band_entry = tk.Entry(band_frame, font=("微软雅黑", 14), width=14,
                                   bd=2, relief="solid", insertbackground="#27AE60")
        self.band_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.band_entry.bind("<Return>", lambda e: self._on_band_search())
        self.band_entry.configure(state=tk.DISABLED)  # 初始禁用

        self.btn_band_mode = tk.Button(band_frame, text="\U0001f3f7 刷卡",
                                       font=("微软雅黑", 10),
                                       bg="#27AE60", fg="white",
                                       padx=6, pady=2, bd=0, cursor="hand2",
                                       command=self._toggle_band_mode)
        self.btn_band_mode.pack(side=tk.RIGHT, padx=(5, 0))

        self.band_mode_active = False

        # ===== 右：结果+操作 =====
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 5), pady=5)
        right.columnconfigure(1, weight=1)

        # 会籍卡选择 + 核销方式
        ttk.Label(right, text="核销方式：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=2)

        self.category_var = tk.StringVar(value="")
        self.category_combo = ttk.Combobox(right, textvariable=self.category_var,
                                           font=("微软雅黑", 10), width=12, state="readonly")
        self.category_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_change)

        # 会籍卡选择
        ttk.Label(right, text="选择会籍卡：", font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.card_var = tk.StringVar(value="")
        self.card_combo = ttk.Combobox(right, textvariable=self.card_var,
                                       font=("微软雅黑", 9), width=30, state="readonly")
        self.card_combo.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=2)

        # 卡片详情提示区（动态显示选中卡的当前状态）
        self.card_detail_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.card_detail_var,
                  font=("微软雅黑", 8), foreground="#E67E22",
                  wraplength=260).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=(5, 0), pady=(0, 2))

        # 消耗数量/金额输入框（动态显示）
        qty_frame = ttk.Frame(right)
        qty_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)
        qty_frame.columnconfigure(0, weight=1)

        self.qty_label = ttk.Label(qty_frame, text="消耗数量：", font=("微软雅黑", 10))
        self.qty_label.pack(side=tk.LEFT)

        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = tk.Entry(qty_frame, textvariable=self.qty_var,
                                  font=("微软雅黑", 10), width=8, bd=1, relief="solid")
        self.qty_entry.pack(side=tk.LEFT, padx=(3, 0))
        self.qty_label_caption = ttk.Label(qty_frame, text="次", font=("微软雅黑", 9),
                                           foreground="#888888")
        self.qty_label_caption.pack(side=tk.LEFT, padx=(2, 0))

        # 扣除预期提示（动态计算）
        self.deduct_preview_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.deduct_preview_var,
                  font=("微软雅黑", 9), foreground="#C0392B",
                  wraplength=260).grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=(5, 0), pady=(0, 2))

        # 上课员工（从管理门店员工数据中选）
        ttk.Label(right, text="跟进员工：", font=("微软雅黑", 10)).grid(row=5, column=0, sticky=tk.W, pady=2)
        self.coach_var = tk.StringVar(value="")
        self.coach_combo = ttk.Combobox(right, textvariable=self.coach_var,
                                        font=("微软雅黑", 9), width=15, state="normal")
        self.coach_combo.grid(row=5, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        # 服务课程名称
        ttk.Label(right, text="服务课程：", font=("微软雅黑", 10)).grid(row=6, column=0, sticky=tk.W, pady=2)
        self.course_var = tk.StringVar(value="进场签到")
        tk.Entry(right, textvariable=self.course_var,
                 font=("微软雅黑", 10), width=18, bd=1, relief="solid").grid(
            row=6, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        # 操作按钮
        btn_frame = ttk.Frame(right)
        btn_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=5)

        self.btn_checkin = tk.Button(btn_frame, text="✅ 确认进场", font=("微软雅黑", 11),
                                     bg="#27AE60", fg="white", padx=20, pady=4, bd=0,
                                     cursor="hand2", command=self._on_checkin)
        self.btn_checkin.pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="🔄 重置", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333333", padx=20, pady=4, bd=0,
                  cursor="hand2", command=self._on_reset).pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(btn_frame, text="", font=("微软雅黑", 9),
                                      foreground="#999999")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # 填充跟进员工列表
        self._load_all_staff()
        # 绑定数量输入实时预览
        self.bind_qty_change()

    def _load_all_staff(self):
        """加载所有在职员工（上课教练改为跟进员工）"""
        try:
            staff = self.biz.get_all_staff()
            # 只展示在职员工
            active = [s.get("姓名", "") for s in staff
                      if s.get("员工状态") in ("在职", "", None)]
            self.coach_combo["values"] = active or ["暂无员工"]
        except Exception:
            self.coach_combo["values"] = []

    def _on_search(self):
        """查询会员"""
        keyword = self.search_var.get().strip()
        if not keyword:
            return

        # 尝试按会员编号精确查找
        member = self.biz.get_member(keyword)
        if not member:
            # 试用手机号搜索
            members = self.biz.search_members(keyword)
            if members:
                member = members[0]
            else:
                self.member_info_var.set("⚠️ 未找到该会员")
                self._member_cache = None
                self._cards_cache = []
                self._clear_card_options()
                return

        self._member_cache = member
        mid = member.get("会员编号", "")
        name = member.get("姓名", "")
        level = member.get("会员等级", "")
        remaining = member.get("剩余课时", 0)

        self.member_info_var.set(f"👤 {name}（{level}） 剩余课时: {remaining}")

        # 查询该会员的有效会籍卡
        self._cards_cache = self.biz.get_member_valid_memberships(mid)

        # 更新会籍卡下拉选项
        card_options = []
        for c in self._cards_cache:
            ctype = c.get("卡类型", "")
            cname = c.get("卡名称", "")
            cid = c.get("会籍卡编号", "")
            if ctype == "次卡":
                remain = c.get("剩余次数", 0)
                card_options.append(f"【次卡】{cname} ({cid}) 剩余{remain}次")
            elif ctype == "现金卡":
                bal = c.get("余额", 0)
                card_options.append(f"【现金卡】{cname} ({cid}) 余额¥{bal}")
            elif ctype == "期限卡":
                card_options.append(f"【期限卡】{cname} ({cid})")

        self.card_combo["values"] = card_options
        if card_options:
            self.card_combo.current(0)

        # 绑定卡选择变更时更新详情提示
        self.card_combo.bind("<<ComboboxSelected>>", self._on_card_selected)

        # 更新核销方式下拉
        categories = []
        for c in self._cards_cache:
            ct = c.get("卡类型", "")
            if ct == "次卡" and "次卡" not in categories:
                categories.append("次卡")
            elif ct == "现金卡" and "现金卡" not in categories:
                categories.append("现金卡")
            elif ct == "期限卡" and "期限卡" not in categories:
                categories.append("期限卡")
        categories.append("无卡进场")

        self.category_combo["values"] = categories
        if categories:
            self.category_combo.current(0)
            self._on_category_change()

        # 更新卡片详情预览
        self._update_card_detail()
        self._update_deduct_preview()

        self.status_label.config(text="已查询到会员", foreground="#27AE60")

    def _toggle_band_mode(self):
        """切换刷卡模式"""
        self.band_mode_active = not self.band_mode_active
        if self.band_mode_active:
            self.btn_band_mode.configure(bg="#E74C3C", text="\u274c 关闭")
            self.band_entry.configure(state=tk.NORMAL)
            self.band_entry.focus_set()
            self.search_entry.configure(state=tk.DISABLED)
            self.member_info_var.set("\u2705 刷卡模式已开启，请刷手环")
        else:
            self.btn_band_mode.configure(bg="#27AE60", text="\U0001f3f7 刷卡")
            self.band_entry.configure(state=tk.DISABLED)
            self.search_entry.configure(state=tk.NORMAL)
            self.member_info_var.set("\u274c 刷卡模式已关闭")

    def _on_band_search(self):
        """手环刷卡查询"""
        reader_val = self.band_entry.get().strip()
        if not reader_val:
            return

        if not reader_val.isdigit():
            self.member_info_var.set("\u26a0\ufe0f 无效的手环数据（需为数字）")
            self.band_entry.delete(0, tk.END)
            return

        # 通过读卡器值查找手环
        band = self.biz.find_by_reader_value(reader_val)
        if not band:
            self.member_info_var.set("\u26a0\ufe0f 未识别的手环（请确认已注册）")
            self.band_entry.delete(0, tk.END)
            return

        member_id = band.get("绑定会员编号", "")
        if not member_id:
            self.member_info_var.set(f"\u26a0\ufe0f 手环 {band.get('手环编号','')} 未绑定会员")
            self.band_entry.delete(0, tk.END)
            return

        # 找到会员
        member = self.biz.get_member(member_id)
        if not member:
            self.member_info_var.set("\u26a0\ufe0f 绑定的会员不存在")
            self.band_entry.delete(0, tk.END)
            return

        self.band_entry.delete(0, tk.END)

        # 填充会员信息到进场面板（复用 _on_search 的会员查询逻辑）
        self.search_var.set(member_id)
        self._on_search()

        self.member_info_var.set(f"\U0001f3f7 手环识别成功 - {member.get('姓名','')}")

    def _clear_card_options(self):
        """清空会籍卡和核销方式选项"""
        self.category_combo["values"] = []
        self.category_var.set("")
        self.card_combo["values"] = []
        self.card_var.set("")

    def _on_category_change(self, event=None):
        """核销方式变更时，显示/隐藏相应的输入框"""
        category = self.category_var.get()
        if category == "次卡":
            self.qty_label.config(text="消耗次数：")
            self.qty_label_caption.config(text="次")
            self.qty_var.set("1")
            self.qty_entry.config(state="normal")
            # 默认选中第一张次卡
            self._select_card_by_type("次卡")
        elif category == "现金卡":
            self.qty_label.config(text="扣减金额：")
            self.qty_label_caption.config(text="元")
            self.qty_var.set("25")
            self.qty_entry.config(state="normal")
            self._select_card_by_type("现金卡")
        elif category == "期限卡":
            self.qty_label.config(text="消耗数量：")
            self.qty_label_caption.config(text="")
            self.qty_var.set("0")
            self.qty_entry.config(state="disabled")
            self._select_card_by_type("期限卡")
        elif category == "无卡进场":
            self.qty_label.config(text="消耗数量：")
            self.qty_label_caption.config(text="")
            self.qty_var.set("0")
            self.qty_entry.config(state="disabled")
            # 清空会籍卡
            self.card_var.set("")

        # 切换后更新详情提示
        self._update_card_detail()
        self._update_deduct_preview()

    def _select_card_by_type(self, card_type):
        """自动选中某类型的会籍卡"""
        card_values = self.card_combo["values"]
        for idx, val in enumerate(card_values):
            if val.startswith(f"【{card_type}】"):
                self.card_combo.current(idx)
                return
        self.card_var.set("")

    def _on_card_selected(self, event=None):
        """会籍卡选择变更：自动切换核销方式 + 更新详情"""
        card_text = self.card_var.get()
        if not card_text:
            return

        # 从卡片文本推断卡类型
        if card_text.startswith("【次卡】"):
            target_category = "次卡"
        elif card_text.startswith("【现金卡】"):
            target_category = "现金卡"
        elif card_text.startswith("【期限卡】"):
            target_category = "期限卡"
        else:
            return

        # 如果当前核销方式与卡片类型不一致，自动切换
        if self.category_var.get() != target_category:
            categories = self.category_combo["values"]
            if target_category in categories:
                self.category_var.set(target_category)
                self._on_category_change()
                return  # _on_category_change 会触发更新

        # 类型一致时仅更新详情
        self._update_card_detail()
        self._update_deduct_preview()

    def _update_card_detail(self):
        """更新卡片详情提示（当前选中卡的状态）"""
        category = self.category_var.get()
        card_text = self.card_var.get()
        self.card_detail_var.set("")

        if not card_text or category == "无卡进场":
            return

        # 从卡片缓存找匹配的卡片
        import re
        m = re.search(r'\((MC\d+)\)', card_text)
        if not m:
            return
        card_id = m.group(1)

        card = None
        for c in self._cards_cache:
            if c.get("会籍卡编号") == card_id:
                card = c
                break
        if not card:
            return

        ctype = card.get("卡类型", "")
        if ctype == "次卡":
            remain = card.get("剩余次数", 0)
            expired = card.get("到期日期", "")
            self.card_detail_var.set(
                f"📋 次卡剩余 {remain} 次" +
                (f"，有效期至 {expired}" if expired else "")
            )
        elif ctype == "现金卡":
            bal = card.get("余额", 0)
            self.card_detail_var.set(f"📋 现金卡余额 ¥{bal:.2f}")
        elif ctype == "期限卡":
            start = card.get("开卡日期", "")
            end = card.get("到期日期", "")
            if start and end:
                self.card_detail_var.set(f"📋 期限卡：{start} ~ {end}，有效期内不限次")
            else:
                self.card_detail_var.set("📋 期限卡：有效期内不限次")

    def _update_deduct_preview(self):
        """更新扣减预览提示"""
        category = self.category_var.get()
        qty_text = self.qty_var.get().strip()
        card_text = self.card_var.get()
        self.deduct_preview_var.set("")

        if not card_text or category == "无卡进场":
            self.deduct_preview_var.set("无卡进场，不扣费")
            return

        import re
        m = re.search(r'\((MC\d+)\)', card_text)
        if not m:
            return
        card_id = m.group(1)
        card = None
        for c in self._cards_cache:
            if c.get("会籍卡编号") == card_id:
                card = c
                break
        if not card:
            return

        if category == "次卡":
            try:
                deduct = int(qty_text) if qty_text else 1
            except ValueError:
                return
            remain = int(card.get("剩余次数", 0))
            after = remain - deduct
            if after < 0:
                self.deduct_preview_var.set(f"⚠️ 剩余 {remain} 次，不足 {deduct} 次！")
            else:
                self.deduct_preview_var.set(
                    f"扣除后剩余 {after} 次" if after > 0 else "⚠️ 本次用完即清空"
                )
        elif category == "现金卡":
            try:
                deduct = float(qty_text) if qty_text else 0
            except ValueError:
                return
            bal = float(card.get("余额", 0))
            after = bal - deduct
            if after < 0:
                self.deduct_preview_var.set(f"⚠️ 余额 ¥{bal:.2f}，不足 ¥{deduct:.2f}！")
            else:
                self.deduct_preview_var.set(
                    f"扣除后余额 ¥{after:.2f}" if after > 0 else "⚠️ 本次扣除后余额归零"
                )
        elif category == "期限卡":
            self.deduct_preview_var.set(f"期限卡签到，不扣费")

        # 绑定 qty 输入变化，实时更新预览
    def bind_qty_change(self):
        """绑定数量输入框的实时预览"""
        self.qty_var.trace_add("write",
                               lambda *a: self._update_deduct_preview())

    def _on_checkin(self):
        """确认进场核销"""
        if not self._member_cache:
            messagebox.showwarning("提示", "请先查询会员")
            return

        member = self._member_cache
        category = self.category_var.get()
        if not category:
            messagebox.showwarning("提示", "请选择核销方式")
            return

        # 解析会籍卡编号
        card_id = ""
        card_name = ""
        if category != "无卡进场":
            card_text = self.card_var.get()
            if not card_text:
                messagebox.showwarning("提示", "请选择会籍卡")
                return
            # 从格式 "【次卡】30次卡 (MC202605070001) 剩余28次" 中提取编号
            import re
            m = re.search(r'\((MC\d+)\)', card_text)
            if m:
                card_id = m.group(1)
            # 提取卡名称
            m2 = re.search(r'】(.+?)\s*\(', card_text)
            if m2:
                card_name = m2.group(1).strip()

        # 解析消耗数量/金额
        consume_count = 0
        consume_amount = 0.0
        qty_text = self.qty_var.get().strip()
        if category == "次卡":
            try:
                consume_count = int(qty_text) if qty_text else 0
            except ValueError:
                messagebox.showwarning("提示", "消耗次数必须为数字")
                return
            if consume_count <= 0:
                messagebox.showwarning("提示", "消耗次数必须大于0")
                return
        elif category == "现金卡":
            try:
                consume_amount = float(qty_text) if qty_text else 0
            except ValueError:
                messagebox.showwarning("提示", "扣减金额必须为数字")
                return
            if consume_amount <= 0:
                messagebox.showwarning("提示", "扣减金额必须大于0")
                return

        # 构建摘要
        name = member.get("姓名", "")
        summary_parts = [f"会员: {name}"]
        summary_parts.append(f"核销: {category}")
        if category == "次卡":
            summary_parts.append(f"次数: -{consume_count}")
        elif category == "现金卡":
            summary_parts.append(f"金额: -¥{consume_amount:.2f}")

        if not messagebox.askyesno("确认进场", "\n".join(summary_parts)):
            return

        # 执行进场核销
        course_name = self.course_var.get().strip() or "进场签到"
        coach = self.coach_var.get().strip()

        result = self.biz.do_checkin({
            "member_id": member.get("会员编号", ""),
            "member_name": name,
            "member_phone": member.get("手机号", ""),
            "category": category,
            "card_id": card_id,
            "card_name": card_name,
            "consume_count": consume_count,
            "consume_amount": consume_amount,
            "course_name": course_name,
            "coach": coach,
            "operator": "",
        })

        if result["success"]:
            messagebox.showinfo("进场成功", result.get("message", "操作成功"))
            self._on_reset()
            # 触发各模块刷新（如果有回调函数）
        else:
            messagebox.showerror("进场失败", result.get("error", "未知错误"))

    def _on_reset(self):
        """重置面板"""
        self.search_var.set("")
        self.member_info_var.set("输入会员编号扫码或回车查询")
        self._member_cache = None
        self._cards_cache = []
        self.category_combo["values"] = []
        self.category_var.set("")
        self.card_combo["values"] = []
        self.card_var.set("")
        self.qty_var.set("1")
        self.qty_entry.config(state="normal")
        self.qty_label_caption.config(text="次")
        self.coach_var.set("")
        self.course_var.set("进场签到")
        self.card_detail_var.set("")
        self.deduct_preview_var.set("")
        self.status_label.config(text="", foreground="#999999")
        self.search_entry.focus_set()
