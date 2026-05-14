"""
API路由 - 定义所有对外接口及其处理逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.serializers import (
    api_response, serialize, serialize_member, serialize_staff,
    serialize_course, serialize_booking, serialize_sale, serialize_product
)
from datetime import date


class ApiRoutes:
    """API路由注册 - 所有对外接口"""

    def __init__(self, biz):
        self.biz = biz
        self.routes = {}  # method_path -> handler
        self._register()

    def _register(self):
        """注册所有路由"""
        # 会员
        self._add("GET", "/api/members", self.get_members)
        self._add("GET", "/api/members/<id>", self.get_member)
        self._add("POST", "/api/members", self.create_member)
        self._add("PUT", "/api/members/<id>", self.update_member)
        self._add("DELETE", "/api/members/<id>", self.delete_member)

        # 员工
        self._add("GET", "/api/staff", self.get_staff_list)
        self._add("GET", "/api/staff/<id>", self.get_staff)

        # 课程
        self._add("GET", "/api/courses", self.get_courses)
        self._add("GET", "/api/courses/<id>", self.get_course)

        # 售课
        self._add("GET", "/api/sales", self.get_sales)
        self._add("POST", "/api/sales", self.create_sale)

        # 预约
        self._add("GET", "/api/bookings", self.get_bookings)
        self._add("POST", "/api/bookings", self.create_booking)
        self._add("PUT", "/api/bookings/<id>/signin", self.signin_booking)
        self._add("PUT", "/api/bookings/<id>/cancel", self.cancel_booking)

        # 上课
        self._add("GET", "/api/class-records", self.get_class_records)

        # 商品
        self._add("GET", "/api/products", self.get_products)

        # 统计
        self._add("GET", "/api/stats/dashboard", self.get_stats_dashboard)

        # 预留支付接口
        self._add("POST", "/api/payments/notify", self.payment_notify)  # 支付回调预留
        self._add("POST", "/api/payments/refund", self.payment_refund)  # 退款预留

    def _add(self, method, path, handler):
        """注册路由"""
        self.routes[f"{method} {path}"] = handler

    def dispatch(self, method, path, params=None, data=None):
        """分发请求到对应处理器"""
        # 先尝试精确匹配
        route_key = f"{method} {path}"
        if route_key in self.routes:
            try:
                return self.routes[route_key](params=params, data=data)
            except Exception as e:
                import traceback
                return api_response(False, message=f"处理请求失败: {str(e)}")

        # 尝试带参数的路由
        for key, handler in self.routes.items():
            if key.startswith(f"{method} ") and "<" in key:
                pattern = key.split(" ", 1)[1]
                matched, path_params = self._match_path(pattern, path)
                if matched:
                    try:
                        combined = dict(path_params)
                        if params:
                            combined.update(params)
                        return handler(params=combined, data=data)
                    except Exception as e:
                        return api_response(False, message=f"处理请求失败: {str(e)}")

        return api_response(False, message=f"未找到路由: {method} {path}")

    def _match_path(self, pattern, path):
        """匹配带参数路径，如 /api/members/<id> 匹配 /api/members/M001"""
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")
        if len(pattern_parts) != len(path_parts):
            return False, {}
        params = {}
        for i, pp in enumerate(pattern_parts):
            if pp.startswith("<") and pp.endswith(">"):
                params[pp[1:-1]] = path_parts[i]
            elif pp != path_parts[i]:
                return False, {}
        return True, params

    # ==================== 会员接口 ====================

    def get_members(self, params=None, data=None):
        """获取会员列表（支持搜索）"""
        keyword = (params or {}).get("keyword", "")
        members = self.biz.search_members(keyword) if keyword else self.biz.get_all_members()
        return api_response(True, [serialize_member(m) for m in members], total=len(members))

    def get_member(self, params=None, data=None):
        """获取单个会员"""
        member_id = (params or {}).get("id", "")
        member = self.biz.get_member(member_id)
        if member:
            return api_response(True, serialize_member(member))
        return api_response(False, message=f"会员 {member_id} 不存在")

    def create_member(self, params=None, data=None):
        """新增会员"""
        if not data:
            return api_response(False, message="缺少会员数据")
        result = self.biz.add_member(data)
        return api_response(result["success"], message=result["message"])

    def update_member(self, params=None, data=None):
        """更新会员"""
        member_id = (params or {}).get("id", "")
        member = self.biz.get_member(member_id)
        if not member:
            return api_response(False, message=f"会员 {member_id} 不存在")
        if not data:
            return api_response(False, message="缺少更新数据")
        row_num = member.get("_row", 0)
        result = self.biz.update_member(row_num, data)
        return api_response(result["success"], message=result["message"])

    def delete_member(self, params=None, data=None):
        """删除会员"""
        member_id = (params or {}).get("id", "")
        member = self.biz.get_member(member_id)
        if not member:
            return api_response(False, message=f"会员 {member_id} 不存在")
        row_num = member.get("_row", 0)
        result = self.biz.delete_member(row_num, member_id)
        return api_response(result["success"], message=result["message"])

    # ==================== 员工接口 ====================

    def get_staff_list(self, params=None, data=None):
        """获取员工列表"""
        staff = self.biz.get_all_staff()
        return api_response(True, [serialize_staff(s) for s in staff], total=len(staff))

    def get_staff(self, params=None, data=None):
        """获取单个员工"""
        staff_id = (params or {}).get("id", "")
        s = self.biz.get_staff(staff_id)
        if s:
            return api_response(True, serialize_staff(s))
        return api_response(False, message=f"员工 {staff_id} 不存在")

    # ==================== 课程接口 ====================

    def get_courses(self, params=None, data=None):
        """获取课程列表"""
        courses = self.biz.get_all_courses()
        return api_response(True, [serialize_course(c) for c in courses], total=len(courses))

    def get_course(self, params=None, data=None):
        """获取单个课程"""
        course_id = (params or {}).get("id", "")
        c = self.biz.get_course(course_id)
        if c:
            return api_response(True, serialize_course(c))
        return api_response(False, message=f"课程 {course_id} 不存在")

    # ==================== 售课接口 ====================

    def get_sales(self, params=None, data=None):
        """获取售课记录"""
        sales = self.biz.get_all_sales()
        return api_response(True, [serialize_sale(s) for s in sales], total=len(sales))

    def create_sale(self, params=None, data=None):
        """创建售课"""
        if not data:
            return api_response(False, message="缺少售课数据")
        result = self.biz.add_sale(data)
        return api_response(result["success"], message=result["message"])

    # ==================== 预约接口 ====================

    def get_bookings(self, params=None, data=None):
        """获取预约列表（支持日期筛选）"""
        p = params or {}
        date_filter = p.get("date", "")
        all_bookings = self.biz.get_all_bookings()
        if date_filter:
            all_bookings = [b for b in all_bookings if str(b.get("预约日期", ""))[:10] == date_filter[:10]]
        return api_response(True, [serialize_booking(b) for b in all_bookings], total=len(all_bookings))

    def create_booking(self, params=None, data=None):
        """创建预约"""
        if not data:
            return api_response(False, message="缺少预约数据")
        result = self.biz.add_booking(data)
        return api_response(result["success"], message=result["message"])

    def signin_booking(self, params=None, data=None):
        """预约签到"""
        booking_id = (params or {}).get("id", "")
        bookings = self.biz.engine.find_rows("预约管理", {"预约编号": booking_id})
        if not bookings:
            return api_response(False, message=f"预约 {booking_id} 不存在")
        row_num = bookings[0].get("_row", 0)
        result = self.biz.sign_in_booking(row_num)
        return api_response(result["success"], message=result["message"])

    def cancel_booking(self, params=None, data=None):
        """取消预约"""
        booking_id = (params or {}).get("id", "")
        bookings = self.biz.engine.find_rows("预约管理", {"预约编号": booking_id})
        if not bookings:
            return api_response(False, message=f"预约 {booking_id} 不存在")
        row_num = bookings[0].get("_row", 0)
        result = self.biz.cancel_booking(row_num)
        return api_response(result["success"], message=result["message"])

    # ==================== 上课接口 ====================

    def get_class_records(self, params=None, data=None):
        """获取上课记录"""
        records = self.biz.get_all_class_records()
        return api_response(True, [serialize(r) for r in records], total=len(records))

    # ==================== 商品接口 ====================

    def get_products(self, params=None, data=None):
        """获取商品列表"""
        products = self.biz.get_all_products()
        return api_response(True, [serialize_product(p) for p in products], total=len(products))

    # ==================== 统计接口 ====================

    def get_stats_dashboard(self, params=None, data=None):
        """获取仪表盘统计数据"""
        stats = self.biz.get_dashboard_stats()
        stats = serialize(stats)
        return api_response(True, stats)

    # ==================== 支付预留接口 ====================

    def payment_notify(self, params=None, data=None):
        """支付回调（预留）"""
        # TODO: 对接微信支付回调后实现
        return api_response(True, message="支付回调接口已就绪（待对接支付网关）")

    def payment_refund(self, params=None, data=None):
        """退款处理（预留）"""
        # TODO: 对接微信支付退款后实现
        return api_response(True, message="退款接口已就绪（待对接支付网关）")
