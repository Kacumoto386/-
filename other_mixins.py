"""
充值/体测/看板/工具 Mixin
"""
from datetime import date, datetime
from config import SHEETS, HEADERS


class RechargeMixin:
    """充值管理相关方法"""

    def add_recharge(self, data):
        """添加充值记录"""
        member_id = data.get("会员编号", "")
        if not member_id:
            return {"success": False, "error": "请选择会员"}
        amount = self._safe_float(data.get("充值金额", 0))
        if amount <= 0:
            return {"success": False, "error": "充值金额必须大于0"}

        recharge_id = self.autonum.recharge_id()
        row_data = {
            "充值编号": recharge_id,
            "会员编号": member_id,
            "会员姓名": data.get("会员姓名", ""),
            "充值金额": amount,
            "充值方式": data.get("充值方式", ""),
            "充值日期": data.get("充值日期", date.today().strftime("%Y-%m-%d")),
            "赠送金额": self._safe_float(data.get("赠送金额", 0)),
            "充值课时": self._safe_float(data.get("充值课时", 0)),
            "操作人员": data.get("操作人员", ""),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["recharge"], row_data)
        return {"success": True, "recharge_id": recharge_id, 'message': '充值成功'}

    def update_recharge(self, row_num, data):
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["recharge"], key)
            if col:
                self.engine.write_cell(SHEETS["recharge"], row_num, col, value)
        return {"success": True, 'message': '充值记录已更新'}

    def delete_recharge(self, row_num):
        self.engine.delete_row(SHEETS["recharge"], row_num)
        return {"success": True, 'message': '充值记录已删除'}

    def get_all_recharges(self):
        return self.engine.get_all_data(SHEETS["recharge"])


class MeasurementMixin:
    """体测记录相关方法"""

    def add_body_measurement(self, data):
        member_id = data.get("会员编号", "")
        if not member_id:
            return {"success": False, "error": "请选择会员"}

        # 自动计算BMI
        height = self._safe_float(data.get("身高(cm)", 0))
        weight = self._safe_float(data.get("体重(kg)", 0))
        if height > 0 and weight > 0:
            bmi = round(weight / ((height / 100) ** 2), 1)
        else:
            bmi = data.get("BMI", 0)

        row_data = {
            "体测编号": self.autonum.body_measurement_id(),
            "会员编号": member_id,
            "会员姓名": data.get("会员姓名", ""),
            "体测日期": data.get("体测日期", date.today().strftime("%Y-%m-%d")),
            "身高(cm)": self._safe_float(data.get("身高(cm)", 0)),
            "体重(kg)": self._safe_float(data.get("体重(kg)", 0)),
            "体脂率(%)": self._safe_float(data.get("体脂率(%)", 0)),
            "BMI": self._safe_float(bmi),
            "肌肉量(kg)": self._safe_float(data.get("肌肉量(kg)", 0)),
            "基础代谢(kcal)": self._safe_float(data.get("基础代谢(kcal)", 0)),
            "体年龄": data.get("体年龄", ""),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        measurement_id = row_data["体测编号"]
        self.engine.append_row(SHEETS["body_measurement"], row_data)
        return {"success": True, "message": f"体测记录 {measurement_id} 保存成功", "measurement_id": measurement_id}

    def update_body_measurement(self, row_num, data):
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["body_measurement"], key)
            if col:
                self.engine.write_cell(SHEETS["body_measurement"], row_num, col, value)
        return {"success": True, "message": "体测记录更新成功"}

    def delete_body_measurement(self, row_num):
        self.engine.delete_row(SHEETS["body_measurement"], row_num)
        return {"success": True, 'message': '体测记录已删除'}

    def get_all_measurements(self):
        return self.engine.get_all_data(SHEETS["body_measurement"])

    def get_member_measurements(self, member_id):
        return [m for m in self.get_all_measurements() if m.get("会员编号") == member_id]


