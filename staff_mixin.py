"""
员工服务 Mixin - 员工/教练模块
"""
from datetime import date
from config import SHEETS, HEADERS


class StaffMixin:
    """员工管理相关方法"""

    def add_staff(self, data):
        """添加员工"""
        name = data.get("姓名", "").strip()
        if not name:
            return {"success": False, "error": "姓名不能为空"}

        phone = data.get("手机号", "").strip()
        if phone and not self.validate_phone_unique("staff", phone):
            return {"success": False, "error": "手机号已存在"}

        staff_id = self.autonum.staff_id()
        row_data = {
            "员工编号": staff_id,
            "姓名": name,
            "性别": data.get("性别", "男"),
            "手机号": phone,
            "职务": data.get("职务", data.get("岗位", "")),
            "身份证号": data.get("身份证号", ""),
            "入职日期": data.get("入职日期", date.today().strftime("%Y-%m-%d")),
            "基本工资": self._safe_float(data.get("基本工资", 0)),
            "提成比例": self._safe_float(data.get("提成比例", 0)),
            "状态": data.get("状态", "在职"),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["staff"], row_data)
        self._staff_cache = None
        return {"success": True, "staff_id": staff_id, 'message': '员工添加成功'}

    def update_staff(self, row_num, data):
        """更新员工信息"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["staff"], key)
            if col:
                self.engine.write_cell(SHEETS["staff"], row_num, col, value)
        self._staff_cache = None
        return {"success": True, 'message': '员工信息已更新'}

    def delete_staff(self, row_num):
        """删除员工"""
        self.engine.delete_row(SHEETS["staff"], row_num)
        self._staff_cache = None
        return {"success": True, 'message': '员工已删除'}

    def get_all_staff(self):
        """获取所有员工"""
        if self._staff_cache is None:
            self._staff_cache = self.engine.get_all_data(SHEETS["staff"])
        return self._staff_cache

    def get_staff(self, staff_id):
        """根据员工编号获取员工信息"""
        for s in self.get_all_staff():
            if s.get("员工编号") == staff_id:
                return s
        return None

    def get_staff_id_names(self):
        """获取员工编号-姓名字典"""
        return self.get_id_name_map(self.get_all_staff(), "员工编号", "姓名")

    def get_staff_with_stats(self):
        """获取员工统计信息"""
        staff_list = self.get_all_staff()
        classes = self.get_all_class_records()
        sales = self.get_all_sales()

        results = []
        for s in staff_list:
            name = s.get("姓名", "")
            class_count = len([c for c in classes if c.get("教练") == name])
            sale_count = len([sl for sl in sales if sl.get("销售顾问") == name])
            sale_amount = sum(self._safe_float(sl.get("实收金额", 0))
                              for sl in sales if sl.get("销售顾问") == name)
            results.append({
                **s,
                "_class_count": class_count,
                "_sale_count": sale_count,
                "_sale_amount": sale_amount,
            })
        return results

    def get_all_trainers(self):
        """获取所有教练（兼容职务/岗位字段）"""
        COACH_ROLES = ("教练", "私教", "高级教练", "健身教练", "瑜伽教练", "游泳教练", "操课教练")
        return [s for s in self.get_all_staff()
                if s.get("职务") in COACH_ROLES or s.get("岗位") in COACH_ROLES]

    def get_coach_schedule(self, coach_name, week_start):
        """获取教练排班"""
        from datetime import timedelta
        week_end = week_start + timedelta(days=6)
        bookings = self.get_weekly_bookings(week_start)
        return [b for b in bookings if b.get("coach") == coach_name]

    def get_weekly_bookings(self, start_date):
        """获取一周预约"""
        from datetime import timedelta
        result = []
        for i in range(7):
            d = start_date + timedelta(days=i)
            result.extend(self.get_bookings_by_date(d))
        return result

    def get_monthly_schedule(self, coach_name, year, month):
        """获取教练某月的排班数据（按天汇总）

        Returns:
            dict: {day: { "count": int, "statuses": [str], "bookings": [dict] }}
        """
        from datetime import date, timedelta
        import calendar
        result = {}
        _, days_in_month = calendar.monthrange(year, month)
        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            bookings = self.get_bookings_by_date(d)
            coach_bookings = [b for b in bookings if b.get("教练姓名") == coach_name]
            if coach_bookings:
                statuses = [b.get("预约状态", "") for b in coach_bookings]
                result[day] = {
                    "count": len(coach_bookings),
                    "statuses": statuses,
                    "bookings": sorted(coach_bookings,
                                       key=lambda x: str(x.get("开始时间", ""))),
                }
            else:
                result[day] = {"count": 0, "statuses": [], "bookings": []}
        return result
