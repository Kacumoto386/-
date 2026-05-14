"""自动编号生成模块"""
from datetime import datetime


class AutoNumber:
    """为各模块生成唯一编号"""

    def __init__(self, engine):
        self.engine = engine

    def _get_next_seq(self, sheet_name, prefix, col=1, digit_count=4):
        """通用编号生成：前缀 + 年月日 + N位序号"""
        today = datetime.now().strftime("%Y%m%d")
        full_prefix = f"{prefix}{today}"
        ws = self.engine.get_sheet(sheet_name)
        max_row = ws.max_row
        for row in range(max_row, 1, -1):
            val = ws.cell(row=row, column=col).value
            if val and str(val).startswith(full_prefix):
                seq = int(str(val)[-digit_count:]) + 1
                return f"{full_prefix}{seq:0{digit_count}d}"
        return f"{full_prefix}{'0' * (digit_count - 1)}1"

    def member_id(self):
        """会员编号：M + 年月日 + 3位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["member"], "M", digit_count=3)

    def staff_id(self):
        """员工编号：E + 3位序号"""
        from config import SHEETS
        ws = self.engine.get_sheet(SHEETS["staff"])
        max_row = ws.max_row
        for row in range(max_row, 1, -1):
            val = ws.cell(row=row, column=1).value
            if val and str(val).startswith("E"):
                seq = int(str(val)[1:]) + 1
                return f"E{seq:03d}"
        return "E001"

    def course_id(self):
        """课程编号：C + 3位序号"""
        from config import SHEETS
        ws = self.engine.get_sheet(SHEETS["course"])
        max_row = ws.max_row
        for row in range(max_row, 1, -1):
            val = ws.cell(row=row, column=1).value
            if val and str(val).startswith("C"):
                seq = int(str(val)[1:]) + 1
                return f"C{seq:03d}"
        return "C001"

    def sale_id(self):
        """售课编号：S + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["sale"], "S", digit_count=4)

    def class_id(self):
        """上课编号：CL + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["class_record"], "CL", digit_count=4)

    def class_record_id(self):
        """上课编号别名（兼容旧的调用）"""
        return self.class_id()

    def recharge_id(self):
        """充值编号：R + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["recharge"], "R", digit_count=4)

    def alert_id(self):
        """提醒编号：A + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["alert"], "A", digit_count=4)

    def log_id(self):
        """日志编号：L + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["log"], "L", digit_count=4)

    def booking_id(self):
        """预约编号：B + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["booking"], "B", digit_count=4)

    def package_id(self):
        """课程包编号：PK + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["lesson_package"], "PK", digit_count=4)

    def product_id(self):
        """商品编号：PR + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["product"], "PR", digit_count=4)

    def product_sale_id(self):
        """零售编号：PS + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["product_sale"], "PS", digit_count=4)

    def body_measurement_id(self):
        """体测编号：BM + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["body_measurement"], "BM", digit_count=4)



    def transfer_id(self):
        """生成转移编号 T + 日期 + 序号"""
        from config import TRANSFER_LOG_SHEET
        return self._get_next_seq(TRANSFER_LOG_SHEET, "T", digit_count=4)

    def user_id(self):
        """生成用户编号 U + 日期 + 序号"""
        from config import STORE_USER_SHEET
        return self._get_next_seq(STORE_USER_SHEET, "U", digit_count=3)

    def contract_id(self):
        """合同编号：CT + 年月日 + 4位序号"""
        return self._get_next_seq("合同管理", "CT", digit_count=4)

    def membership_id(self):
        """会籍卡编号：MC + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["membership"], "MC", digit_count=4)

    def checkin_id(self):
        """进场编号：CI + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["checkin"], "CI", digit_count=4)

    def card_product_id(self):
        """卡产品编号：CP + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["card_product"], "CP", digit_count=4)

    def group_package_id(self):
        """团课打包编号：GP + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["group_package"], "GP", digit_count=4)

    def monthly_pass_id(self):
        """包月团课编号：MP + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["monthly_pass"], "MP", digit_count=4)

    def tier_id(self):
        """梯度编号：T + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["commission_tier"], "T", digit_count=4)

    def band_id(self):
        """手环编号：WB + 年月日 + 4位序号"""
        from config import SHEETS
        return self._get_next_seq(SHEETS["wristband"], "WB", digit_count=4)