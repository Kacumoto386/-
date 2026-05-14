"""
会籍卡业务逻辑 Mixin - 次卡/期限卡/现金卡 三种卡类型
"""
from datetime import date, datetime, timedelta
from config import SHEETS, MEMBERSHIP_STATUSES


class MembershipMixin:
    """会籍卡管理相关方法"""

    def add_membership(self, data):
        """添加会籍卡（售卡）
        
        Args:
            data: dict，包含会员信息、卡类型、金额等
        Returns:
            dict: {"success": bool, "membership_id": str, "message": str}
        """
        member_id = data.get("会员编号", "")
        card_type = data.get("卡类型", "")
        
        if not member_id:
            return {"success": False, "error": "请选择会员"}
        if card_type not in ("次卡", "期限卡", "现金卡"):
            return {"success": False, "error": "卡类型无效"}
        
        card_id = self.autonum.membership_id()
        today = date.today()
        sale_date = data.get("开卡日期", today)
        if isinstance(sale_date, str):
            try:
                sale_date = datetime.strptime(sale_date, "%Y-%m-%d").date()
            except ValueError:
                sale_date = today
        
        row_data = {
            "会籍卡编号": card_id,
            "会员编号": member_id,
            "会员姓名": data.get("会员姓名", ""),
            "会员手机号": data.get("会员手机号", ""),
            "卡类型": card_type,
            "卡名称": data.get("卡名称", ""),
            "售价": self._safe_float(data.get("售价", 0)),
            "实收金额": self._safe_float(data.get("实收金额", 0)),
            "付款方式": data.get("付款方式", ""),
            "销售员工": data.get("销售员工", ""),
            "开卡日期": sale_date,
            "状态": "有效",
            "操作员": data.get("操作员", ""),
            "备注": data.get("备注", ""),
        }
        
        # 次卡字段
        if card_type == "次卡":
            total = self._safe_int(data.get("总次数", 0))
            row_data["总次数"] = total
            row_data["已消耗次数"] = 0
            row_data["剩余次数"] = total
            valid_from = data.get("有效期起", sale_date)
            valid_to = data.get("有效期止", "")
            row_data["有效期起"] = valid_from
            row_data["有效期止"] = valid_to
            row_data["余额"] = ""
            row_data["已消费金额"] = ""
            row_data["有效天数"] = ""
        
        # 期限卡字段
        elif card_type == "期限卡":
            days = self._safe_int(data.get("有效天数", 30))
            valid_from = data.get("有效期起", sale_date)
            # 确保 valid_from 是 date 对象
            if isinstance(valid_from, str):
                try:
                    from datetime import datetime as _dt
                    valid_from = _dt.strptime(valid_from, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    valid_from = sale_date
            valid_to = data.get("有效期止", valid_from + timedelta(days=days))
            row_data["有效天数"] = days
            row_data["有效期起"] = valid_from
            row_data["有效期止"] = valid_to
            row_data["总次数"] = ""
            row_data["已消耗次数"] = ""
            row_data["剩余次数"] = ""
            row_data["余额"] = ""
            row_data["已消费金额"] = ""
        
        # 现金卡字段
        elif card_type == "现金卡":
            row_data["余额"] = self._safe_float(data.get("余额", 0))
            row_data["已消费金额"] = 0.0
            row_data["总次数"] = ""
            row_data["已消耗次数"] = ""
            row_data["剩余次数"] = ""
            row_data["有效期起"] = ""
            row_data["有效期止"] = ""
            row_data["有效天数"] = ""
        
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["membership"], row_data)
        
        # 售卡联动：更新会员信息
        self._link_membership_to_member(card_type, member_id, row_data)
        
        return {"success": True, "membership_id": card_id, "message": f"会籍卡 {card_id} 售卡成功"}
    
    def _link_membership_to_member(self, card_type, member_id, card_data):
        """售卡后联动更新会员信息"""
        member = self.get_member(member_id)
        if not member:
            return
        
        update_data = {}
        
        if card_type == "次卡":
            # 次卡只在会籍卡表管理，不累加到会员表的课时字段
            pass
        
        elif card_type == "期限卡":
            valid_to = card_data.get("有效期止", "")
            card_name = card_data.get("卡名称", "")
            update_data["会员等级"] = card_name
            update_data["会员状态"] = "有效"
            update_data["到期日期"] = valid_to
        
        elif card_type == "现金卡":
            balance = self._safe_float(card_data.get("余额", 0))
            current_balance = self._safe_float(member.get("剩余金额", 0))
            update_data["剩余金额"] = current_balance + balance
        
        if update_data:
            self.update_member(member["_row"], update_data)
    
    def get_membership(self, card_id):
        """根据会籍卡编号获取会籍卡信息"""
        for c in self.get_all_memberships():
            if c.get("会籍卡编号") == card_id:
                return c
        return None
    
    def get_all_memberships(self):
        """获取所有会籍卡"""
        return self.engine.get_all_data(SHEETS["membership"])
    
    def get_member_memberships(self, member_id):
        """获取某会员的所有会籍卡"""
        return [c for c in self.get_all_memberships()
                if c.get("会员编号") == member_id]
    
    def get_member_valid_memberships(self, member_id):
        """获取某会员的有效会籍卡"""
        return [c for c in self.get_member_memberships(member_id)
                if c.get("状态") == "有效"]
    
    def get_member_membership_summary(self, member_id):
        """获取某会员会籍卡汇总信息
        
        Returns:
            dict: {
                "会籍卡(次卡剩余)": int,    # 所有有效次卡的剩余次数之和
                "会籍卡(现金余额)": float,  # 所有有效现金卡的余额之和
                "会籍卡到期日": str,       # 最近的期限卡到期日
                "会籍卡数量": int,         # 有效会籍卡总数
            }
        """
        cards = self.get_member_valid_memberships(member_id)
        total_remaining = 0
        total_balance = 0.0
        latest_expiry = ""
        
        for c in cards:
            card_type = c.get("卡类型", "")
            if card_type == "次卡":
                remaining = self._safe_int(c.get("剩余次数", 0))
                total_remaining += remaining
            elif card_type == "现金卡":
                balance = self._safe_float(c.get("余额", 0))
                total_balance += balance
            elif card_type == "期限卡":
                expiry = c.get("有效期止", "")
                if expiry:
                    expiry_str = str(expiry)
                    if expiry_str > latest_expiry:
                        latest_expiry = expiry_str
        
        # 格式化日期
        if latest_expiry:
            try:
                d = datetime.strptime(str(latest_expiry)[:10], "%Y-%m-%d") if " " not in str(latest_expiry) else datetime.strptime(str(latest_expiry)[:10], "%Y-%m-%d")
                latest_expiry = d.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                latest_expiry = str(latest_expiry)[:10]
        
        return {
            "会籍卡(次卡剩余)": total_remaining,
            "会籍卡(现金余额)": total_balance,
            "会籍卡到期日": latest_expiry if latest_expiry else "",
            "会籍卡数量": len(cards),
        }
    
    def update_membership(self, row_num, data):
        """更新会籍卡信息"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["membership"], key)
            if col:
                self.engine.write_cell(SHEETS["membership"], row_num, col, value)
        return {"success": True, 'message': '会籍卡已更新'}
    
    def refund_membership(self, row_num, card_id, refund_date=None):
        """退费会籍卡"""
        card = self.get_membership(card_id)
        if not card:
            return {"success": False, "error": "会籍卡不存在"}
        if card.get("状态") == "已退费":
            return {"success": False, "error": "该卡已经退费"}
        
        today = refund_date or date.today()
        
        # 更新卡状态
        self.update_membership(row_num, {
            "状态": "已退费",
            "退费日期": today,
        })
        
        # 回滚对会员的影响
        member = self.get_member(card.get("会员编号", ""))
        if member:
            card_type = card.get("卡类型", "")
            update_data = {}
            
            if card_type == "次卡":
                remaining = self._safe_int(card.get("剩余次数", 0))
                current_remaining = self._safe_float(member.get("剩余课时", 0))
                current_total = self._safe_float(member.get("总购课时", 0))
                total = self._safe_int(card.get("总次数", 0))
                update_data["剩余课时"] = max(0, current_remaining - remaining)
                update_data["总购课时"] = max(0, current_total - total)
            
            elif card_type == "期限卡":
                update_data["会员状态"] = "过期"
            
            elif card_type == "现金卡":
                balance = self._safe_float(card.get("余额", 0))
                current_balance = self._safe_float(member.get("剩余金额", 0))
                update_data["剩余金额"] = max(0, current_balance - balance)
            
            if update_data:
                self.update_member(member["_row"], update_data)
        
        return {"success": True, "message": f"会籍卡 {card_id} 退费成功"}
    
    def consume_membership_lesson(self, member_id, consume_count=1):
        """消耗会员的次卡（上课签到自动扣减）
        
        优先消耗最早开的、有效的次卡
        Returns: 是否成功消耗了某张卡
        """
        cards = self.get_member_valid_memberships(member_id)
        # 只保留次卡，按开卡日期升序
        count_cards = [c for c in cards if c.get("卡类型") == "次卡"]
        count_cards.sort(key=lambda c: str(c.get("开卡日期", "")))
        
        if not count_cards:
            return False
        
        remaining = consume_count
        for card in count_cards:
            if remaining <= 0:
                break
            card_remaining = self._safe_int(card.get("剩余次数", 0))
            if card_remaining <= 0:
                continue
            
            consume = min(remaining, card_remaining)
            new_remaining = card_remaining - consume
            new_consumed = self._safe_int(card.get("已消耗次数", 0)) + consume
            remaining -= consume
            
            self.update_membership(card["_row"], {
                "已消耗次数": new_consumed,
                "剩余次数": new_remaining,
            })
            
            if new_remaining <= 0:
                self.update_membership(card["_row"], {"状态": "已用完"})
        
        return remaining < consume_count
    
    def check_expired_memberships(self):
        """检查并更新已过期的期限卡"""
        today = date.today()
        updated = 0
        for c in self.get_all_memberships():
            if c.get("卡类型") != "期限卡" or c.get("状态") != "有效":
                continue
            valid_to = c.get("有效期止")
            if valid_to and hasattr(valid_to, 'toordinal') and valid_to < today:
                self.update_membership(c["_row"], {"状态": "已过期"})
                # 会员状态联动
                member = self.get_member(c.get("会员编号", ""))
                if member and member.get("会员状态") == "有效":
                    self.update_member(member["_row"], {"会员状态": "过期"})
                updated += 1
        return updated
