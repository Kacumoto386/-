"""
商品/零售服务 Mixin
"""
from datetime import date
from config import SHEETS, HEADERS


class ProductMixin:
    """商品管理相关方法"""

    def add_product(self, data):
        """添加商品"""
        name = data.get("商品名称", "").strip()
        if not name:
            return {"success": False, "error": "商品名称不能为空"}
        product_id = self.autonum.product_id()
        row_data = {
            "商品编号": product_id,
            "商品名称": name,
            "商品类别": data.get("商品类别", ""),
            "进价": self._safe_float(data.get("进价", 0)),
            "售价": self._safe_float(data.get("售价", 0)),
            "库存数量": self._safe_float(data.get("库存数量", 0)),
            "单位": data.get("单位", "个"),
            "供应商": data.get("供应商", ""),
            "商品状态": data.get("商品状态", "上架"),
            "备注": data.get("备注", ""),
        }
        row_data = self._inject_store_id(row_data, data)
        self.engine.append_row(SHEETS["product"], row_data)
        return {"success": True, "product_id": product_id, 'message': '商品添加成功'}

    def update_product(self, row_num, data):
        """更新商品"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["product"], key)
            if col:
                self.engine.write_cell(SHEETS["product"], row_num, col, value)
        return {"success": True, 'message': '商品信息已更新'}

    def delete_product(self, row_num):
        """删除商品"""
        try:
            self.engine.delete_row(SHEETS["product"], row_num)
            return {"success": True, "message": "删除成功"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_products(self):
        """获取所有商品"""
        return self.engine.get_all_data(SHEETS["product"])

    def get_product(self, product_id):
        """获取单个商品"""
        for p in self.get_all_products():
            if p.get("商品编号") == product_id:
                return p
        return None

    def search_products(self, keyword):
        """搜索商品"""
        if not keyword:
            return self.get_all_products()
        return [p for p in self.get_all_products()
                if keyword in str(p.get("商品名称", ""))]

    def add_product_sale(self, data):
        """添加单条商品零售记录（兼容旧调用）"""
        return self._batch_add_product_sales([data])

    def add_cart_product_sale(self, data):
        """添加购物车零售记录（含优惠和储值字段）"""
        product_id = data.get("商品编号", "")
        if not product_id:
            return {"success": False, "error": "商品编号不能为空"}

        name = data.get("商品名称", "")
        qty = self._safe_int(data.get("数量", 1))
        price = self._safe_float(data.get("零售价", 0))
        total = round(price * qty, 2)
        discount = self._safe_float(data.get("优惠金额", 0))
        if discount > total:
            discount = total

        sale_id = self.autonum.product_sale_id()
        today = data.get("零售日期", date.today().strftime("%Y-%m-%d"))

        sale_data = {
            "零售编号": sale_id,
            "零售日期": today,
            **data,
            "数量": qty,
            "单价": price,
            "总价": total,
            "优惠金额": discount,
            "商品名称": name,
        }
        # 默认值
        sale_data.setdefault("会员编号", "")
        sale_data.setdefault("会员姓名", "")
        sale_data.setdefault("支付方式", "微信")
        sale_data.setdefault("销售人员", "")
        sale_data.setdefault("备注", "")

        self.engine.append_row(SHEETS["product_sale"], sale_data)

        # 扣减库存
        products = self.get_all_products()
        product = next((p for p in products if p.get("商品编号") == product_id), None)
        if product:
            old_stock = self._safe_float(product.get("库存数量", 0))
            new_stock = max(0, old_stock - qty)
            self.update_product(product["_row"], {"库存数量": new_stock})

        return {"success": True, "sale_id": sale_id, 'message': '零售记录添加成功'}

    def _batch_add_product_sales(self, sales_data_list):
        """批量添加零售记录（原 add_product_sale 内部逻辑）"""
        results = []
        for data in sales_data_list:
            result = self.add_cart_product_sale(data)
            results.append(result)
            if not result["success"]:
                return {"success": False, "errors": results}
        return {"success": True, "sale_ids": [r["sale_id"] for r in results], "results": results}

    def get_all_product_sales(self):
        """获取所有零售记录"""
        return self.engine.get_all_data(SHEETS["product_sale"])

    def update_product_sale(self, row_num, data):
        """更新零售记录"""
        for key, value in data.items():
            col = self.engine.get_header_col(SHEETS["product_sale"], key)
            if col:
                self.engine.write_cell(SHEETS["product_sale"], row_num, col, value)
        return {"success": True, 'message': '零售记录已更新'}

    def delete_product_sale(self, row_num):
        """删除零售记录并恢复库存"""
        try:
            sale = None
            for s in self.get_all_product_sales():
                if s.get("_row") == row_num:
                    sale = s
                    break
            if sale:
                product_id = sale.get("商品编号", "")
                qty = self._safe_int(sale.get("数量", 0))
                if product_id and qty > 0:
                    product = self.get_product(product_id)
                    if product:
                        old_stock = self._safe_float(product.get("库存数量", 0))
                        self.update_product(product["_row"], {"库存数量": old_stock + qty})
            self.engine.delete_row(SHEETS["product_sale"], row_num)
            return {"success": True, "message": "删除成功，库存已恢复"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_member_balance(self, member_id):
        """查询会员储值余额（从 recharge Sheet 汇总）"""
        try:
            recharges = self.engine.get_all_data(SHEETS["recharge"])
            balance = 0
            for r in recharges:
                if r.get("会员编号") == member_id:
                    amt = self._safe_float(r.get("充值金额", 0))
                    balance += amt
            return balance
        except Exception:
            return 0

    def deduct_member_balance(self, member_id, amount, operator=""):
        """扣减会员储值余额（在 recharge 表追加负值记录）"""
        from datetime import date
        recharge_data = {
            "充值编号": self.autonum.recharge_id(),
            "会员编号": member_id,
            "会员姓名": "",
            "充值金额": -abs(amount),
            "充值日期": date.today().strftime("%Y-%m-%d"),
            "支付方式": "储值消费",
            "操作员": operator,
            "备注": "商品零售储值扣减",
        }
        self.engine.append_row(SHEETS["recharge"], recharge_data)
        return {"success": True, "new_balance": self.get_member_balance(member_id), 'message': '储值已扣除'}

    def get_member_id_names(self):
        """获取会员编号和姓名的映射"""
        try:
            members = self.engine.get_all_data(SHEETS["member"])
            return [(m.get("会员编号", ""), m.get("姓名", "")) for m in members if m.get("会员编号")]
        except Exception:
            return []

    @staticmethod
    def _safe_float(val, default=0.0):
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_int(val, default=0):
        if val is None:
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    def _inject_store_id(self, row_data, original_data):
        """注入门店编号（如果有）"""
        store_id = original_data.get("store_id", "") or original_data.get("门店编号", "")
        if store_id:
            row_data["门店编号"] = store_id
        return row_data
