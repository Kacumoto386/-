# -*- coding: utf-8 -*-
"""
门店数据转移与合并管理
- 单条/批量数据门店间转移
- 门店合并（数据归并到目标门店）
"""
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StoreTransferManager:
    """门店数据转移与合并管理器"""

    def __init__(self, biz, store_mgr):
        self.biz = biz
        self.mgr = store_mgr

    # ==================== 数据转移 ====================

    def transfer_data(self, data_type, data_ids, target_store_id,
                      operator="admin", reason=""):
        """
        批量转移数据到目标门店
        data_type: 数据类型 (member/staff/sale/...)
        data_ids: 数据编号列表
        target_store_id: 目标门店编号
        """
        from config import TRANSFER_LOG_SHEET, STORE_MAP_SHEET

        target_store = self.mgr.get_store(target_store_id)
        if not target_store:
            return {"success": False, "count": 0, "message": "目标门店不存在"}

        target_name = target_store.get("门店名称", target_store_id)
        transferred = 0
        errors = []
        log_entries = []

        for data_id in data_ids:
            # 查找现有映射
            existing = self.biz.engine.find_rows(STORE_MAP_SHEET, {
                "数据类型": data_type,
                "数据编号": data_id,
            })

            source_store_ids = set()
            for item in existing:
                source_store_ids.add(item.get("门店编号", ""))
                # 删除旧映射
                self.biz.engine.delete_row(STORE_MAP_SHEET, item.get("_row", 0))

            # 创建新映射到目标门店
            self.mgr.map_data_to_store(data_type, data_id, target_store_id)

            # 记录转移日志
            source_ids_str = ",".join(source_store_ids) if source_store_ids else "无"
            log_entries.append({
                "数据类型": data_type,
                "数据编号": data_id,
                "源门店编号": source_ids_str,
                "目标门店编号": target_store_id,
            })
            transferred += 1

        # 写转移日志
        if log_entries:
            self._write_transfer_log(log_entries, operator, reason)

        return {
            "success": True,
            "count": transferred,
            "message": f"成功转移 {transferred} 条{data_type}数据到「{target_name}」",
            "target_store": target_name,
        }

    def transfer_by_type(self, data_type, source_store_id, target_store_id,
                         operator="admin", reason=""):
        """
        将源门店某类型全部数据转移到目标门店
        """
        mapped = self.mgr.get_data_ids_for_store(source_store_id, data_type)
        data_ids = [m.get("数据编号", "") for m in mapped if m.get("数据编号")]
        if not data_ids:
            return {"success": False, "count": 0, "message": f"源门店无{data_type}数据"}

        return self.transfer_data(data_type, data_ids, target_store_id,
                                  operator, reason)

    def transfer_all_store_data(self, source_store_id, target_store_id,
                                operator="admin", reason=""):
        """
        将源门店所有类型数据转移到目标门店
        （门店合并前置操作）
        """
        from config import STORE_DATA_TYPES
        total = 0
        type_results = []

        for dtype in STORE_DATA_TYPES:
            result = self.transfer_by_type(dtype, source_store_id,
                                           target_store_id, operator, reason)
            if result["success"]:
                total += result["count"]
                type_results.append(f"{dtype}: {result['count']}条")

        return {
            "success": True,
            "count": total,
            "message": f"数据转移完成：{', '.join(type_results)}",
            "types": type_results,
        }

    # ==================== 门店合并 ====================

    def merge_stores(self, source_store_id, target_store_id,
                     operator="admin", delete_source=True):
        """
        合并两个门店：源门店数据归并到目标门店
        1. 转移所有数据到目标门店
        2. 标记源门店为已关闭
        3. 可选：更新所有映射记录
        """
        from config import STORE_SHEET
        source = self.mgr.get_store(source_store_id)
        target = self.mgr.get_store(target_store_id)

        if not source or not target:
            return {"success": False, "message": "源门店或目标门店不存在"}

        source_name = source.get("门店名称", source_store_id)
        target_name = target.get("门店名称", target_store_id)

        if source_store_id == target_store_id:
            return {"success": False, "message": "源门店和目标门店不能相同"}

        # 1. 转移所有数据
        transfer_result = self.transfer_all_store_data(
            source_store_id, target_store_id, operator,
            reason=f"门店合并：{source_name} → {target_name}"
        )

        # 2. 关闭源门店
        source_row = source.get("_row", 0)
        if source_row and delete_source:
            self.mgr.update_store(source_row, {"门店状态": "已关闭", "备注": f"已合并至{target_name}"})
            # 或者直接删除
            # self.mgr.delete_store(source_row, source_store_id)

        return {
            "success": True,
            "message": f"门店合并完成：\n{source_name} → {target_name}\n{transfer_result['message']}",
            "transferred": transfer_result["count"],
            "source_store": source_name,
            "target_store": target_name,
        }

    # ==================== 转移日志 ====================

    def _write_transfer_log(self, entries, operator, reason):
        """写入转移日志"""
        from config import TRANSFER_LOG_SHEET, TRANSFER_LOG_HEADERS

        for entry in entries:
            row = self.biz.engine.find_next_empty_row(TRANSFER_LOG_SHEET)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            from core.auto_num import AutoNumber
            transfer_id = AutoNumber(self.biz.engine).transfer_id()
            self.biz.engine.write_row(TRANSFER_LOG_SHEET, row, {
                "转移编号": transfer_id,
                "数据类型": entry.get("数据类型", ""),
                "数据编号": entry.get("数据编号", ""),
                "源门店编号": entry.get("源门店编号", ""),
                "目标门店编号": entry.get("目标门店编号", ""),
                "操作人": operator,
                "转移时间": now,
                "原因": reason,
            })

    def get_transfer_logs(self, limit=50):
        """获取数据转移日志"""
        from config import TRANSFER_LOG_SHEET
        logs = self.biz.engine.get_all_data(TRANSFER_LOG_SHEET)
        return logs[-limit:] if len(logs) > limit else logs