class DashboardMixin:
    """看板/统计相关方法"""

    def get_dashboard_stats(self):
        """获取首页看板统计数据"""
        members = self.get_all_members()
        sales = self.get_all_sales()
        classes = self.get_all_class_records()
        recharges = self.get_all_recharges()
        product_sales = self.get_all_product_sales()

        today = date.today()
        current_month = today.month
        current_year = today.year

        active_members = [m for m in members if m.get("会员状态") == "有效"]
        new_this_month = []
        for m in members:
            jd = self._safe_to_date(m.get("加入日期"))
            if jd and jd.month == current_month and jd.year == current_year:
                new_this_month.append(m)

        total_remaining = sum(self._safe_float(m.get("剩余课时", 0)) for m in members)
        class_this_month = [c for c in classes
                            if self._safe_to_date(c.get("上课日期"))
                            and self._safe_to_date(c.get("上课日期")).month == current_month]
        sale_this_month = [s for s in sales
                           if self._safe_to_date(s.get("售课日期"))
                           and self._safe_to_date(s.get("售课日期")).month == current_month]
        total_sale_amount = sum(self._safe_float(s.get("实收金额", 0)) for s in sale_this_month)

        recharge_this_month = sum(
            self._safe_float(r.get("充值金额", 0))
            for r in recharges
            if self._safe_to_date(r.get("充值日期"))
            and self._safe_to_date(r.get("充值日期")).month == current_month
        )

        product_sale_this_month = sum(
            self._safe_float(p.get("总价", 0))
            for p in product_sales
            if self._safe_to_date(p.get("零售日期"))
            and self._safe_to_date(p.get("零售日期")).month == current_month
        )

        expire_soon = [
            m for m in members
            if m.get("会员有效期")
            and hasattr(m["会员有效期"], "toordinal")
            and 0 <= (m["会员有效期"] - today).days <= 30
        ]

        # 进场统计
        today_checkins = self.get_today_checkin_summary()
        today_checkin_count = self.get_today_checkin_count()

        daily_trend = []
        for i in range(6, -1, -1):
            d = today - __import__('datetime').timedelta(days=i)
            day_sales = [s for s in sales if self._safe_to_date(s.get("售课日期")) == d]
            daily_trend.append({
                "date": d.strftime("%Y-%m-%d"),
                "sale": sum(self._safe_float(s.get("实收金额", 0)) for s in day_sales),
                "count": len(day_sales),
            })

        return {
            "active_members": len(active_members),
            "new_members": len(new_this_month),
            "total_remaining": total_remaining,
            "class_count": len(class_this_month),
            "sale_amount": total_sale_amount,
            "recharge_amount": recharge_this_month,
            "product_sale_amount": product_sale_this_month,
            "expire_soon": len(expire_soon),
            "daily_trend": daily_trend,
            "trainer_ranking": self.get_trainer_ranking(),
            "monthly_trend": self._get_monthly_trend(),
            "course_distribution": self._get_course_distribution(),
            "course_ranking": self._get_course_ranking(),
            "coach_radar_data": self._get_coach_radar_data(),
            "today_checkin_count": today_checkin_count,
            "today_checkin_list": today_checkins,
        }

    def _get_monthly_trend(self, months=6):
        """获取月度营收趋势"""
        sales = self.get_all_sales()
        today = date.today()
        trend = []
        for i in range(months - 1, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_sales = [s for s in sales
                           if self._safe_to_date(s.get("售课日期"))
                           and self._safe_to_date(s.get("售课日期")).month == m
                           and self._safe_to_date(s.get("售课日期")).year == y]
            total = sum(self._safe_float(s.get("实收金额", 0)) for s in month_sales)
            trend.append({"month": f"{y}-{m:02d}", "amount": total, "count": len(month_sales)})
        return trend

    def get_trainer_ranking(self, limit=8):
        """获取教练业绩排行"""
        staff = self.get_all_staff()
        classes = self.get_all_class_records()
        sales = self.get_all_sales()
        today = date.today()
        ranking = []
        for s in staff:
            name = s.get("姓名", "")
            if not name:
                continue
            class_count = sum(1 for c in classes
                              if self._safe_to_date(c.get("上课日期"))
                              and self._safe_to_date(c.get("上课日期")).month == today.month
                              and (c.get("教练") == name or c.get("上课教练") == name))
            sale_amount = sum(
                self._safe_float(sl.get("实收金额", 0)) for sl in sales
                if self._safe_to_date(sl.get("售课日期"))
                and self._safe_to_date(sl.get("售课日期")).month == today.month
                and (sl.get("销售顾问") == name or sl.get("员工") == name)
            )
            ranking.append({"name": name, "sale_amount": sale_amount, "class_count": class_count})
        ranking.sort(key=lambda x: x["sale_amount"], reverse=True)
        return ranking[:limit]


class UtilsMixin:
    """工具方法"""

    def _sale_matches(self, sale, year, month):
        """判断售课记录是否在指定年月"""
        sd = self._safe_to_date(sale.get("售课日期"))
        return sd and sd.month == month and sd.year == year

    def generate_alerts(self):
        """生成到期提醒"""
        from datetime import date, timedelta
        today = date.today()
        alerts = []
        for m in self.get_all_members():
            expiry = m.get("会员有效期")
            if not expiry or not hasattr(expiry, 'toordinal'):
                continue
            days_left = (expiry - today).days
            if 0 <= days_left <= 7:
                alerts.append({"会员姓名": m.get("姓名", ""), "提醒类型": "会员到期",
                               "提醒日期": str(today), "内容": f"会员 {m.get('姓名')} 将于 {days_left} 天后到期",
                               "是否处理": "未处理"})
        return alerts

    def get_all_alerts(self):
        return self.engine.get_all_data(SHEETS["alert"])

    def get_id_name_map(self, data_list, id_key, name_key):
        """将数据列表转为 id->name 字典"""
        return {item.get(id_key, ""): item.get(name_key, "") for item in data_list if item.get(id_key)}

    def get_sheet_column_names(self, sheet_key):
        """获取指定Sheet的列名"""
        name = SHEETS.get(sheet_key)
        if not name:
            return []
        return self.engine.get_headers(name)

    def export_to_csv(self, data, output_path, encoding="utf-8-sig"):
        """导出数据到CSV"""
        import csv
        if not data:
            with open(output_path, 'w', encoding=encoding, newline='') as f:
                f.write("")
            return True
        headers = list(data[0].keys())
        with open(output_path, 'w', encoding=encoding, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in data:
                writer.writerow([str(row.get(h, "")) for h in headers])
        return True

    def validate_phone_unique(self, phone, sheet_type):
        """验证手机号唯一性"""
        if not phone:
            return True
        if sheet_type == "member":
            data_list = self.get_all_members()
        elif sheet_type == "staff":
            data_list = self.get_all_staff()
        else:
            return True
        return not any(d.get("手机号") == phone for d in data_list)

    # ========== 自定义系统名称 ==========

    def get_custom_name(self):
        """获取自定义系统名称，没有设置则返回 PROJECT_NAME"""
        from config import PROJECT_NAME, CUSTOM_NAME_SHEET, CUSTOM_NAME_CELL
        try:
            ws = self.engine.wb[CUSTOM_NAME_SHEET]
            val = ws[CUSTOM_NAME_CELL].value
            if val and str(val).strip():
                return str(val).strip()
        except Exception:
            pass
        return PROJECT_NAME

    def set_custom_name(self, name):
        """设置自定义系统名称"""
        from config import CUSTOM_NAME_SHEET, CUSTOM_NAME_CELL
        name = name.strip() if name else ""
        ws = self.engine.wb[CUSTOM_NAME_SHEET]
        ws[CUSTOM_NAME_CELL] = name
        self.engine.save()
        return {"success": True, "message": f"系统名称已更新为「{name}」"}
