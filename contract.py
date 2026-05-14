# -*- coding: utf-8 -*-
"""
合同管理引擎 — 合同增删改查 / 签署 / 到期提醒
V2.6.0
"""
import datetime


class ContractManager:
    """合同管理引擎"""

    def __init__(self, biz):
        self.biz = biz
        self.today = datetime.date.today()
    def _ensure_sheet(self):
        """确保合同管理Sheet存在且有表头"""
        from config import CONTRACT_HEADERS
        ws = self.biz.engine.get_sheet("合同管理")
        existing = self.biz.engine.get_headers("合同管理")
        if not existing or all(h == "" or h is None for h in existing):
            for i, h in enumerate(CONTRACT_HEADERS, 1):
                ws.cell(row=3, column=i, value=h)
            self.biz.engine.save()



    # ── 基础 CRUD ──

    def add_contract(self, data):
        """新增合同"""
        from core.auto_num import AutoNumber
        num = AutoNumber(self.biz.engine)
        cid = num.contract_id()

        row = {
            "合同编号": cid,
            "合同类型": data.get("合同类型", ""),
            "会员编号": data.get("会员编号", ""),
            "会员姓名": data.get("会员姓名", ""),
            "合同金额": data.get("合同金额", 0),
            "合同内容摘要": data.get("合同内容摘要", ""),
            "签署日期": data.get("签署日期", str(self.today)),
            "有效期起": data.get("有效期起", ""),
            "有效期止": data.get("有效期止", ""),
            "签署状态": data.get("签署状态", "待签署"),
            "签署方式": data.get("签署方式", "纸质"),
            "门店编号": data.get("门店编号", ""),
            "操作员": data.get("操作员", ""),
            "备注": data.get("备注", ""),
            "附件路径": data.get("附件路径", ""),
        }

        success = self.biz.engine.append_row("合同管理", row)
        if success:
            return {"success": True, "message": "合同已创建", "contract_id": cid}
        return {"success": False, "message": "创建失败"}

    def get_all_contracts(self):
        """获取所有合同"""
        self._ensure_sheet()
        return self.biz.engine.get_all_data("合同管理")

    def get_contract(self, contract_id):
        """获取单个合同"""
        for c in self.get_all_contracts():
            if c.get("合同编号") == contract_id:
                return c
        return None

    def get_member_contracts(self, member_id):
        """获取某个会员的所有合同"""
        return [c for c in self.get_all_contracts()
                if c.get("会员编号") == member_id]

    def update_contract(self, row_idx, data):
        """更新合同"""
        for key, val in data.items():
            col = self.biz.engine.get_header_col("合同管理", key)
            if col:
                self.biz.engine.write_cell("合同管理", row_idx, col, val)
        return {"success": True, "message": "已更新"}

    def delete_contract(self, row_idx):
        """删除合同"""
        self.biz.engine.delete_row("合同管理", row_idx)
        return {"success": True, "message": "已删除"}

    # ── 业务流程 ──

    def sign_contract(self, contract_id):
        """签署合同"""
        c = self.get_contract(contract_id)
        if not c:
            return {"success": False, "message": "合同不存在"}
        if c.get("签署状态") == "已签署":
            return {"success": False, "message": "合同已签署，不可重复签署"}
        self.update_contract(c["_row"], {
            "签署状态": "已签署",
            "签署日期": str(self.today),
        })
        return {"success": True, "message": "签署成功"}

    def void_contract(self, contract_id):
        """作废合同"""
        c = self.get_contract(contract_id)
        if not c:
            return {"success": False, "message": "合同不存在"}
        self.update_contract(c["_row"], {"签署状态": "已作废"})
        return {"success": True, "message": "已作废"}

    # ── 到期提醒 ──

    def get_expiring_contracts(self, within_days=30):
        """获取即将到期的合同"""
        result = []
        for c in self.get_all_contracts():
            expire = c.get("有效期止", "")
            if not expire:
                continue
            try:
                if isinstance(expire, datetime.datetime):
                    expire_date = expire.date()
                elif isinstance(expire, datetime.date):
                    expire_date = expire
                else:
                    expire_date = datetime.datetime.strptime(str(expire)[:10],
                                                             "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            remaining = (expire_date - self.today).days
            if 0 <= remaining <= within_days:
                result.append({**c, "剩余天数": remaining})
        # 按剩余天数排序
        result.sort(key=lambda x: x.get("剩余天数", 999))
        return result

    def search_contracts(self, keyword):
        """搜索合同（按编号/会员姓名/合同类型）"""
        kw = str(keyword).strip().lower()
        if not kw:
            return []
        results = []
        for c in self.get_all_contracts():
            if (kw in str(c.get("合同编号", "")).lower() or
                kw in str(c.get("会员姓名", "")).lower() or
                kw in str(c.get("合同类型", "")).lower()):
                results.append(c)
        return results

    # ── 统计 ──

    def get_contract_stats(self):
        """合同统计"""
        contracts = self.get_all_contracts()
        total = len(contracts)
        signed = sum(1 for c in contracts if c.get("签署状态") == "已签署")
        pending = sum(1 for c in contracts if c.get("签署状态") == "待签署")
        voided = sum(1 for c in contracts if c.get("签署状态") == "已作废")
        expiring = len(self.get_expiring_contracts(30))
        return {
            "total": total,
            "signed": signed,
            "pending": pending,
            "voided": voided,
            "expiring_soon": expiring,
        }
