"""
会员服务 Mixin - 会员模块
"""
from datetime import date
from config import SHEETS, HEADERS


class MemberMixin:
    """会员管理相关方法"""

    def add_member(self, data):
        """添加会员"""
        name = data.get("姓名", "").strip()
        if not name:
            return {"success": False, "error": "会员姓名不能为空"}

        phone = data.get("手机号", "").strip()
        if phone and not self.validate_phone_unique("member", phone):
            return {"success": False, "error": "手机号已存在"}

        gender = data.get("性别", "男")
        join_date = data.get("加入日期", date.today().strftime("%Y-%m-%d"))

        member_id = self.autonum.member_id()
        row_data = {
            "会员编号": member_id,
            "姓名": name,
            "手机号": phone,
            "性别": gender,
            "出生日期": data.get("出生日期", ""),
            "身份证号": data.get("身份证号", ""),
            "紧急联系人": data.get("紧急联系人", ""),
            "联系电话": data.get("联系电话", ""),
            "会员等级": data.get("会员等级", "普通会员"),
            "加入日期": join_date,
            "会员有效期": data.get("会员有效期", ""),
            "剩余课时": self._safe_float(data.get("剩余课时", 0)),
            "总购课时": self._safe_float(data.get("总购课时", 0)),
            "会员状态": data.get("会员状态", "有效"),
            "来源渠道": data.get("来源渠道", ""),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["member"], row_data)
        self._member_cache = None
        return {"success": True, "member_id": member_id, 'message': '会员添加成功'}

    def update_member(self, row_num, data):
        """更新会员信息"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["member"], key)
            if col:
                self.engine.write_cell(SHEETS["member"], row_num, col, value)
        self._member_cache = None
        return {"success": True, 'message': '会员信息已更新'}

    def update_member_photo_path(self, row_num, photo_path):
        """更新会员照片路径"""
        col = self.engine.get_header_col(SHEETS["member"], "照片路径")
        if col:
            self.engine.write_cell(SHEETS["member"], row_num, col, photo_path)
        self._member_cache = None

    def get_member_photo_path(self, member_id):
        """获取会员照片路径"""
        member = self.get_member(member_id)
        if member:
            return member.get("照片路径", "") or ""
        return ""

    def delete_member(self, row_num, member_id=None):
        """删除会员"""
        # 如果传入了会员编号，清理对应照片
        if member_id:
            from utils.photo_utils import delete_photo
            delete_photo(member_id)
        self.engine.delete_row(SHEETS["member"], row_num)
        self._member_cache = None
        return {"success": True, 'message': '会员已删除'}

    def search_members(self, keyword):
        """搜索会员"""
        result = []
        for m in self.get_all_members():
            if keyword in str(m.get("姓名", "")) or keyword in str(m.get("手机号", "")):
                result.append(m)
        return result

    def get_all_members(self):
        """获取所有会员"""
        if self._member_cache is None:
            self._member_cache = self.engine.get_all_data(SHEETS["member"])
        return self._member_cache

    def get_member(self, member_id):
        """根据会员编号获取会员信息"""
        for m in self.get_all_members():
            if m.get("会员编号") == member_id:
                return m
        return None

    def get_member_id_names(self):
        """获取会员编号-姓名字典"""
        return self.get_id_name_map(self.get_all_members(), "会员编号", "姓名")

    def get_member_packages(self, member_id):
        """获取会员的课程包"""
        result = []
        for p in self.get_all_packages():
            if p.get("会员编号") == member_id:
                result.append(p)
        return result

    def get_member_measurements(self, member_id):
        """获取会员的体测记录"""
        return [m for m in self.get_all_measurements()
                if m.get("会员编号") == member_id]

    def get_product_sales_by_member(self, member_id):
        """获取会员的商品购买记录"""
        return [s for s in self.get_all_product_sales()
                if s.get("会员编号") == member_id]

    def _update_member_lessons(self, member_id, delta_lessons):
        """更新会员剩余课时"""
        for m in self.get_all_members():
            if m.get("会员编号") == member_id:
                current = self._safe_float(m.get("剩余课时", 0))
                total_bought = self._safe_float(m.get("总购课时", 0))
                new_current = current + delta_lessons
                new_total = total_bought + (delta_lessons if delta_lessons > 0 else 0)
                self.update_member(m["_row"], {
                    "剩余课时": new_current,
                    "总购课时": new_total,
                })
                return True
        return False
