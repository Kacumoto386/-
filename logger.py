"""操作日志模块"""
from datetime import datetime
from core.excel_engine import ExcelEngine


class OperationLogger:
    """记录操作日志到Excel的'操作日志'Sheet"""

    def __init__(self, engine: ExcelEngine, sheet_name="操作日志"):
        self.engine = engine
        self.sheet_name = sheet_name
        self._init_sheet()

    def _init_sheet(self):
        """初始化日志Sheet的标题行"""
        ws = self.engine.get_sheet(self.sheet_name)
        # 先解除所有合并单元格，防止 MergedCell 写入失败
        if ws.merged_cells.ranges:
            for merge_range in list(ws.merged_cells.ranges):
                ws.unmerge_cells(str(merge_range))
        # 检查第3行是否已有表头（兼容第一行为大标题的格式）
        if ws.cell(row=3, column=1).value != "日志编号":
            # 如果第1行有数据但不是表头，保留；我们把表头写在第3行
            headers = [
                "日志编号", "操作时间", "操作人", "操作类型",
                "操作模块", "操作详情", "变更前", "变更后",
            ]
            for i, h in enumerate(headers, 1):
                ws.cell(row=3, column=i).value = h
            # 设置列宽
            col_widths = {1: 18, 2: 20, 3: 12, 4: 10, 5: 10, 6: 40, 7: 30, 8: 30}
            for col, width in col_widths.items():
                ws.column_dimensions[chr(64 + col)].width = width

    def _get_next_id(self):
        """生成日志编号：L + 年月日 + 4位序号"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"L{today}"
        ws = self.engine.get_sheet(self.sheet_name)
        max_row = ws.max_row
        for row in range(max_row, 1, -1):
            val = ws.cell(row=row, column=1).value
            if val and str(val).startswith(prefix):
                seq = int(str(val)[-4:]) + 1
                return f"{prefix}{seq:04d}"
        return f"{prefix}0001"

    def log(self, op_type, module, detail, before="", after="", operator="系统"):
        """记录一条操作日志"""
        log_id = self._get_next_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws = self.engine.get_sheet(self.sheet_name)
        row = ws.max_row + 1

        ws.cell(row=row, column=1).value = log_id
        ws.cell(row=row, column=2).value = now
        ws.cell(row=row, column=3).value = operator
        ws.cell(row=row, column=4).value = op_type
        ws.cell(row=row, column=5).value = module
        ws.cell(row=row, column=6).value = detail
        ws.cell(row=row, column=7).value = str(before) if before else ""
        ws.cell(row=row, column=8).value = str(after) if after else ""
        self.engine.save()

    def get_all_logs(self):
        """获取所有日志记录"""
        ws = self.engine.get_sheet(self.sheet_name)
        logs = []
        for row in range(2, ws.max_row + 1):
            log_id = ws.cell(row=row, column=1).value
            if log_id is None:
                continue
            logs.append({
                "日志编号": str(log_id),
                "操作时间": ws.cell(row=row, column=2).value,
                "操作人": ws.cell(row=row, column=3).value,
                "操作类型": ws.cell(row=row, column=4).value,
                "操作模块": ws.cell(row=row, column=5).value,
                "操作描述": ws.cell(row=row, column=6).value,
                "详细内容": ws.cell(row=row, column=7).value,
            })
        return logs[::-1]  # 最新在前
