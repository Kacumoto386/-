"""
数据序列化器 - 将业务数据转为JSON兼容格式
处理日期/Decimal等特殊类型的转换
"""
import json
from datetime import date, datetime


class ApiEncoder(json.JSONEncoder):
    """JSON编码器，支持datetime、date等类型"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def serialize(obj):
    """将Python对象转为JSON兼容的dict/list"""
    return json.loads(json.dumps(obj, cls=ApiEncoder))


def api_response(success=True, data=None, message="", total=None):
    """统一API响应格式"""
    resp = {
        "success": success,
        "message": message,
        "data": data if data is not None else [],
    }
    if total is not None:
        resp["total"] = total
    return resp


def serialize_member(member):
    """序列化单个会员记录"""
    return {
        "member_id": member.get("会员编号", ""),
        "name": member.get("姓名", ""),
        "gender": member.get("性别", ""),
        "phone": member.get("手机号", ""),
        "birthday": serialize(member.get("生日")),
        "level": member.get("会员等级", ""),
        "status": member.get("会员状态", ""),
        "join_date": serialize(member.get("加入日期")),
        "expire_date": serialize(member.get("到期日期")),
        "total_lessons": _int(member.get("总购课时")),
        "used_lessons": _int(member.get("已消耗课时")),
        "remaining_lessons": _int(member.get("剩余课时")),
        "recharge_amount": _float(member.get("充值总额")),
        "remaining_amount": _float(member.get("剩余金额")),
        "notes": member.get("备注", ""),
    }


def serialize_staff(staff):
    """序列化单个员工记录"""
    return {
        "staff_id": staff.get("员工编号", ""),
        "name": staff.get("姓名", ""),
        "gender": staff.get("性别", ""),
        "phone": staff.get("手机号", ""),
        "position": staff.get("岗位", ""),
        "hire_date": serialize(staff.get("入职日期")),
        "base_salary": _float(staff.get("底薪")),
        "status": staff.get("在职状态", ""),
        "sale_commission_rate": _float(staff.get("售课提成比例")),
        "class_commission_rate": _float(staff.get("上课提成比例")),
    }


def serialize_course(course):
    """序列化课程"""
    return {
        "course_id": course.get("课程编号", ""),
        "name": course.get("课程名称", ""),
        "type": course.get("课程类型", ""),
        "standard_price": _float(course.get("标准售价")),
        "discount_price": _float(course.get("优惠售价")),
        "standard_lessons": _int(course.get("标准课时")),
        "valid_days": _int(course.get("课程有效期(天)")),
        "max_people": _int(course.get("最大预约人数")),
        "status": course.get("课程状态", ""),
        "sport": course.get("运动项目", ""),
    }


def serialize_booking(booking):
    """序列化预约"""
    return {
        "booking_id": booking.get("预约编号", ""),
        "date": serialize(booking.get("预约日期")),
        "start_time": booking.get("开始时间", ""),
        "end_time": booking.get("结束时间", ""),
        "member_id": booking.get("会员编号", ""),
        "member_name": booking.get("会员姓名", ""),
        "course_id": booking.get("课程编号", ""),
        "course_name": booking.get("课程名称", ""),
        "coach": booking.get("教练姓名", ""),
        "location": booking.get("上课地点", ""),
        "status": booking.get("预约状态", ""),
    }


def serialize_sale(sale):
    """序列化售课记录"""
    return {
        "sale_id": sale.get("售课编号", ""),
        "sale_date": serialize(sale.get("售课日期")),
        "member_id": sale.get("会员编号", ""),
        "member_name": sale.get("会员姓名", ""),
        "course_name": sale.get("课程名称", ""),
        "lessons_bought": _int(sale.get("购买课时数")),
        "lessons_gifted": _int(sale.get("赠送课时数")),
        "total_lessons": _int(sale.get("总课时数")),
        "unit_price": _float(sale.get("单价")),
        "discount": _float(sale.get("折扣")),
        "total_price": _float(sale.get("折后总价")),
        "actual_amount": _float(sale.get("实收金额")),
        "payment_method": sale.get("付款方式", ""),
        "salesperson": sale.get("销售员姓名", ""),
        "status": sale.get("支付状态", ""),
    }


def serialize_product(product):
    """序列化商品"""
    return {
        "product_id": product.get("商品编号", ""),
        "name": product.get("商品名称", ""),
        "category": product.get("商品类别", ""),
        "price": _float(product.get("售价")),
        "cost": _float(product.get("进价")),
        "stock": _int(product.get("库存数量")),
        "unit": product.get("单位", ""),
        "supplier": product.get("供应商", ""),
    }


def _int(val, default=0):
    """安全转整数"""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _float(val, default=0.0):
    """安全转浮点数"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
