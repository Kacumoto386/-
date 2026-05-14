"""
业务逻辑层 - BusinessLayer（聚合入口）
使用多继承聚合各领域 Mixin，保持与旧 import 路径兼容
"""
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SHEETS, HEADERS, DATA_START_ROW, PACKAGE_STATUSES
from core.excel_engine import ExcelEngine
from core.auto_num import AutoNumber
from core.validator import Validator
from core.logger import OperationLogger

from core.member_mixin import MemberMixin
from core.staff_mixin import StaffMixin
from core.course_mixin import CourseMixin
from core.class_record_mixin import ClassRecordMixin
from core.booking_mixin import BookingMixin
from core.product_mixin import ProductMixin
from core.other_mixins import RechargeMixin, MeasurementMixin, DashboardMixin, UtilsMixin
from core.membership_mixin import MembershipMixin
from core.checkin_mixin import CheckinMixin
from core.card_product_mixin import CardProductMixin
from core.group_package_mixin import GroupPackageMixin
from core.reactivation_mixin import ReactivationMixin
from core.commission_mixin import CommissionMixin
from core.wristband_mixin import WristbandMixin


class BusinessLayer(
    MemberMixin, StaffMixin, CourseMixin, ClassRecordMixin,
    BookingMixin, ProductMixin, RechargeMixin, MeasurementMixin,
    DashboardMixin, UtilsMixin, MembershipMixin, CheckinMixin,
    CardProductMixin, GroupPackageMixin, ReactivationMixin,
    CommissionMixin, WristbandMixin
):
    """业务逻辑层 - 为各个模块提供数据操作接口"""

    def __init__(self, excel_path=None):
        if excel_path is None:
            from config import EXCEL_PATH
            excel_path = EXCEL_PATH
        self.excel_path = excel_path
        self.engine = ExcelEngine(excel_path)
        self.autonum = AutoNumber(self.engine)
        self.validator = Validator()
        self.logger = OperationLogger(self.engine)
        self.store_mgr = None
        self._member_cache = None
        self._staff_cache = None
        self._course_cache = None

    def _ensure_store_id(self, data):
        """确保门店编号存在（兼容连锁门店模式）"""
        if self.store_mgr and "门店编号" not in data:
            current = self.store_mgr.get_current_store()
            if current:
                data["门店编号"] = current.get("store_id", "")
        return data

    def _inject_store_id(self, row_data, original_data):
        """向行数据注入门店编号"""
        if "门店编号" in original_data:
            row_data["门店编号"] = original_data["门店编号"]
        elif "门店编号" in row_data:
            pass
        elif self.store_mgr:
            current = self.store_mgr.get_current_store()
            if current:
                row_data["门店编号"] = current.get("store_id", "")
        return row_data

    def _safe_to_date(self, val):
        """安全转换为日期"""
        if val is None or val == "":
            return None
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
                try:
                    return datetime.strptime(val.strip(), fmt).date()
                except (ValueError, AttributeError):
                    continue
        return None

    def _safe_int(self, val):
        """安全转换为整数"""
        try:
            return int(val) if val else 0
        except (ValueError, TypeError):
            return 0

    def _safe_float(self, val):
        """安全转换为浮点数"""
        try:
            return float(val) if val else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _safe_to_str(self, val):
        """安全转换为字符串"""
        if val is None:
            return ""
        if hasattr(val, 'strftime'):
            return val.strftime("%Y-%m-%d")
        return str(val).strip()

    def save(self):
        self.engine.save()

    def close(self):
        self.engine.close()
