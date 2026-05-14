"""
课程/售课/课时包服务 Mixin
V2.14.1 - 售课到期逻辑：新增有效期自动计算 + 过期检查 + 售课状态列
"""
from datetime import date, datetime, timedelta
from config import SHEETS, HEADERS


class CourseMixin:
    """课程/售课/课时包相关方法"""

    def add_course(self, data):
        """添加课程"""
        name = data.get("课程名称", "").strip()
        if not name:
            return {"success": False, "error": "课程名称不能为空"}
        course_id = self.autonum.course_id()
        row_data = {
            "课程编号": course_id,
            "课程名称": name,
            "运动项目": data.get("运动项目", ""),
            "课程类型": data.get("课程类型", "1对1私教"),
            "单节课时长(分钟)": self._safe_int(data.get("单节课时长(分钟)", 60)),
            "标准课时数": self._safe_int(data.get("标准课时数", 1)),
            "标准售价": self._safe_float(data.get("标准售价", 0)),
            "最低售价": self._safe_float(data.get("最低售价", 0)),
            "课程有效期(天)": self._safe_int(data.get("课程有效期(天)", 180)),
            "最大预约人数": self._safe_int(data.get("最大预约人数", 1)),
            "适用会员等级": data.get("适用会员等级", "全部"),
            "是否支持试课": data.get("是否支持试课", "否"),
            "试课消耗课时": self._safe_int(data.get("试课消耗课时", 0)),
            "课程描述": data.get("课程描述", ""),
            "课程状态": data.get("课程状态", "正常"),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["course"], row_data)
        # 清除缓存，使下次读取时重新加载
        self._course_cache = None
        return {"success": True, "course_id": course_id, 'message': '课程添加成功'}

    def get_all_courses(self):
        """获取所有课程"""
        if self._course_cache is None:
            self._course_cache = self.engine.get_all_data(SHEETS["course"])
        return self._course_cache

    def get_course(self, course_id):
        """根据课程编号获取课程"""
        for c in self.get_all_courses():
            if c.get("课程编号") == course_id:
                return c
        return None

    def get_course_id_names(self):
        """获取课程编号-名称字典"""
        return self.get_id_name_map(self.get_all_courses(), "课程编号", "课程名称")

    def add_sale(self, data):
        """添加售课记录（带到期逻辑 V2.14.1）

        自动计算有效期截止日：
        - data 中指定"课时有效期(天)" → 按此计算
        - 课程信息中有"课程有效期(天)" → 按此计算
        - 均未指定 → 默认 180 天
        """
        member_id = data.get("会员编号", "")
        if not member_id:
            return {"success": False, "error": "请选择会员"}

        course_name = data.get("课程名称", "")
        if not course_name:
            return {"success": False, "error": "请选择课程"}

        qty = self._safe_float(data.get("购买课时", 0) or data.get("购买课时数", 0))
        if qty <= 0:
            return {"success": False, "error": "购买课时必须大于0"}

        price = self._safe_float(data.get("课程价格", 0) or data.get("单价", 0))
        amount = self._safe_float(data.get("实收金额", price * qty))
        sale_date = data.get("售课日期", date.today().strftime("%Y-%m-%d"))

        # === 课时有效期计算（三层兜底） ===
        # ① 优先从 data 中取
        validity_days = self._safe_int(data.get("课时有效期(天)", 0))
        if validity_days <= 0:
            validity_days = self._safe_int(data.get("课时有效期", 0))
        # ② 从课程信息中取
        if validity_days <= 0:
            course_id = data.get("课程编号", "")
            if course_id:
                course = self.get_course(course_id)
                if course:
                    validity_days = self._safe_int(course.get("课程有效期(天)", 0))
        # ③ 兜底默认
        if validity_days <= 0:
            validity_days = 180  # 默认半年

        # 计算有效期截止日
        expiry_date = data.get("有效期截止日", "")
        if not expiry_date and validity_days > 0:
            if isinstance(sale_date, str):
                try:
                    base_date = datetime.strptime(sale_date[:10], "%Y-%m-%d")
                except (ValueError, TypeError):
                    base_date = datetime.now()
            elif isinstance(sale_date, (datetime, date)):
                base_date = sale_date if isinstance(sale_date, datetime) else datetime.combine(sale_date, datetime.min.time())
            else:
                base_date = datetime.now()
            expiry_date = (base_date + timedelta(days=validity_days)).strftime("%Y-%m-%d")
        elif not expiry_date:
            expiry_date = ""

        # 当前时间作为"创建时间"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sale_id = self.autonum.sale_id()
        row_data = {
            "售课编号": sale_id,
            "售课日期": sale_date,
            "会员编号": member_id,
            "会员姓名": data.get("会员姓名", ""),
            "课程编号": data.get("课程编号", ""),
            "课程名称": course_name,
            "购买课时数": qty,
            "赠送课时数": self._safe_float(data.get("赠送课时数", 0)),
            "总课时数": qty + self._safe_float(data.get("赠送课时数", 0)),
            "单价": price,
            "折扣": self._safe_float(data.get("折扣", 1.0)),
            "折后总价": amount,
            "实收金额": amount,
            "付款方式": data.get("付款方式", ""),
            "销售员工": data.get("销售员工", data.get("销售人员", "")),
            "销售员姓名": data.get("销售员姓名", ""),
            "销售提成比例": self._safe_float(data.get("销售提成比例", 0)),
            "销售提成金额": 0,
            "课时有效期(天)": validity_days,
            "有效期截止日": expiry_date,
            "购课来源": data.get("购课来源", ""),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["sale"], row_data)

        # 自动更新会员剩余课时
        self._update_member_lessons(member_id, qty)

        # 自动生成课程包（带有效期）
        self.add_lesson_package({
            "会员编号": member_id,
            "会员姓名": data.get("会员姓名", ""),
            "课程名称": course_name,
            "购买课时": qty,
            "剩余课时": qty,
            "课程包类型": "售课赠送",
            "售课编号": sale_id,
            "套餐日期": sale_date,
            "有效期起": sale_date,
            "有效期止": expiry_date,
            "状态": "有效",
        })

        return {"success": True, "sale_id": sale_id, "message": f"售课记录 {sale_id} 创建成功（有效期至 {expiry_date}）"}

    def update_sale(self, row_num, data):
        """更新售课记录"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["sale"], key)
            if col:
                self.engine.write_cell(SHEETS["sale"], row_num, col, value)
        return {"success": True, 'message': '售课记录修改成功'}

    def delete_sale(self, row_num, sale_id=None):
        """删除售课记录"""
        self.engine.delete_row(SHEETS["sale"], row_num)
        return {"success": True, "message": f"售课记录已删除"}

    def get_all_sales(self):
        """获取所有售课记录"""
        return self.engine.get_all_data(SHEETS["sale"])

    def add_lesson_package(self, data):
        """添加课程包（支持有效期和状态）"""
        package_id = self.autonum.package_id()

        # 有效期起
        valid_from = data.get("有效期起", "")
        if not valid_from:
            valid_from = data.get("套餐日期", date.today().strftime("%Y-%m-%d"))

        # 有效期止
        valid_to = data.get("有效期止", "")
        if not valid_to:
            valid_to = data.get("到期日期", "")

        # 状态
        status = data.get("状态", "正常")
        if status in ("", None):
            status = "正常"

        row_data = {
            "课程包编号": package_id,
            "会员编号": data.get("会员编号", ""),
            "会员姓名": data.get("会员姓名", ""),
            "课程名称": data.get("课程名称", ""),
            "购买课时": self._safe_float(data.get("购买课时", 0)),
            "剩余课时": self._safe_float(data.get("剩余课时", 0)),
            "课程包类型": data.get("课程包类型", "售课赠送"),
            "售课编号": data.get("售课编号", ""),
            "套餐日期": valid_from,
            "有效期起": valid_from,
            "有效期止": valid_to,
            "状态": status,
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["lesson_package"], row_data)
        return {"success": True, "package_id": package_id, 'message': '课程包创建成功'}

    def get_package(self, package_id):
        """获取单个课程包"""
        for p in self.get_all_packages():
            if p.get("课程包编号") == package_id:
                return p
        return None

    def get_package_by_sale(self, sale_id):
        """根据售课编号获取课程包"""
        for p in self.get_all_packages():
            if p.get("售课编号") == sale_id:
                return p
        return None

    def get_all_packages(self):
        """获取所有课程包"""
        return self.engine.get_all_data(SHEETS["lesson_package"])

    def get_all_lesson_packages(self):
        """获取所有课程包（别名）"""
        return self.get_all_packages()

    def update_package_status(self, package_id=None):
        """更新课程包状态（基于有效期止 + 剩余课时）"""
        from datetime import date
        today = date.today()
        if package_id:
            packages = [self.get_package(package_id)]
        else:
            packages = self.get_all_packages()

        updated = []
        for p in packages:
            if not p:
                continue
            if p.get("状态") not in ("正常", "有效", ""):
                continue  # 已过期/已用完的跳过

            # 检查有效期止
            expiry = p.get("有效期止", "") or p.get("到期日期", "")
            remaining = self._safe_float(p.get("剩余课时", 0))
            status_changed = False

            if expiry:
                if isinstance(expiry, str):
                    try:
                        expiry_date = datetime.strptime(expiry[:10], "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        expiry_date = None
                elif isinstance(expiry, datetime):
                    expiry_date = expiry.date()
                elif isinstance(expiry, date):
                    expiry_date = expiry
                else:
                    expiry_date = None

                if expiry_date and expiry_date < today:
                    self.update_lesson_package(p["_row"], {"状态": "已过期"})
                    updated.append({"id": p.get("课程包编号"), "status": "已过期"})
                    status_changed = True

            if not status_changed and remaining <= 0:
                self.update_lesson_package(p["_row"], {"状态": "已用完"})
                updated.append({"id": p.get("课程包编号"), "status": "已用完"})

        return {"success": True, "updated": updated, 'message': '课程包状态已更新'}

    def check_sale_expiry(self):
        """批量检查售课记录，将过期售课和关联课程包一起标记
        
        售课记录的"有效期截止日"作为过期判断依据
        新增"售课状态"列：有效 / 已过期 / 无期限
        """
        today = date.today()
        sales = self.get_all_sales()
        expired_count = 0

        # 确保"售课状态"列存在
        header_list = self.engine.get_headers(SHEETS["sale"])
        status_col_idx = None
        for i, h in enumerate(header_list):
            if h == "售课状态":
                status_col_idx = i + 1
                break

        if status_col_idx is None:
            ws = self.engine.get_sheet(SHEETS["sale"])
            new_col = len(header_list) + 1
            ws.cell(row=3, column=new_col).value = "售课状态"
            self.engine.apply_header_style(SHEETS["sale"], 3, new_col)
            self.engine.save()
            status_col_idx = new_col
            # 重新读取所有数据（因为列结构变了）
            sales = self.get_all_sales()

        for s in sales:
            expiry = s.get("有效期截止日", "")
            sale_id = s.get("售课编号", "")
            if not sale_id:
                continue

            if not expiry:
                # 无截止日 → 标记为"无期限"
                self.engine.write_cell(SHEETS["sale"], s["_row"], status_col_idx, "无期限")
                continue

            # 统一转为 date 比较
            if isinstance(expiry, str):
                try:
                    expiry_date = datetime.strptime(expiry[:10], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    continue
            elif isinstance(expiry, datetime):
                expiry_date = expiry.date()
            elif isinstance(expiry, date):
                expiry_date = expiry
            else:
                continue

            is_expired = expiry_date < today
            new_status = "已过期" if is_expired else "有效"

            # 更新售课记录的状态列
            self.engine.write_cell(SHEETS["sale"], s["_row"], status_col_idx, new_status)

            if is_expired:
                # 找到关联的课程包并设为过期
                packages = self.get_all_packages()
                for p in packages:
                    pkg_sale_id = p.get("售课编号", "")
                    if pkg_sale_id == sale_id and p.get("状态") in ("正常", "有效", ""):
                        self.update_lesson_package(p["_row"], {"状态": "已过期"})
                        expired_count += 1

        # 保存所有更改
        self.engine.save()
        return {"success": True, "expired_count": expired_count, 'message': '售课到期检查完成'}

    def consume_lesson_from_package(self, member_id, consume_qty=1):
        """从会员的课程包中消耗课时"""
        packages = [
            p for p in self.get_all_packages()
            if p.get("会员编号") == member_id
            and p.get("状态") in ("正常", "")
        ]
        if not packages:
            return {"success": False, "error": "该会员没有可用的课程包"}

        remaining_total = sum(self._safe_float(p.get("剩余课时", 0)) for p in packages)
        if remaining_total < consume_qty:
            return {"success": False, "error": f"剩余课时不足（需要{consume_qty}，剩余{remaining_total}）"}

        to_consume = consume_qty
        for p in sorted(packages, key=lambda x: x.get("_row", 0)):
            if to_consume <= 0:
                break
            p_remaining = self._safe_float(p.get("剩余课时", 0))
            if p_remaining <= 0:
                continue
            deduct = min(p_remaining, to_consume)
            new_remaining = p_remaining - deduct
            self.update_lesson_package(p["_row"], {"剩余课时": new_remaining})
            to_consume -= deduct
        return {"success": True, "consumed": consume_qty, 'message': '课时消耗成功'}

    def update_lesson_package(self, row_num, data):
        """更新课程包"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["lesson_package"], key)
            if col:
                self.engine.write_cell(SHEETS["lesson_package"], row_num, col, value)
        return {"success": True, 'message': '课程包已更新'}

    def delete_lesson_package(self, row_num):
        """删除课程包"""
        self.engine.delete_row(SHEETS["lesson_package"], row_num)
        return {"success": True, 'message': '课程包已删除'}

    def _get_course_distribution(self):
        """获取课程类型分布（本月售课中各课程的数量）"""
        sales = self.get_all_sales()
        today = date.today()
        course_counts = {}
        for s in sales:
            sd = self._safe_to_date(s.get("售课日期"))
            if sd and sd.month == today.month and sd.year == today.year:
                cname = s.get("课程名称", "未知")
                qty = self._safe_float(s.get("购买课时", 1))
                course_counts[cname] = course_counts.get(cname, 0) + qty
        result = [{"name": k, "count": int(v)} for k, v in course_counts.items()]
        result.sort(key=lambda x: x["count"], reverse=True)
        return result[:10]

    def _get_course_ranking(self, limit=8):
        """获取课程销量排行"""
        sales = self.get_all_sales()
        today = date.today()
        course_counts = {}
        for s in sales:
            sd = self._safe_to_date(s.get("售课日期"))
            if sd and sd.month == today.month and sd.year == today.year:
                cname = s.get("课程名称", "未知")
                qty = self._safe_float(s.get("购买课时", 1))
                course_counts[cname] = course_counts.get(cname, 0) + qty
        result = [{"name": k, "count": int(v)} for k, v in course_counts.items()]
        result.sort(key=lambda x: x["count"], reverse=True)
        return result[:limit]
