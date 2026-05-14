"""
门店管理器 - 连锁/多门店核心模块
管理门店信息、数据映射、跨店查询
"""
import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StoreManager:
    """门店管理器 - 多门店数据隔离与查询"""

    def __init__(self, engine):
        # engine can be BusinessLayer or ExcelEngine - normalize
        from core.excel_engine import ExcelEngine
        from core.business import BusinessLayer
        if isinstance(engine, BusinessLayer):
            self.excel = engine.engine
            self.biz = engine
        elif isinstance(engine, ExcelEngine):
            self.excel = engine
            self.biz = None
        else:
            self.excel = engine
            self.biz = None
        self._setup_sheets()

    def _setup_sheets(self):
        """确保门店相关Sheet存在"""
        from config import STORE_SHEET, STORE_STATS_SHEET, STORE_MAP_SHEET
        for sheet_name, headers_key in [
            (STORE_SHEET, "STORE_HEADERS"),
            (STORE_STATS_SHEET, "STORE_STATS_HEADERS"),
            (STORE_MAP_SHEET, "STORE_MAP_HEADERS"),
        ]:
            if not self.excel.sheet_exists(sheet_name):
                ws = self.excel.wb.create_sheet(title=sheet_name)
                from config import STORE_HEADERS, STORE_STATS_HEADERS, STORE_MAP_HEADERS
                from config import DATA_START_ROW, HEADER_ROW
                headers_map = {
                    "STORE_HEADERS": STORE_HEADERS,
                    "STORE_STATS_HEADERS": STORE_STATS_HEADERS,
                    "STORE_MAP_HEADERS": STORE_MAP_HEADERS,
                }
                headers = headers_map[headers_key]
                # 写表头到第3行（与现有样式一致）
                for i, h in enumerate(headers, 1):
                    ws.cell(row=HEADER_ROW, column=i, value=h)

    # ==================== 门店CRUD ====================

    def get_all_stores(self):
        """获取所有门店"""
        from config import STORE_SHEET
        return self.excel.get_all_data(STORE_SHEET)

    def get_store(self, store_id):
        """获取单个门店"""
        from config import STORE_SHEET
        stores = self.excel.find_rows(STORE_SHEET, {"门店编号": store_id})
        return stores[0] if stores else None

    def add_store(self, data):
        """添加门店"""
        from config import STORE_SHEET, STORE_HEADERS

        # 自动生成门店编号
        existing = self.get_all_stores()
        next_num = len(existing) + 1
        store_id = f"ST{next_num:03d}"

        from config import DATA_START_ROW
        row = self.excel.find_next_empty_row(STORE_SHEET)

        row_data = {
            "门店编号": data.get("门店编号", store_id),
            "门店名称": data.get("门店名称", ""),
            "门店地址": data.get("门店地址", ""),
            "联系电话": data.get("联系电话", ""),
            "店长": data.get("店长", ""),
            "营业时间": data.get("营业时间", ""),
            "门店状态": data.get("门店状态", "营业中"),
            "创建日期": data.get("创建日期", date.today()),
            "备注": data.get("备注", ""),
        }
        self.excel.write_row(STORE_SHEET, row, row_data)
        return {"success": True, "message": f"门店 {store_id} 添加成功", "store_id": store_id}

    def get_current_store(self):
        """获取当前默认门店，返回第一个有效门店或None"""
        stores = self.get_all_stores()
        return stores[0] if stores else None

    def update_store(self, row_num, data):
        """更新门店"""
        from config import STORE_SHEET
        old_data = self.excel.row_to_dict(STORE_SHEET, row_num)
        self.excel.update_row(STORE_SHEET, row_num, data)
        return {"success": True, "message": "门店更新成功"}

    def delete_store(self, row_num, store_id=""):
        """删除门店"""
        from config import STORE_SHEET
        self.excel.delete_row(STORE_SHEET, row_num)
        # 删除关联映射
        self.remove_all_mappings_for_store(store_id)
        return {"success": True, "message": f"门店 {store_id} 已删除"}

    def search_stores(self, keyword=""):
        """搜索门店"""
        from config import STORE_SHEET
        if not keyword:
            return self.get_all_stores()
        return self.excel.search_rows(STORE_SHEET, keyword)

    # ==================== 数据映射管理 ====================

    def map_data_to_store(self, data_type, data_id, store_id):
        """将一条数据关联到门店"""
        from config import STORE_MAP_SHEET
        from config import STORE_MAP_HEADERS, HEADER_ROW

        # 获取门店名称
        store = self.get_store(store_id)
        store_name = store.get("门店名称", "") if store else ""

        # 检查是否已存在映射
        existing = self.excel.find_rows(STORE_MAP_SHEET, {
            "数据类型": data_type,
            "数据编号": data_id,
        })
        if existing:
            # 更新门店信息
            row_num = existing[0].get("_row", 0)
            self.excel.update_row(STORE_MAP_SHEET, row_num, {
                "门店编号": store_id,
                "所属门店": store_name,
                "关联时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            return True

        # 新增映射
        row = self.excel.find_next_empty_row(STORE_MAP_SHEET)
        self.excel.write_row(STORE_MAP_SHEET, row, {
            "关联ID": f"{data_type}_{data_id}_{store_id}",
            "数据类型": data_type,
            "数据编号": data_id,
            "门店编号": store_id,
            "所属门店": store_name,
            "关联时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        return True

    def remove_mapping(self, data_type, data_id):
        """移除数据门店映射"""
        from config import STORE_MAP_SHEET
        existing = self.excel.find_rows(STORE_MAP_SHEET, {
            "数据类型": data_type,
            "数据编号": data_id,
        })
        for item in existing:
            self.excel.delete_row(STORE_MAP_SHEET, item.get("_row", 0))

    def remove_all_mappings_for_store(self, store_id):
        """移除某个门店的所有映射"""
        from config import STORE_MAP_SHEET
        existing = self.excel.find_rows(STORE_MAP_SHEET, {
            "门店编号": store_id,
        })
        for item in existing:
            self.excel.delete_row(STORE_MAP_SHEET, item.get("_row", 0))

    def get_data_ids_for_store(self, store_id, data_type=None):
        """获取某个门店关联的所有数据编号"""
        from config import STORE_MAP_SHEET
        all_maps = self.excel.get_all_data(STORE_MAP_SHEET)
        # 数据可能不是dict格式，需要处理
        results = []
        for m in all_maps:
            if isinstance(m, dict):
                if m.get("门店编号") == store_id:
                    if data_type is None or m.get("数据类型") == data_type:
                        results.append(m)
        return results

    def get_data_for_store(self, biz, sheet_key, store_id):
        """获取某个门店关联的指定类型数据"""
        from config import SHEETS
        all_data = self.excel.get_all_data(SHEETS[sheet_key])

        if not store_id:
            return all_data  # 不筛选

        # 获取门店关联的数据编号
        mapped = self.get_data_ids_for_store(store_id, sheet_key)
        mapped_ids = set(m.get("数据编号", "") for m in mapped)

        # 过滤
        id_field = self._get_id_field(sheet_key)
        if id_field:
            return [d for d in all_data if d.get(id_field, "") in mapped_ids]
        return all_data

    def get_id_field(self, data_type):
        """根据数据类型获取ID字段名"""
        from config import HEADERS
        id_fields = {
            "member": "会员编号",
            "staff": "员工编号",
            "course": "课程编号",
            "sale": "售课编号",
            "class_record": "上课编号",
            "recharge": "充值编号",
            "booking": "预约编号",
            "product": "商品编号",
            "product_sale": "零售编号",
        }
        return id_fields.get(data_type, "")

    def _get_id_field(self, sheet_key):
        """根据Sheet key获取ID字段"""
        return self.get_id_field(sheet_key)

    # ==================== 跨店统计 ====================

    def get_store_stats_summary(self):
        """获取各门店统计数据"""
        from config import STORE_SHEET
        stores = self.get_all_stores()
        store_list = []

        for store in stores:
            store_id = store.get("门店编号", "")
            store_name = store.get("门店名称", "")

            # 获取门店数据映射
            member_ids = self.get_data_ids_for_store(store_id, "member")
            staff_ids = self.get_data_ids_for_store(store_id, "staff")

            store_list.append({
                "store_id": store_id,
                "store_name": store_name,
                "member_count": len(member_ids),
                "staff_count": len(staff_ids),
                "status": store.get("门店状态", ""),
            })

        return store_list

    def _count_by_month(self, data_type, store_id, month=None):
        """统计某门店当月某类型数据数量"""
        from datetime import date
        today = date.today()
        target_month = month if month else today.month
        target_year = today.year

        mapped = self.get_data_ids_for_store(store_id, data_type)
        return len(mapped)

    # ==================== 数据初始化 ====================

    def ensure_default_store(self, biz):
        """确保至少有一个默认门店（单门店模式）"""
        stores = self.get_all_stores()
        if not stores:
            result = self.add_store({
                "门店名称": "总店",
                "门店地址": "",
                "联系电话": "",
                "店长": "",
                "门店状态": "营业中",
            })
            if result["success"]:
                # 将现有所有数据关联到默认门店
                default_store_id = result["store_id"]
                self._map_all_existing_data(biz, default_store_id)
                return default_store_id
        return stores[0].get("门店编号", "ST001") if stores else "ST001"

    def _map_all_existing_data(self, biz, store_id):
        """将现有所有数据关联到指定门店"""
        from config import STORE_DATA_TYPES
        for dtype in STORE_DATA_TYPES:
            getter_name = f"get_all_{dtype}s"
            if hasattr(biz, getter_name):
                items = getattr(biz, getter_name)()
                id_field = self._get_id_field(dtype)
                if id_field:
                    for item in items:
                        data_id = item.get(id_field, "")
                        if data_id:
                            self.map_data_to_store(dtype, data_id, store_id)
