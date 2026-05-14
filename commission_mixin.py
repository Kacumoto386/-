"""
梯度提成计算引擎 - CommissionMixin
V1.0 - 支持自定义梯度规则、分段累进计算
"""
from datetime import datetime
from config import SHEETS, COMMISSION_TIER_TYPES, COMMISSION_TIER_HEADERS, COMMISSION_TIER_STATUSES


class CommissionMixin:
    """梯度提成计算引擎"""

    # ========== 梯度配置 CRUD ==========

    def get_all_tier_rules(self):
        """获取所有梯度规则"""
        return self.engine.get_all_data(SHEETS["commission_tier"])

    def get_tier_rules(self, tier_type="售课提成", only_enabled=True):
        """按类型获取梯度规则，按排序号升序
        
        Args:
            tier_type: "售课提成" 或 "上课提成"
            only_enabled: 是否只返回启用状态的
        Returns:
            排序后的规则列表
        """
        rules = self.get_all_tier_rules()
        filtered = [r for r in rules if r.get("类型") == tier_type]
        if only_enabled:
            filtered = [r for r in filtered if r.get("状态") in ("启用", "")]
        
        # 按排序号升序
        filtered.sort(key=lambda r: self._safe_int(r.get("排序号", 99)))
        return filtered

    def add_tier_rule(self, data):
        """新增一条梯度规则"""
        name = data.get("梯度名称", "").strip()
        if not name:
            return {"success": False, "error": "梯度名称不能为空"}
        
        tier_type = data.get("类型", "")
        if tier_type not in COMMISSION_TIER_TYPES:
            return {"success": False, "error": f"无效的类型: {tier_type}"}
        
        lower = self._safe_float(data.get("下限", 0))
        upper = data.get("上限", "")
        rate = self._safe_float(data.get("提成率", 0))
        sort_order = self._safe_int(data.get("排序号", 99))
        
        tier_id = self.autonum.tier_id()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row_data = {
            "梯度编号": tier_id,
            "梯度名称": name,
            "类型": tier_type,
            "下限": lower,
            "上限": upper if upper else "",
            "提成率": rate,
            "排序号": sort_order,
            "状态": data.get("状态", "启用"),
            "创建时间": now_str,
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["commission_tier"], row_data)
        return {"success": True, "tier_id": tier_id, "message": f"梯度规则 {name} 添加成功"}

    def update_tier_rule(self, row_num, data):
        """更新一条梯度规则"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["commission_tier"], key)
            if col:
                self.engine.write_cell(SHEETS["commission_tier"], row_num, col, value)
        return {"success": True, "message": "梯度规则已更新"}

    def delete_tier_rule(self, row_num):
        """删除一条梯度规则"""
        self.engine.delete_row(SHEETS["commission_tier"], row_num)
        return {"success": True, "message": "梯度规则已删除"}

    # ========== 梯度计算 ==========

    def match_tier_rate(self, tier_type, value):
        """根据值匹配梯度，返回对应的提成率
        
        全额匹配模式：找到第一个满足 [下限 ≤ 值 < 上限] 的梯度，返回提成率
        上限为空表示无上限
        
        Returns:
            匹配到的 (梯度名称, 提成率, 梯度下限, 梯度上限)
            未匹配到返回 ("未匹配", 0, None, None)
        """
        rules = self.get_tier_rules(tier_type)
        value = self._safe_float(value)
        
        for r in rules:
            lower = self._safe_float(r.get("下限", 0))
            upper_raw = r.get("上限", "")
            rate = self._safe_float(r.get("提成率", 0))
            
            if lower <= value:
                if upper_raw == "" or upper_raw is None:
                    return (r.get("梯度名称", ""), rate, lower, None)
                upper = self._safe_float(upper_raw)
                if value < upper:
                    return (r.get("梯度名称", ""), rate, lower, upper)
        
        # 兜底：使用最后的梯度
        if rules:
            last = rules[-1]
            return (last.get("梯度名称", ""), self._safe_float(last.get("提成率", 0)),
                    self._safe_float(last.get("下限", 0)), last.get("上限"))
        return ("未匹配", 0, None, None)

    def calculate_tier_commission(self, tier_type, value):
        """分段累进计算梯度提成
        
        将值按梯度段分段，每段分别计算，然后求和
        
        Args:
            tier_type: "售课提成" 或 "上课提成"
            value: 销售额或上课节数
        
        Returns:
            dict {
                "total_commission": 总提成金额,
                "segments": [{"name": 段名, "range": 区间, "rate": 率, "base": 基数, "commission": 提成}, ...],
                "rate": 综合提成率,
                "tier_name": 命中最高梯度名,
            }
        """
        rules = self.get_tier_rules(tier_type)
        value = self._safe_float(value)
        
        if not rules:
            return {
                "total_commission": 0,
                "segments": [],
                "rate": 0,
                "tier_name": "无规则",
            }
        
        segments = []
        total_commission = 0.0
        remaining = value
        last_upper = 0
        
        for r in rules:
            lower = self._safe_float(r.get("下限", 0))
            upper_raw = r.get("上限", "")
            rate = self._safe_float(r.get("提成率", 0))
            
            # 跳过超出范围的段
            if value <= lower:
                break
            
            if upper_raw == "" or upper_raw is None:
                # 最后一档：剩余全部
                base = remaining
            else:
                upper = self._safe_float(upper_raw)
                if value <= lower:
                    break
                if remaining <= 0:
                    break
                band_width = upper - lower
                base = min(band_width, remaining)
            
            commission = base * rate
            total_commission += commission
            
            if upper_raw == "" or upper_raw is None:
                range_str = f"{lower:,.0f}+"
            else:
                range_str = f"{lower:,.0f}~{self._safe_float(upper_raw):,.0f}"
            
            segments.append({
                "name": r.get("梯度名称", f"第{len(segments)+1}段"),
                "range": range_str,
                "rate": rate,
                "base": base,
                "commission": commission,
            })
            
            remaining -= base
            last_upper = self._safe_float(upper_raw) if upper_raw else None
        
        overall_rate = total_commission / value if value > 0 else 0
        tier_name = segments[-1]["name"] if segments else "无规则"
        
        return {
            "total_commission": round(total_commission, 2),
            "segments": segments,
            "rate": round(overall_rate, 4),
            "tier_name": tier_name,
        }

    # ========== 批量计算（给报表用） ==========

    def calc_sale_commission_by_tier(self, staff_name, sale_amount):
        """计算某个员工的售课梯度提成"""
        # 先看员工有无单独设置比例
        staff = self._find_staff(staff_name)
        if staff:
            fixed_rate = self._safe_float(staff.get("售课提成比例"))
            if fixed_rate > 0:
                # 有固定比例 → 用固定比例（兼容旧逻辑）
                return {
                    "total_commission": sale_amount * fixed_rate,
                    "segments": [{"name": "固定比例", "range": "", "rate": fixed_rate,
                                  "base": sale_amount, "commission": sale_amount * fixed_rate}],
                    "rate": fixed_rate,
                    "tier_name": f"{fixed_rate*100:.0f}%固定",
                }
        
        # 无固定比例 → 用梯度规则
        return self.calculate_tier_commission("售课提成", sale_amount)

    def calc_class_commission_by_tier(self, staff_name, class_count, unit_price=100):
        """计算某个员工的上课梯度提成
        
        Args:
            staff_name: 员工姓名
            class_count: 上课节数
            unit_price: 每节课单价（按100元/节估算）
        """
        staff = self._find_staff(staff_name)
        if staff:
            fixed_rate = self._safe_float(staff.get("上课提成比例"))
            if fixed_rate > 0:
                amount = class_count * unit_price
                return {
                    "total_commission": amount * fixed_rate,
                    "segments": [{"name": "固定比例", "range": "", "rate": fixed_rate,
                                  "base": amount, "commission": amount * fixed_rate}],
                    "rate": fixed_rate,
                    "tier_name": f"{fixed_rate*100:.0f}%固定",
                }
        
        # 上课提成是按节数匹配梯度 → 每节再乘以单价
        tier_result = self.calculate_tier_commission("上课提成", class_count)
        # 结果按每节100元折算
        tier_result["total_commission"] = round(tier_result["total_commission"] * unit_price, 2)
        for seg in tier_result["segments"]:
            seg["commission"] = round(seg["commission"] * unit_price, 2)
            seg["base"] = int(seg["base"])
        return tier_result

    def _find_staff(self, staff_name):
        """根据姓名查找员工"""
        for s in self.get_all_staff():
            if s.get("姓名") == staff_name:
                return s
        return None

    def get_tier_types_with_counts(self):
        """获取各类型的梯度规则数量"""
        rules = self.get_all_tier_rules()
        result = {}
        for t in COMMISSION_TIER_TYPES:
            count = len([r for r in rules if r.get("类型") == t and r.get("状态") in ("启用", "")])
            result[t] = count
        return result
