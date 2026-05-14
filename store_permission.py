# -*- coding: utf-8 -*-
"""
门店权限管理模块
- 用户角色管理
- 权限验证
- 门店访问控制
"""
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StorePermissionManager:
    """门店权限管理器"""

    def __init__(self, biz, store_mgr):
        self.biz = biz
        self.mgr = store_mgr
        self._setup_sheet()

    def _setup_sheet(self):
        """确保权限Sheet存在"""
        from config import STORE_USER_SHEET, STORE_USER_HEADERS, HEADER_ROW
        if not self.biz.engine.sheet_exists(STORE_USER_SHEET):
            ws = self.biz.engine.wb.create_sheet(title=STORE_USER_SHEET)
            for i, h in enumerate(STORE_USER_HEADERS, 1):
                ws.cell(row=HEADER_ROW, column=i, value=h)

    # ==================== 用户管理 ====================

    def get_all_users(self):
        """获取所有用户"""
        from config import STORE_USER_SHEET
        return self.biz.engine.get_all_data(STORE_USER_SHEET)

    def add_user(self, data):
        """添加用户"""
        from config import STORE_USER_SHEET, STORE_USER_HEADERS, STORE_ROLES

        name = data.get("姓名", "").strip()
        account = data.get("账号", "").strip()
        password = data.get("密码", "123456")
        role = data.get("角色", "staff")
        stores = data.get("管辖门店", "")

        if not name or not account:
            return {"success": False, "message": "姓名和账号不能为空"}

        if role not in STORE_ROLES:
            return {"success": False, "message": f"无效角色: {role}"}

        # 检查账号重复
        existing = self.get_all_users()
        for u in existing:
            if u.get("账号") == account:
                return {"success": False, "message": f"账号「{account}」已存在"}

        # 生成用户编号
        from core.auto_num import AutoNumber
        user_id = AutoNumber(self.biz.engine).user_id()

        row = self.biz.engine.find_next_empty_row(STORE_USER_SHEET)
        self.biz.engine.write_row(STORE_USER_SHEET, row, {
            "用户编号": user_id,
            "姓名": name,
            "账号": account,
            "密码": password,
            "角色": role,
            "管辖门店列表": stores,
            "状态": "启用",
            "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        return {"success": True, "message": f"用户 {name} 创建成功", "user_id": user_id}

    def update_user(self, row_num, data):
        """更新用户"""
        from config import STORE_USER_SHEET
        self.biz.engine.update_row(STORE_USER_SHEET, row_num, data)
        return {"success": True, "message": "用户更新成功"}

    def delete_user(self, row_num):
        """删除用户"""
        from config import STORE_USER_SHEET
        self.biz.engine.delete_row(STORE_USER_SHEET, row_num)
        return {"success": True, "message": "用户已删除"}

    def authenticate(self, account, password):
        """用户认证"""
        users = self.get_all_users()
        for u in users:
            if u.get("账号") == account and u.get("密码") == password:
                if u.get("状态") == "启用":
                    return {
                        "success": True,
                        "user": u,
                        "message": "认证成功",
                    }
                return {"success": False, "message": "账号已被禁用"}
        return {"success": False, "message": "账号或密码错误"}

    # ==================== 权限检查 ====================

    def get_managed_stores(self, user):
        """获取用户管辖的门店列表"""
        from config import STORE_ROLES
        if not user:
            return []

        role = user.get("角色", "")
        if role == "admin":
            # 管理员管辖所有门店
            return self.mgr.get_all_stores()

        store_list_str = user.get("管辖门店列表", "")
        if not store_list_str:
            return []

        store_ids = [s.strip() for s in store_list_str.split(",") if s.strip()]
        result = []
        for sid in store_ids:
            store = self.mgr.get_store(sid)
            if store:
                result.append(store)
        return result

    def has_permission(self, user, permission_key):
        """检查用户是否有某个功能权限"""
        from config import STORE_PERMISSIONS
        if not user:
            return False

        role = user.get("角色", "")
        allowed_roles = STORE_PERMISSIONS.get(permission_key, [])
        return role in allowed_roles

    def can_access_store(self, user, store_id):
        """检查用户是否有权限访问某个门店的数据"""
        if not user:
            return False

        role = user.get("角色", "")
        if role == "admin":
            return True  # 管理员可以访问所有

        store_list = user.get("管辖门店列表", "")
        return store_id in [s.strip() for s in store_list.split(",")]

    def filter_data_by_permission(self, user, data_list, store_id_field="所属门店"):
        """
        根据用户权限过滤数据列表
        admin/auditor 返回全部
        manager/staff 仅返回管辖门店的数据
        """
        if not user:
            return []

        role = user.get("角色", "")
        if role in ["admin", "auditor"]:
            return data_list

        managed_stores = self.get_managed_stores(user)
        managed_ids = set(s.get("门店编号", "") for s in managed_stores)
        if not managed_ids:
            return []

        return [d for d in data_list if d.get(store_id_field, "") in managed_ids]

    # ==================== UI辅助 ====================

    def get_user_display(self, user):
        """获取用户显示信息"""
        from config import STORE_ROLES
        if not user:
            return {"display": "未登录", "color": "#999"}

        role_name = STORE_ROLES.get(user.get("角色", ""), user.get("角色", ""))
        colors = {
            "admin": "#E74C3C",
            "manager": "#2E75B6",
            "staff": "#70AD47",
            "auditor": "#FFC000",
        }
        return {
            "display": f"{user.get('姓名', '')} ({role_name})",
            "color": colors.get(user.get("角色", ""), "#999"),
            "role": user.get("角色", ""),
        }
