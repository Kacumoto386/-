"""
上课/教练/排班服务 Mixin
"""
from datetime import date
from config import SHEETS, HEADERS


class ClassRecordMixin:
    """上课记录相关方法"""

    def add_class_record(self, data):
        """添加上课记录"""
        sale_id = data.get("售课编号", "")
        member_id = data.get("会员编号", "")
        if not member_id:
            return {"success": False, "error": "请选择会员"}

        class_id = self.autonum.class_record_id()
        row_data = {
            "上课编号": class_id,
            "会员编号": member_id,
            "会员姓名": data.get("会员姓名", ""),
            "课程名称": data.get("课程名称", ""),
            "上课日期": data.get("上课日期", date.today().strftime("%Y-%m-%d")),
            "上课时段": data.get("上课时段", ""),
            "上课教练": data.get("上课教练", data.get("教练", "")),
            "上课地点": data.get("上课地点", ""),
            "上课时长": data.get("上课时长", "60分钟"),
            "课程类型": data.get("课程类型", "1对1私教"),
            "课耗课时": self._safe_float(data.get("课耗课时", 1)),
            "售课编号": sale_id,
            "签到状态": "已签到",
            "备注": data.get("备注", ""),
            "进场签到": data.get("进场签到", "否"),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["class_record"], row_data)

        # 消耗课时
        consume_qty = self._safe_float(data.get("课耗课时", 1))
        self._update_member_lessons(member_id, -consume_qty)
        self.consume_lesson_from_package(member_id, consume_qty)

        return {"success": True, "class_id": class_id, "message": "上课记录添加成功"}

    def update_class_record(self, row_num, data):
        """更新上课记录"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["class_record"], key)
            if col:
                self.engine.write_cell(SHEETS["class_record"], row_num, col, value)
        return {"success": True, "message": "上课记录添加成功"}

    def delete_class_record(self, row_num):
        """删除上课记录"""
        self.engine.delete_row(SHEETS["class_record"], row_num)
        return {"success": True, "message": "上课记录修改成功"}

    def get_all_class_records(self):
        """获取所有上课记录"""
        return self.engine.get_all_data(SHEETS["class_record"])

    def _get_coach_radar_data(self):
        """获取教练综合能力雷达图数据"""
        staff = self.get_all_staff()
        sales = self.get_all_sales()
        classes = self.get_all_class_records()
        today = date.today()

        radar_data = {}
        coaches = [s for s in staff if s.get("职务") in ("教练", "私教", "高级教练")]

        for coach in coaches[:5]:
            name = coach.get("姓名", "")
            if not name:
                continue

            class_count = sum(1 for c in classes
                              if self._safe_to_date(c.get("上课日期"))
                              and self._safe_to_date(c.get("上课日期")).month == today.month
                              and (c.get("教练") == name or c.get("上课教练") == name))

            sale_amount = sum(
                self._safe_float(s.get("实收金额", 0))
                for s in sales
                if self._safe_to_date(s.get("售课日期"))
                and self._safe_to_date(s.get("售课日期")).month == today.month
                and (s.get("销售顾问") == name or s.get("员工") == name)
            )

            student_count = sum(1 for c in classes
                                if c.get("教练") == name or c.get("上课教练") == name)

            total_classes = sum(1 for c in classes
                                if c.get("教练") == name or c.get("上课教练") == name)
            score = min(100, 60 + total_classes * 3) if total_classes > 0 else 0

            max_sale = max((self._safe_float(s.get("实收金额", 0)) for s in sales), default=1)
            max_class = max(
                len([c for c in classes
                     if self._safe_to_date(c.get("上课日期"))
                     and self._safe_to_date(c.get("上课日期")).month == today.month]),
                1
            )

            sale_norm = min(100, sale_amount / max_sale * 100) if max_sale else 0
            class_norm = min(100, class_count / max_class * 100) if max_class else 0
            student_norm = min(100, student_count * 10)

            radar_data[name] = [
                {"label": "课时量", "value": class_norm},
                {"label": "售课业绩", "value": sale_norm},
                {"label": "学员覆盖", "value": student_norm},
                {"label": "综合评分", "value": score},
                {"label": "活跃度", "value": min(100, class_count * 20)},
            ]
        return radar_data
