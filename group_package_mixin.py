# -*- coding: utf-8 -*-
"""
团课打包产品 & 包月团课业务逻辑
V2.12.0
"""
from datetime import date, datetime, timedelta
from config import (
    SHEETS, HEADERS,
    GROUP_PACKAGE_HEADERS, GROUP_PACKAGE_STATUSES,
    GROUP_PACKAGE_TYPES,
    MONTHLY_PASS_HEADERS, MONTHLY_PASS_STATUSES,
)


class GroupPackageMixin:
    """团课打包产品 & 包月团课相关方法"""

    def _ensure_group_package_sheet(self):
        """确保团课打包产品Sheet存在且有表头"""
        ws = self.engine.get_sheet(SHEETS["group_package"])
        existing = self.engine.get_headers(SHEETS["group_package"])
        if not existing or all(h == "" or h is None for h in existing):
            for i, h in enumerate(GROUP_PACKAGE_HEADERS, 1):
                ws.cell(row=3, column=i, value=h)
            self.engine.save()

    def _ensure_monthly_pass_sheet(self):
        """确保包月团课Sheet存在且有表头"""
        ws = self.engine.get_sheet(SHEETS["monthly_pass"])
        existing = self.engine.get_headers(SHEETS["monthly_pass"])
        if not existing or all(h == "" or h is None for h in existing):
            for i, h in enumerate(MONTHLY_PASS_HEADERS, 1):
                ws.cell(row=3, column=i, value=h)
            self.engine.save()

    # ──────────────────────────────────────────
    # 1. 团课打包产品 CRUD
    # ──────────────────────────────────────────

    def add_group_package(self, data):
        """新增团课打包产品"""
        self._ensure_group_package_sheet()
        errors = []
        if not data.get("打包名称"):
            errors.append("打包名称不能为空")
        courses_str = data.get("包含课程", "")
        if not courses_str:
            errors.append("请选择包含的课程")
        ptype = data.get("打包类型", "")
        if ptype not in GROUP_PACKAGE_TYPES:
            errors.append("打包类型无效")
        if errors:
            return {"success": False, "error": errors[0]}

        # 解析包含课程
        course_ids = [c.strip() for c in courses_str.split(",") if c.strip()]
        course_names = []
        for cid in course_ids:
            course = self.get_course(cid)
            if course:
                course_names.append(course.get("课程名称", cid))
        course_name_str = " / ".join(course_names)

        pkg_id = self.autonum.group_package_id()
        today = date.today()

        row_data = {
            "打包编号": pkg_id,
            "打包名称": data.get("打包名称", ""),
            "包含课程": courses_str,
            "课程名称列表": course_name_str,
            "打包类型": ptype,
            "总次数": self._safe_int(data.get("总次数", 0)) if ptype == "计次打包" else 0,
            "标准售价": self._safe_float(data.get("标准售价", 0)),
            "优惠售价": self._safe_float(data.get("优惠售价", 0)),
            "有效期(天)": self._safe_int(data.get("有效期(天)", 30)),
            "状态": data.get("状态", "上架"),
            "创建日期": today,
            "备注": data.get("备注", ""),
            "门店编号": data.get("门店编号", ""),
        }
        self.engine.append_row(SHEETS["group_package"], row_data)
        return {"success": True, "package_id": pkg_id, "message": f"打包产品 {pkg_id} 添加成功"}

    def get_all_group_packages(self):
        """获取所有团课打包产品"""
        self._ensure_group_package_sheet()
        return self.engine.get_all_data(SHEETS["group_package"])

    def get_group_package(self, pkg_id):
        """根据编号获取团课打包产品"""
        for p in self.get_all_group_packages():
            if p.get("打包编号") == pkg_id:
                return p
        return None

    def get_on_sale_group_packages(self):
        """获取上架的团课打包产品（仅计次打包）"""
        return [p for p in self.get_all_group_packages()
                if p.get("状态") == "上架"]

    def update_group_package(self, row_num, data):
        """更新团课打包产品"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["group_package"], key)
            if col:
                self.engine.write_cell(SHEETS["group_package"], row_num, col, value)
        return {"success": True, 'message': '打包产品已更新'}

    def delete_group_package(self, row_num):
        """删除团课打包产品"""
        self.engine.delete_row(SHEETS["group_package"], row_num)
        return {"success": True, 'message': '打包产品已删除'}

    # ──────────────────────────────────────────
    # 2. 包月团课 CRUD
    # ──────────────────────────────────────────

    def add_monthly_pass(self, data):
        """购买包月团课"""
        self._ensure_monthly_pass_sheet()
        errors = []
        if not data.get("月卡名称"):
            errors.append("月卡名称不能为空")
        if not data.get("会员编号"):
            errors.append("请选择会员")
        courses_str = data.get("包含课程", "")
        if not courses_str:
            errors.append("请选择包含的课程")
        if errors:
            return {"success": False, "error": errors[0]}

        # 解析包含课程
        course_ids = [c.strip() for c in courses_str.split(",") if c.strip()]
        course_names = []
        for cid in course_ids:
            course = self.get_course(cid)
            if course:
                course_names.append(course.get("课程名称", cid))
        course_name_str = " / ".join(course_names)

        pass_id = self.autonum.monthly_pass_id()
        today = date.today()
        days = self._safe_int(data.get("有效期(天)", 30))
        valid_from = today
        valid_to = today + timedelta(days=days)

        row_data = {
            "月卡编号": pass_id,
            "月卡名称": data.get("月卡名称", ""),
            "会员编号": data.get("会员编号", ""),
            "会员姓名": data.get("会员姓名", ""),
            "包含课程": courses_str,
            "课程名称列表": course_name_str,
            "售价": self._safe_float(data.get("售价", 0)),
            "有效期起": valid_from,
            "有效期止": valid_to,
            "状态": "有效",
            "购买日期": today,
            "备注": data.get("备注", ""),
            "门店编号": data.get("门店编号", ""),
        }
        self.engine.append_row(SHEETS["monthly_pass"], row_data)
        return {"success": True, "monthly_pass_id": pass_id,
                "message": f"包月团课 {pass_id} 购买成功"}

    def get_all_monthly_passes(self):
        """获取所有包月团课"""
        self._ensure_monthly_pass_sheet()
        return self.engine.get_all_data(SHEETS["monthly_pass"])

    def get_member_monthly_passes(self, member_id):
        """获取某会员的包月团课"""
        return [m for m in self.get_all_monthly_passes()
                if m.get("会员编号") == member_id]

    def get_member_valid_monthly_passes(self, member_id):
        """获取某会员有效的包月团课（有效期内+状态有效）"""
        today = date.today()
        valid = []
        for m in self.get_member_monthly_passes(member_id):
            if m.get("状态") != "有效":
                continue
            expiry = m.get("有效期止")
            if isinstance(expiry, (datetime, date)):
                if expiry.date() if isinstance(expiry, datetime) else expiry < today:
                    continue
            valid.append(m)
        return valid

    def is_member_covered_by_monthly_pass(self, member_id, course_id):
        """检查会员的包月团课是否覆盖某课程"""
        passes = self.get_member_valid_monthly_passes(member_id)
        for mp in passes:
            courses = [c.strip() for c in mp.get("包含课程", "").split(",") if c.strip()]
            if course_id in courses:
                return True, mp
        return False, None

    def update_monthly_pass_status(self):
        """自动更新过期的包月团课状态"""
        today = date.today()
        for mp in self.get_all_monthly_passes():
            if mp.get("状态") != "有效":
                continue
            expiry = mp.get("有效期止")
            if isinstance(expiry, datetime):
                expiry = expiry.date()
            if isinstance(expiry, date) and expiry < today:
                row = mp.get("_row")
                if row:
                    col = self.engine.get_header_col(SHEETS["monthly_pass"], "状态")
                    if col:
                        self.engine.write_cell(SHEETS["monthly_pass"], row, col, "已过期")

    # ──────────────────────────────────────────
    # 3. 售出团课打包（计次打包 → 课程包）
    # ──────────────────────────────────────────

    def sell_group_package(self, member_id, member_name, pkg_id, sale_price=None):
        """售出计次打包产品，生成课程包记录

        计次打包：生成一个课程包，包含所有课程，共享总次数
        """
        pkg = self.get_group_package(pkg_id)
        if not pkg:
            return {"success": False, "error": "打包产品不存在"}
        if pkg.get("打包类型") != "计次打包":
            return {"success": False, "error": "此产品不是计次打包类型"}

        total = self._safe_int(pkg.get("总次数", 0))
        if total <= 0:
            return {"success": False, "error": "打包产品次数无效"}

        course_ids = [c.strip() for c in pkg.get("包含课程", "").split(",") if c.strip()]
        course_names = pkg.get("课程名称列表", "")
        valid_days = self._safe_int(pkg.get("有效期(天)", 30))
        today = date.today()

        # 打包产品生成的课程包：课程名称 = "打包名称(共X门课)"
        pkg_label = f"{pkg.get('打包名称')}({len(course_ids)}门)"
        package_data = {
            "课程包编号": self.autonum.package_id(),
            "售课编号": f"GP_{pkg_id}",
            "会员编号": member_id,
            "会员姓名": member_name,
            "课程编号": ",".join(course_ids),
            "课程名称": pkg_label,
            "总课时": total,
            "已消耗课时": 0,
            "剩余课时": total,
            "有效期起": today,
            "有效期止": today + timedelta(days=valid_days),
            "状态": "有效",
            "门店编号": pkg.get("门店编号", ""),
        }
        self.engine.append_row(SHEETS["lesson_package"], package_data)
        return {"success": True, "package_num": package_data["课程包编号"],
                "message": f"打包产品售出成功，课程包 {package_data['课程包编号']} 已创建"}

    def consume_from_group_package(self, member_id, course_id, consume_qty=1):
        """从团课打包课程包中扣减次数

        找到会员的该类打包课程包（按课程编号匹配包含课程），扣减1次
        Returns: (success, package) or (False, None)
        """
        packages = [p for p in self.get_all_packages()
                    if p.get("会员编号") == member_id
                    and p.get("状态") == "有效"]
        for p in packages:
            course_ids_str = p.get("课程编号", "")
            course_ids = [c.strip() for c in course_ids_str.split(",") if c.strip()]
            if course_id in course_ids:
                remaining = self._safe_int(p.get("剩余课时", 0))
                consumed = self._safe_int(p.get("已消耗课时", 0))
                if remaining >= consume_qty:
                    new_remaining = remaining - consume_qty
                    new_consumed = consumed + consume_qty
                    row = p.get("_row")
                    if row:
                        self.engine.update_cell(SHEETS["lesson_package"], row,
                                                 "剩余课时", new_remaining)
                        self.engine.update_cell(SHEETS["lesson_package"], row,
                                                 "已消耗课时", new_consumed)
                        if new_remaining <= 0:
                            self.engine.update_cell(SHEETS["lesson_package"], row,
                                                     "状态", "已用完")
                    return True, p
        return False, None
