# -*- coding: utf-8 -*-
"""
财务管理引擎 v2 — 收入汇总 / 支出管理 / 经营报表
V2.6.0
"""
import datetime
from collections import defaultdict


def _to_date(val):
    """将 str / date / datetime 统一转为 date"""
    if isinstance(val, datetime.datetime):
        return val.date()
    if isinstance(val, datetime.date):
        return val
    if isinstance(val, str):
        val = val.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return val


INCOME_HEADERS = [
    "财务编号", "日期", "收入类型", "分类", "金额",
    "关联模块", "关联编号", "门店编号", "备注"
]
EXPENSE_HEADERS = [
    "财务编号", "日期", "支出类别", "金额", "支付方式",
    "经办人", "发票号", "门店编号", "备注"
]


class FinanceManager:
    """财务管理引擎"""

    def __init__(self, biz):
        self.biz = biz
        self.today = datetime.date.today()

    # ── Sheet 初始化 ──

    def _ensure_sheet(self, sheet_name, headers):
        """确保Sheet存在且有表头"""
        ws = self.biz.engine.get_sheet(sheet_name)
        existing = self.biz.engine.get_headers(sheet_name)
        if not existing or all(h == "" or h is None for h in existing):
            for i, h in enumerate(headers, 1):
                ws.cell(row=3, column=i, value=h)
            self.biz.engine.save()

    def _get_all_data(self, sheet_name):
        """安全获取数据，自动初始化Sheet"""
        self._ensure_sheet(sheet_name,
                           INCOME_HEADERS if "收入" in sheet_name else EXPENSE_HEADERS)
        return self.biz.engine.get_all_data(sheet_name)

    def _get_finance_number(self, prefix):
        from core.auto_num import AutoNumber
        return AutoNumber(self.biz.engine).sale_id()

    # ──────────────────────────────────────────
    # 1. 收入管理
    # ──────────────────────────────────────────

    def sync_income_from_sales(self, year=None, month=None):
        if year is None:
            year = self.today.year
        if month is None:
            month = self.today.month
        sales = self.biz.get_all_sales()
        synced = 0
        for s in sales:
            date_val = s.get("售课日期")
            if isinstance(date_val, datetime.datetime):
                d = date_val.date()
            elif isinstance(date_val, datetime.date):
                d = date_val
            else:
                continue
            if d.year == year and d.month == month:
                self._append_income({
                    "日期": str(d),
                    "收入类型": "售课收入",
                    "分类": s.get("课程名称", ""),
                    "金额": float(s.get("实收金额", 0) or 0),
                    "关联模块": "sale",
                    "关联编号": s.get("售课编号", ""),
                    "门店编号": s.get("门店编号", ""),
                    "备注": "",
                })
                synced += 1
        return synced

    def sync_income_from_recharges(self, year=None, month=None):
        if year is None:
            year = self.today.year
        if month is None:
            month = self.today.month
        recharges = self.biz.get_all_recharges()
        synced = 0
        for r in recharges:
            date_val = r.get("充值日期")
            if isinstance(date_val, datetime.datetime):
                d = date_val.date()
            elif isinstance(date_val, datetime.date):
                d = date_val
            else:
                continue
            if d.year == year and d.month == month:
                self._append_income({
                    "日期": str(d),
                    "收入类型": "充值收入",
                    "分类": r.get("充值类型", ""),
                    "金额": float(r.get("实付金额", 0) or 0),
                    "关联模块": "recharge",
                    "关联编号": r.get("充值编号", ""),
                    "门店编号": r.get("门店编号", ""),
                    "备注": "",
                })
                synced += 1
        return synced

    def sync_income_from_retail(self, year=None, month=None):
        if year is None:
            year = self.today.year
        if month is None:
            month = self.today.month
        retail = self.biz.get_all_product_sales()
        synced = 0
        for s in retail:
            date_val = s.get("零售日期")
            if isinstance(date_val, datetime.datetime):
                d = date_val.date()
            elif isinstance(date_val, datetime.date):
                d = date_val
            else:
                continue
            if d.year == year and d.month == month:
                self._append_income({
                    "日期": str(d),
                    "收入类型": "零售收入",
                    "分类": s.get("商品名称", ""),
                    "金额": float(s.get("总价", 0) or 0),
                    "关联模块": "product_sale",
                    "关联编号": s.get("零售编号", ""),
                    "门店编号": s.get("门店编号", ""),
                    "备注": "",
                })
                synced += 1
        return synced

    def sync_all_income(self, year=None, month=None):
        return {
            "sale": self.sync_income_from_sales(year, month),
            "recharge": self.sync_income_from_recharges(year, month),
            "retail": self.sync_income_from_retail(year, month),
        }

    def _append_income(self, data):
        self._ensure_sheet("收入总账", INCOME_HEADERS)
        fno = self._get_finance_number("FI")
        data["财务编号"] = fno
        return self.biz.engine.append_row("收入总账", data)

    def add_manual_income(self, data):
        self._ensure_sheet("收入总账", INCOME_HEADERS)
        fno = self._get_finance_number("FI")
        data["财务编号"] = fno
        return self.biz.engine.append_row("收入总账", data)

    def get_income_records(self, year=None, month=None, income_type=None, start_date=None, end_date=None):
        """获取收入记录（支持年月筛选 或 日期范围筛选）

        Args:
            year: 年份（与 month 配合使用）
            month: 月份
            income_type: 收入类型过滤
            start_date: 起始日期（str/date），与 end_date 配合使用
            end_date: 结束日期（str/date）
        """
        all_records = self._get_all_data("收入总账")
        results = []
        for r in all_records:
            date_str = str(r.get("日期", ""))[:10]
            try:
                d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            # 日期范围模式
            if start_date or end_date:
                start = _to_date(start_date) if start_date else datetime.date.min
                end = _to_date(end_date) if end_date else datetime.date.max
                if d < start or d > end:
                    continue
            # 年月模式
            else:
                if year and d.year != year:
                    continue
                if month and d.month != month:
                    continue

            if income_type and r.get("收入类型") != income_type:
                continue
            results.append(r)
        return results

    # ──────────────────────────────────────────
    # 2. 支出管理
    # ──────────────────────────────────────────

    def add_expense(self, data):
        self._ensure_sheet("支出记录", EXPENSE_HEADERS)
        fno = self._get_finance_number("FE")
        data["财务编号"] = fno
        if "日期" not in data or not data["日期"]:
            data["日期"] = str(self.today)
        return self.biz.engine.append_row("支出记录", data)

    def get_expenses(self, year=None, month=None, category=None, start_date=None, end_date=None):
        """获取支出记录（支持年月筛选 或 日期范围筛选）"""
        all_records = self._get_all_data("支出记录")
        results = []
        for r in all_records:
            date_str = str(r.get("日期", ""))[:10]
            try:
                d = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            # 日期范围模式
            if start_date or end_date:
                start = _to_date(start_date) if start_date else datetime.date.min
                end = _to_date(end_date) if end_date else datetime.date.max
                if d < start or d > end:
                    continue
            # 年月模式
            else:
                if year and d.year != year:
                    continue
                if month and d.month != month:
                    continue

            if category and r.get("支出类别") != category:
                continue
            results.append(r)
        return results

    def update_expense(self, row_idx, data):
        for key, val in data.items():
            self.biz.engine.update_cell("支出记录", row_idx, key, val)
        return {"success": True, 'message': '支出记录已更新'}

    def delete_expense(self, row_idx):
        self.biz.engine.delete_row("支出记录", row_idx)
        return {"success": True, 'message': '支出已删除'}

    # ──────────────────────────────────────────
    # 3. 报表
    # ──────────────────────────────────────────

    def get_daily_report(self, year, month, day):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        income = self.get_income_records(year, month)
        income_today = [r for r in income if str(r.get("日期", ""))[:10] == date_str]
        expenses = self.get_expenses(year, month)
        exp_today = [e for e in expenses if str(e.get("日期", ""))[:10] == date_str]

        return {
            "date": date_str,
            "total_income": round(sum(float(r.get("金额", 0) or 0) for r in income_today), 2),
            "total_expense": round(sum(float(e.get("金额", 0) or 0) for e in exp_today), 2),
            "profit": round(sum(float(r.get("金额", 0) or 0) for r in income_today) -
                           sum(float(e.get("金额", 0) or 0) for e in exp_today), 2),
            "income_count": len(income_today),
            "expense_count": len(exp_today),
        }

    def get_monthly_report(self, year, month):
        income = self.get_income_records(year, month)
        expenses = self.get_expenses(year, month)
        total_income = sum(float(r.get("金额", 0) or 0) for r in income)
        total_expense = sum(float(e.get("金额", 0) or 0) for e in expenses)

        by_type = defaultdict(float)
        for r in income:
            by_type[r.get("收入类型", "其他")] += float(r.get("金额", 0) or 0)
        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e.get("支出类别", "其他")] += float(e.get("金额", 0) or 0)

        return {
            "year": year,
            "month": month,
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "profit": round(total_income - total_expense, 2),
            "profit_rate": round((total_income - total_expense) / total_income * 100, 1) if total_income else 0,
            "income_count": len(income),
            "expense_count": len(expenses),
            "income_by_type": dict(by_type),
            "expense_by_category": dict(by_cat),
        }

    def get_yearly_report(self, year):
        monthly = [self.get_monthly_report(year, m) for m in range(1, 13)]
        total_income = sum(m["total_income"] for m in monthly)
        total_expense = sum(m["total_expense"] for m in monthly)
        return {
            "year": year,
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "profit": round(total_income - total_expense, 2),
            "profit_rate": round((total_income - total_expense) / total_income * 100, 1) if total_income else 0,
            "monthly": monthly,
        }
