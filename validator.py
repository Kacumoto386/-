"""数据校验模块"""
import re
from datetime import datetime


def check_required(data, field, label=None):
    """检查必填字段"""
    name = label or field
    if not data.get(field):
        return f"「{name}」不能为空"
    return None


def check_positive_number(data, field, label=None):
    """检查正数"""
    name = label or field
    val = data.get(field)
    if val is None or val == "":
        return None  # 可选字段
    try:
        num = float(val)
        if num <= 0:
            return f"「{name}」必须大于0"
    except (ValueError, TypeError):
        return f"「{name}」必须是数字"
    return None


def check_phone(data, field="手机号"):
    """检查手机号格式"""
    phone = data.get(field)
    if not phone:
        return None
    if not re.match(r"^1\d{10}$", str(phone)):
        return "手机号格式不正确（需11位数字）"
    return None


def check_in_list(data, field, valid_values, label=None):
    """检查值是否在有效列表中"""
    name = label or field
    val = data.get(field)
    if val and val not in valid_values:
        return f"「{name}」无效，可选值: {'/'.join(valid_values)}"
    return None


def build_errors(*checks):
    """合并多个检查结果为错误列表"""
    return [c for c in checks if c is not None]


class Validator:
    """各模块数据校验"""

    @staticmethod
    def validate_member(data):
        """校验会员信息"""
        return build_errors(
            check_required(data, "姓名"),
            check_required(data, "手机号"),
            check_phone(data),
            check_in_list(data, "性别", ["男", "女"]),
            check_in_list(data, "会员等级", ["普通", "银卡", "金卡", "钻石"]),
            check_in_list(data, "会员状态", ["有效", "即将到期", "已到期", "冻结"]),
            check_in_list(data, "跟进状态", ["正常", "需回访", "流失预警", "已流失"]),
        )

    @staticmethod
    def validate_staff(data):
        """校验员工信息"""
        return build_errors(
            check_required(data, "姓名"),
            check_required(data, "手机号"),
            check_phone(data),
            check_in_list(data, "性别", ["男", "女"]),
            check_in_list(data, "岗位", [
                "销售顾问", "健身教练", "瑜伽教练", "游泳教练",
                "操课教练", "店长", "前台",
            ]),
            check_in_list(data, "员工状态", ["在职", "离职", "休假"]),
        )

    @staticmethod
    def validate_sale(data):
        """校验售课记录"""
        return build_errors(
            check_required(data, "会员编号"),
            check_required(data, "课程编号"),
            check_required(data, "购买课时数"),
            check_positive_number(data, "购买课时数"),
            check_positive_number(data, "实收金额"),
        )

    @staticmethod
    def validate_class_record(data):
        """校验上课记录"""
        return build_errors(
            check_required(data, "会员编号"),
            check_required(data, "课程编号"),
            check_required(data, "授课教练"),
            check_positive_number(data, "消耗课时数"),
        )

    @staticmethod
    def validate_recharge(data):
        """校验充值记录"""
        return build_errors(
            check_required(data, "会员编号"),
            check_required(data, "充值金额"),
            check_positive_number(data, "充值金额"),
        )

    @staticmethod
    def validate_phone_unique(engine, sheet_name, phone, exclude_row=None):
        """校验手机号唯一性"""
        headers = engine.get_headers(sheet_name)
        phone_col = None
        for i, h in enumerate(headers):
            if "手机" in h:
                phone_col = i + 1
                break
        if phone_col is None:
            return True, ""

        ws = engine.get_sheet(sheet_name)
        for row in range(4, ws.max_row + 1):
            val = ws.cell(row=row, column=phone_col).value
            if val and str(val) == str(phone):
                if exclude_row is None or row != exclude_row:
                    return False, f"手机号 {phone} 已存在"
        return True, ""
