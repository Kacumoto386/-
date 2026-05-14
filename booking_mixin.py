"""
预约服务 Mixin
V2.13.0 - 重构：预约时段改为每10分钟粒度 + 开始/结束时间双字段
"""
from datetime import date, timedelta, datetime
from config import SHEETS, HEADERS


class BookingMixin:
    """预约管理相关方法"""

    def add_booking(self, data):
        """添加预约"""
        member_id = data.get("会员编号", "")
        if not member_id:
            return {"success": False, "error": "请选择会员"}

        coach = data.get("教练姓名", "") or data.get("教练", "")
        if not coach:
            return {"success": False, "error": "请选择教练"}

        booking_date = data.get("预约日期", "")
        start_time = data.get("开始时间", "")
        if not booking_date or not start_time:
            return {"success": False, "error": "请选择预约日期和时段"}

        # 兼容旧版：如果传入的是"预约时段"而不是"开始时间"
        time_slot = data.get("预约时段", start_time)

        conflict = self.check_booking_conflict(coach, booking_date, time_slot, member_id)
        if conflict:
            return {"success": False, "error": conflict}

        booking_id = self.autonum.booking_id()

        # 计算结束时间（默认开始时间+50分钟，约1节课时长）
        end_time = data.get("结束时间", "")
        if not end_time and start_time:
            try:
                parts = start_time.split(":")
                h, m = int(parts[0]), int(parts[1])
                end_h = h + (m + 50) // 60
                end_m = (m + 50) % 60
                if end_h < 24:
                    end_time = f"{end_h:02d}:{end_m:02d}"
                else:
                    end_time = "21:50"
            except (ValueError, IndexError):
                end_time = ""

        course = self.get_course(data.get("课程编号", "")) if hasattr(self, 'get_course') else None
        max_people = 0
        if course:
            max_people = int(float(str(course.get("最大预约人数", 0) or 0)))

        row_data = {
            "预约编号": booking_id,
            "预约日期": booking_date,
            "开始时间": time_slot,
            "结束时间": end_time,
            "会员编号": member_id,
            "会员姓名": data.get("会员姓名", ""),
            "会员手机号": data.get("会员手机号", ""),
            "课程编号": data.get("课程编号", ""),
            "课程名称": data.get("课程名称", ""),
            "教练编号": data.get("教练编号", ""),
            "教练姓名": coach,
            "上课地点": data.get("上课地点", ""),
            "预约状态": "已预约",
            "签到人数": 0,
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["booking"], row_data)
        return {"success": True, "booking_id": booking_id, "message": "预约成功"}

    def check_booking_conflict(self, coach, booking_date, time_slot, member_id=""):
        """检查预约冲突

        按分钟级时段检查：如果预约的时段与已有预约的时段在30分钟内重叠，视为冲突
        """
        bookings = self.get_all_bookings()

        def parse_minutes(t_str):
            """将 HH:MM 转为当天分钟数"""
            try:
                parts = str(t_str).strip().split(":")
                return int(parts[0]) * 60 + int(parts[1])
            except (ValueError, IndexError):
                return 0

        target_start = parse_minutes(time_slot)
        target_end = target_start + 50  # 默认每次预约50分钟

        for b in bookings:
            if b.get("预约状态") not in ("已预约", "已签到"):
                continue
            same_date = str(b.get("预约日期", ""))[:10] == str(booking_date)[:10]
            if not same_date:
                continue

            # 获取已有预约的开始时间
            existing_slot = b.get("开始时间", "") or b.get("预约时段", "")
            existing_start = parse_minutes(existing_slot)

            # 检查是否在目标时段的重叠窗口内（25分钟内视为冲突）
            is_overlap = abs(existing_start - target_start) < 30

            if not is_overlap:
                continue

            if b.get("教练姓名") == coach or b.get("教练") == coach:
                return f"教练 {coach} 在该时段已有预约"
            if member_id and b.get("会员编号") == member_id:
                return "该会员在该时段已有预约"
        return None

    def sign_in_booking(self, row_num):
        """预约签到（签到 → 自动创建上课记录）"""
        bookings = self.engine.get_all_data(SHEETS["booking"])
        booking = next((b for b in bookings if b.get("_row") == row_num), None)
        if not booking:
            return {"success": False, "error": "预约记录不存在"}

        if booking.get("预约状态") != "已预约":
            return {"success": False, "error": f"当前状态为'{booking.get('预约状态')}'，无法签到"}

        # 更新预约状态
        status_col = self.engine.get_header_col(SHEETS["booking"], "预约状态")
        self.engine.write_cell(SHEETS["booking"], row_num, status_col, "已签到")

        # 签到人数+1
        sign_col = self.engine.get_header_col(SHEETS["booking"], "签到人数")
        current_sign = int(float(str(booking.get("签到人数", 0) or 0)))
        self.engine.write_cell(SHEETS["booking"], row_num, sign_col, current_sign + 1)

        # 自动创建上课记录
        member_id = booking.get("会员编号", "")
        class_data = {
            "会员编号": member_id,
            "会员姓名": booking.get("会员姓名", ""),
            "课程编号": booking.get("课程编号", ""),
            "课程名称": booking.get("课程名称", ""),
            "上课日期": str(booking.get("预约日期", date.today().strftime("%Y-%m-%d")))[:10],
            "开始时间": booking.get("开始时间", ""),
            "上课教练": booking.get("教练姓名", ""),
            "课耗课时": 1,
            "签到状态": "已签到",
            "备注": f"预约签到（{booking.get('预约编号', '')}）",
        }
        self.add_class_record(class_data)

        return {"success": True, "message": "签到成功，已自动创建上课记录"}

    def cancel_booking(self, row_num):
        """取消预约"""
        status_col = self.engine.get_header_col(SHEETS["booking"], "预约状态")
        self.engine.write_cell(SHEETS["booking"], row_num, status_col, "已取消")
        return {"success": True, "message": "已取消"}

    def complete_booking(self, row_num):
        """完成预约"""
        status_col = self.engine.get_header_col(SHEETS["booking"], "预约状态")
        self.engine.write_cell(SHEETS["booking"], row_num, status_col, "已完成")
        return {"success": True, "message": "已完成"}

    def get_bookings_by_date(self, target_date):
        """获取指定日期的预约"""
        return [b for b in self.get_all_bookings()
                if str(b.get("预约日期", ""))[:10] == str(target_date)[:10]]

    def get_all_bookings(self):
        """获取所有预约"""
        return self.engine.get_all_data(SHEETS["booking"])

    def get_group_bookings_by_date(self, target_date, course_id=None):
        """获取指定日期的团课预约"""
        result = [b for b in self.get_bookings_by_date(target_date)
                  if b.get("课程名称", "").startswith("团") or "团课" in b.get("课程名称", "")]
        if course_id:
            result = [b for b in result if b.get("课程编号") == course_id]
        return result

    def batch_sign_in(self, booking_ids):
        """批量签到"""
        success = 0
        errors = []
        for bid in booking_ids:
            r = self.sign_in_booking(bid)
            if r.get("success"):
                success += 1
            else:
                errors.append(r.get("error", ""))
        return {"success": True, "success_count": success, "errors": errors, 'message': '批量签到完成'}
