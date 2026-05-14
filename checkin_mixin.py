"""
进场核销业务逻辑 Mixin
支持：次卡扣次数、现金卡扣余额、期限卡签到、无卡进场
"""
from datetime import date, datetime
from config import SHEETS, CHECKIN_CATEGORIES


class CheckinMixin:
    """进场核销相关方法"""

    def do_checkin(self, data):
        """执行进场核销
        
        Args:
            data: dict, 包含以下字段
                - member_id: 会员编号
                - member_name: 会员姓名
                - member_phone: 会员手机号
                - category: 核销方式（次卡/现金卡/期限卡/无卡进场）
                - card_id: 会籍卡编号（无卡进场时为空）
                - card_name: 卡名称
                - consume_count: 扣减次数（次卡模式）
                - consume_amount: 扣减金额（现金卡模式）
                - course_name: 服务课程（默认"进场签到"）
                - coach: 上课教练（可选）
                - operator: 操作员工
                
        Returns:
            dict: {"success": bool, "checkin_id": str, "message": str}
        """
        member_id = data.get("member_id", "")
        if not member_id:
            return {"success": False, "error": "请选择会员"}

        category = data.get("category", "")
        if category not in CHECKIN_CATEGORIES:
            return {"success": False, "error": f"核销方式无效: {category}"}

        # 生成进场编号
        checkin_id = self.autonum.checkin_id()
        now = datetime.now()
        today = now.date()
        now_str = now.strftime("%H:%M")
        course_name = data.get("course_name", "进场签到")

        # --- 根据不同核销方式执行扣减 ---
        deduction_ok = True
        deduction_detail = {}

        if category == "次卡":
            consume_count = self._safe_int(data.get("consume_count", 1))
            card_id = data.get("card_id", "")
            if not card_id:
                return {"success": False, "error": "次卡核销必须指定会籍卡"}
            # 消耗次卡
            result = self._consume_lesson_card(member_id, card_id, consume_count)
            if not result["success"]:
                return result
            deduction_detail = result

        elif category == "现金卡":
            consume_amount = self._safe_float(data.get("consume_amount", 0))
            card_id = data.get("card_id", "")
            if not card_id:
                return {"success": False, "error": "现金卡核销必须指定会籍卡"}
            if consume_amount <= 0:
                return {"success": False, "error": "扣减金额必须大于0"}
            # 消耗现金卡余额
            result = self._consume_cash_card(member_id, card_id, consume_amount)
            if not result["success"]:
                return result
            deduction_detail = result

        elif category == "期限卡":
            card_id = data.get("card_id", "")
            if card_id:
                deduction_detail = {"card_id": card_id, "message": "期限卡签到，不扣减"}
            else:
                deduction_detail = {"message": "期限卡签到，不扣减"}

        elif category == "无卡进场":
            deduction_detail = {"message": "无卡进场，不扣减"}
            card_id = ""

        # --- 写入进场记录 ---
        row_data = {
            "进场编号": checkin_id,
            "会员编号": member_id,
            "会员姓名": data.get("member_name", ""),
            "会员手机号": data.get("member_phone", ""),
            "核销方式": category,
            "会籍卡编号": data.get("card_id", ""),
            "卡名称": data.get("card_name", ""),
            "扣减次数": self._safe_int(deduction_detail.get("consume_count", 0)),
            "扣减金额": self._safe_float(deduction_detail.get("consume_amount", 0)),
            "服务课程": course_name,
            "上课教练": data.get("coach", ""),
            "操作员工": data.get("operator", ""),
            "进场时间": now_str,
            "进场日期": today,
            "所属门店": data.get("门店编号", ""),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["checkin"], row_data)

        # --- 自动创建上课记录（签到模式）---
        consume_hours = 0
        if category == "次卡":
            consume_hours = self._safe_float(deduction_detail.get("consume_count", 1))
        elif category == "现金卡":
            consume_hours = 0
        elif category in ("期限卡", "无卡进场"):
            consume_hours = 0

        class_data = {
            "会员编号": member_id,
            "会员姓名": data.get("member_name", ""),
            "课程名称": course_name,
            "上课日期": today,
            "上课时段": now_str,
            "上课地点": "前台签到",
            "上课时长": "签到",
            "课程类型": "进场签到",
            "课耗课时": consume_hours,
            "签到状态": "已签到",
            "备注": f"进场签到来核销: {category}",
            "进场签到": "是",
        }
        if data.get("coach"):
            class_data["上课教练"] = data["coach"]
            class_data["教练"] = data["coach"]
        self.add_class_record(class_data)

        return {
            "success": True,
            "checkin_id": checkin_id,
            "message": f"进场核销完成: {checkin_id} ({category})",
        }

    def _consume_lesson_card(self, member_id, card_id, consume_count):
        """消耗次卡
        
        从指定会籍卡中扣减指定次数
        """
        card = self.get_membership(card_id)
        if not card:
            return {"success": False, "error": f"会籍卡不存在: {card_id}"}

        if card.get("状态") != "有效":
            return {"success": False, "error": f"会籍卡状态异常: {card.get('状态')}"}

        if card.get("卡类型") != "次卡":
            return {"success": False, "error": f"该卡不是次卡: {card.get('卡类型')}"}

        card_remaining = self._safe_int(card.get("剩余次数", 0))
        if card_remaining < consume_count:
            return {
                "success": False,
                "error": f"次卡剩余次数不足: 剩余{card_remaining}, 需{consume_count}",
            }

        new_remaining = card_remaining - consume_count
        new_consumed = self._safe_int(card.get("已消耗次数", 0)) + consume_count

        self.update_membership(card["_row"], {
            "已消耗次数": new_consumed,
            "剩余次数": new_remaining,
        })

        if new_remaining <= 0:
            self.update_membership(card["_row"], {"状态": "已用完"})

        # 同步更新会员剩余课时
        member = self.get_member(member_id)
        if member:
            current_remaining = self._safe_float(member.get("剩余课时", 0))
            self.update_member(member["_row"], {
                "剩余课时": max(0, current_remaining - consume_count),
            })

        return {
            "success": True,
            "consume_count": consume_count,
            "card_id": card_id,
            "message": f"次卡 {card_id} 消耗 {consume_count} 次",
        }

    def _consume_cash_card(self, member_id, card_id, consume_amount):
        """消耗现金卡余额
        
        从指定现金卡扣减余额，同步更新会员剩余金额（储值金额）
        """
        card = self.get_membership(card_id)
        if not card:
            return {"success": False, "error": f"会籍卡不存在: {card_id}"}

        if card.get("状态") != "有效":
            return {"success": False, "error": f"会籍卡状态异常: {card.get('状态')}"}

        if card.get("卡类型") != "现金卡":
            return {"success": False, "error": f"该卡不是现金卡: {card.get('卡类型')}"}

        card_balance = self._safe_float(card.get("余额", 0))
        if card_balance < consume_amount:
            return {
                "success": False,
                "error": f"现金卡余额不足: 余额¥{card_balance:.2f}, 需¥{consume_amount:.2f}",
            }

        new_balance = card_balance - consume_amount
        new_consumed = self._safe_float(card.get("已消费金额", 0)) + consume_amount

        self.update_membership(card["_row"], {
            "余额": new_balance,
            "已消费金额": new_consumed,
        })

        if new_balance <= 0:
            self.update_membership(card["_row"], {"状态": "已用完"})

        # 同步更新会员剩余金额（会员储值字段）
        member = self.get_member(member_id)
        if member:
            current_balance = self._safe_float(member.get("剩余金额", 0))
            self.update_member(member["_row"], {
                "剩余金额": max(0, current_balance - consume_amount),
            })

        return {
            "success": True,
            "consume_amount": consume_amount,
            "card_id": card_id,
            "message": f"现金卡 {card_id} 扣减 ¥{consume_amount:.2f}",
        }

    def get_all_checkins(self):
        """获取所有进场记录"""
        return self.engine.get_all_data(SHEETS["checkin"])

    def get_member_checkins(self, member_id):
        """获取某会员的进场记录"""
        return [c for c in self.get_all_checkins()
                if c.get("会员编号") == member_id]

    def get_today_checkins(self):
        """获取今日进场记录"""
        today = date.today()
        return [c for c in self.get_all_checkins()
                if c.get("进场日期") == today]

    def get_today_checkin_count(self):
        """获取今日进场人数"""
        return len(self.get_today_checkins())

    def get_today_checkin_summary(self):
        """获取今日进场摘要（用于看板底部动态）"""
        records = self.get_today_checkins()
        summary = []
        for r in records:
            category = r.get("核销方式", "")
            name = r.get("会员姓名", "")
            time = r.get("进场时间", "")
            if category == "次卡":
                detail = f"次卡×{r.get('扣减次数', 1)}"
            elif category == "现金卡":
                detail = f"现金卡¥{r.get('扣减金额', 0):.0f}"
            elif category == "期限卡":
                detail = "期限卡签到"
            else:
                detail = "无卡进场"
            summary.append(f"{name}  {detail}  {time}")
        return summary
