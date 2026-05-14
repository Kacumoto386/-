"""
可售会籍卡产品目录 - 业务逻辑 Mixin
支持门店自定义可售会籍卡的 CRUD、筛选
"""
from datetime import date
from config import SHEETS, CARD_PRODUCT_STATUSES, CARD_PRODUCT_TYPES


class CardProductMixin:
    """可售会籍卡产品目录相关方法"""

    def get_all_card_products(self):
        """获取所有可售会籍卡"""
        return self.engine.get_all_data(SHEETS["card_product"])

    def get_card_product(self, card_product_id):
        """获取单个卡产品"""
        products = self.get_all_card_products()
        for p in products:
            if p.get("卡产品编号") == card_product_id:
                return p
        return None

    def add_card_product(self, data):
        """新增可售会籍卡产品"""
        from core.validator import check_required, check_in_list, build_errors

        errors = build_errors(
            check_required(data, "卡名称"),
            check_required(data, "卡类型"),
        )

        card_type = data.get("卡类型", "")
        if card_type:
            errors += build_errors(
                check_in_list(data, "卡类型", CARD_PRODUCT_TYPES, "卡类型"),
            )

        if errors:
            return {"success": False, "error": errors[0]}

        card_id = self.autonum.card_product_id()
        today = date.today()

        row_data = {
            "卡产品编号": card_id,
            "卡名称": data.get("卡名称", ""),
            "卡类型": card_type,
            "标准售价": self._safe_float(data.get("标准售价", 0)),
            "总次数": self._safe_int(data.get("总次数", 0)),
            "有效天数": self._safe_int(data.get("有效天数", 0)),
            "储值金额": self._safe_float(data.get("储值金额", 0)),
            "状态": data.get("状态", "上架"),
            "创建日期": today,
            "所属门店": data.get("所属门店", ""),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["card_product"], row_data)

        return {
            "success": True,
            "card_product_id": card_id,
            "message": f"卡产品 {card_id} 添加成功",
        }

    def update_card_product(self, row_num, data):
        """更新可售会籍卡"""
        self.engine.update_row(SHEETS["card_product"], row_num, data)
        return {"success": True, "message": "卡产品更新成功"}

    def delete_card_product(self, row_num):
        """删除可售会籍卡"""
        self.engine.delete_row(SHEETS["card_product"], row_num)
        return {"success": True, "message": "卡产品已删除"}

    def get_card_products_by_type(self, card_type, store_id=None):
        """按卡类型和门店筛选上架的可售会籍卡
        
        Args:
            card_type: 卡类型（次卡/期限卡/现金卡/通卡）
            store_id: 门店编号，None=不过滤门店
            
        Returns:
            list[dict]: 筛选出的卡产品列表
        """
        products = self.get_all_card_products()
        result = []
        for p in products:
            if p.get("状态") != "上架":
                continue
            if p.get("卡类型") != card_type:
                continue
            # 门店过滤：空=全局卡、匹配store_id
            p_store = p.get("所属门店", "")
            if store_id and p_store and p_store != store_id:
                continue
            result.append(p)
        return result

    def get_card_product_options(self, card_type, store_id=None):
        """获取卡产品名称选项列表（供下拉框使用）"""
        products = self.get_card_products_by_type(card_type, store_id)
        options = []
        for p in products:
            name = p.get("卡名称", "")
            pid = p.get("卡产品编号", "")
            price = self._safe_float(p.get("标准售价", 0))
            if card_type == "次卡":
                count = self._safe_int(p.get("总次数", 0))
                label = f"{name} ({pid})  ¥{price:.0f}  {count}次"
            elif card_type == "现金卡":
                amount = self._safe_float(p.get("储值金额", 0))
                label = f"{name} ({pid})  ¥{price:.0f}  储值¥{amount:.0f}"
            elif card_type in ("期限卡", "通卡"):
                days = self._safe_int(p.get("有效天数", 0))
                label = f"{name} ({pid})  ¥{price:.0f}  {days}天"
            else:
                label = f"{name} ({pid})  ¥{price:.0f}"
            options.append((pid, name, label, p))
        return options
