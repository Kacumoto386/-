# -*- coding: utf-8 -*-
"""
门店独立数据报表导出模块
- 按门店筛选导出CSV
- 门店专属报表
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StoreExportManager:
    """门店数据导出管理器"""

    EXPORT_TYPES = [
        ("会员列表", "member", False, ""),
        ("员工列表", "staff", False, ""),
        ("售课记录", "sale", True, "售课日期"),
        ("上课记录", "class_record", True, "上课日期"),
        ("课程包汇总", "lesson_package", False, ""),
        ("预约记录", "booking", True, "预约日期"),
        ("商品列表", "product", False, ""),
        ("零售记录", "product_sale", True, "零售日期"),
        ("体测记录", "body_measurement", True, "体测日期"),
        ("会员充值", "recharge", True, "充值日期"),
        ("操作日志", "log", True, "操作时间"),
    ]

    def __init__(self, biz, store_mgr):
        self.biz = biz
        self.mgr = store_mgr

    def export_store_data(self, store_id, sheet_key, filepath,
                          start_date="", end_date="", date_col=""):
        """
        导出指定门店的数据到CSV
        返回: {"success": bool, "count": int, "message": str}
        """
        from config import SHEETS

        # 获取门店信息
        store = self.mgr.get_store(store_id)
        store_name = store.get("门店名称", store_id) if store else store_id

        # 获取该门店关联的数据
        all_data = self.biz.engine.get_all_data(SHEETS.get(sheet_key, sheet_key))

        # 获取门店关联的数据编号
        mapped = self.mgr.get_data_ids_for_store(store_id, sheet_key)
        mapped_ids = set(m.get("数据编号", "") for m in mapped)

        # 过滤
        id_field = self.mgr.get_id_field(sheet_key)
        if id_field:
            filtered = [d for d in all_data if d.get(id_field, "") in mapped_ids]
        else:
            filtered = list(all_data)

        # 时间过滤
        if start_date and end_date and date_col:
            from datetime import datetime, date
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                filtered2 = []
                for d in filtered:
                    val = d.get(date_col, "")
                    if val:
                        if isinstance(val, datetime):
                            d_date = val.date()
                        elif isinstance(val, date):
                            d_date = val
                        else:
                            try:
                                d_date = datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
                            except ValueError:
                                continue
                        if start_dt <= d_date <= end_dt:
                            filtered2.append(d)
                filtered = filtered2
            except ValueError:
                pass

        if not filtered:
            return {"success": False, "count": 0,
                    "message": f"门店「{store_name}」无相关数据"}

        # 获取列名
        headers = self.biz.get_sheet_column_names(sheet_key)
        if not headers:
            headers = list(filtered[0].keys()) if filtered else []

        # 写入CSV
        import csv
        try:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in filtered:
                    writer.writerow([row.get(h, "") for h in headers])
        except Exception as e:
            return {"success": False, "count": 0,
                    "message": f"写入文件失败: {str(e)}"}

        return {
            "success": True,
            "count": len(filtered),
            "message": f"门店「{store_name}」{sheet_key}数据导出成功 ({len(filtered)}条)",
            "store_name": store_name,
        }

    def export_all_stores_summary(self, filepath):
        """
        导出所有门店数据汇总报表
        每个门店一行，含各维度统计
        """
        from datetime import date
        import csv

        today = date.today()
        stores = self.mgr.get_all_stores()

        rows = [["门店编号", "门店名称", "门店状态", "有效会员数", "员工数",
                 "本月售课额", "本月充值额", "本月零售额", "本月上课数", "统计日期"]]

        for store in stores:
            store_id = store.get("门店编号", "")
            store_name = store.get("门店名称", "")

            member_ids = self.mgr.get_data_ids_for_store(store_id, "member")
            staff_ids = self.mgr.get_data_ids_for_store(store_id, "staff")

            # 售课金额
            sale_mapped = set(m.get("数据编号", "") for m in
                              self.mgr.get_data_ids_for_store(store_id, "sale"))
            sale_amount = 0
            for s in self.biz.get_all_sales():
                if s.get("售课编号", "") in sale_mapped:
                    sd = self.biz._safe_to_date(s.get("售课日期"))
                    if sd and sd.month == today.month:
                        sale_amount += self.biz._safe_float(s.get("实收金额", 0))

            # 充值金额
            recharge_mapped = set(m.get("数据编号", "") for m in
                                  self.mgr.get_data_ids_for_store(store_id, "recharge"))
            recharge_amount = 0
            for r in self.biz.get_all_recharges():
                if r.get("充值编号", "") in recharge_mapped:
                    rd = self.biz._safe_to_date(r.get("充值日期"))
                    if rd and rd.month == today.month:
                        recharge_amount += self.biz._safe_float(r.get("充值金额", 0))

            # 零售
            retail_mapped = set(m.get("数据编号", "") for m in
                                self.mgr.get_data_ids_for_store(store_id, "product_sale"))
            retail_amount = 0
            for p in self.biz.get_all_product_sales():
                if p.get("零售编号", "") in retail_mapped:
                    pd = self.biz._safe_to_date(p.get("零售日期"))
                    if pd and pd.month == today.month:
                        retail_amount += self.biz._safe_float(p.get("总价", 0))

            # 上课数
            class_mapped = set(m.get("数据编号", "") for m in
                               self.mgr.get_data_ids_for_store(store_id, "class_record"))
            class_count = sum(
                1 for c in self.biz.get_all_class_records()
                if c.get("上课编号", "") in class_mapped
            )

            rows.append([
                store_id, store_name, store.get("门店状态", ""),
                len(member_ids), len(staff_ids),
                round(sale_amount, 2), round(recharge_amount, 2),
                round(retail_amount, 2), class_count,
                today.strftime("%Y-%m-%d"),
            ])

        try:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            return {"success": True, "count": len(rows) - 1,
                    "message": f"门店汇总报表导出成功 ({len(rows)-1}个门店)"}
        except Exception as e:
            return {"success": False, "count": 0,
                    "message": f"写入失败: {str(e)}"}
