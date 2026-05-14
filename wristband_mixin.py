"""
手环管理混合类
V2.16.1 - 手环CRUD + 绑定/解绑会员 + 通过读卡器值查找
"""
from datetime import date, datetime
from config import SHEETS, HEADERS, WRISTBAND_STATUSES


class WristbandMixin:
    """手环管理"""

    def _init_wristband_sheet(self):
        """确保手环管理 Sheet 和表头存在"""
        sheet_name = SHEETS["wristband"]
        if not self.engine.sheet_exists(sheet_name):
            # Sheet 不存在，创建并初始化表头
            ws = self.engine.wb.create_sheet(title=sheet_name)
            headers = HEADERS["wristband"]
            for i, h in enumerate(headers, 1):
                ws.cell(row=3, column=i, value=h)
            self.engine.apply_header_style(sheet_name, 3, len(headers))
            self.engine.save()
        else:
            # Sheet 存在但可能没有表头，检查并补充
            headers = self.engine.get_headers(sheet_name)
            if not headers:
                # 没有表头，说明是空 Sheet，初始化
                expected = HEADERS["wristband"]
                for i, h in enumerate(expected, 1):
                    self.engine.write_cell(sheet_name, 3, i, h)
                self.engine.apply_header_style(sheet_name, 3, len(expected))
                self.engine.save()

    # ── CRUD ──

    def add_wristband(self, data):
        """注册新手环

        data: {
            "读卡器写入值": "1234567890",  # 10位数字
            "自定义编号": "储物柜A01",
            "备注": "",
        }
        """
        self._init_wristband_sheet()
        sheet_name = SHEETS["wristband"]

        reader_val = str(data.get("读卡器写入值", "")).strip()
        custom_id = str(data.get("自定义编号", "")).strip()

        # 校验读卡器值
        if not reader_val or len(reader_val) != 10 or not reader_val.isdigit():
            return {"success": False, "message": "读卡器写入值必须为10位数字"}

        # 校验唯一性
        existing = self.get_all_wristbands()
        for w in existing:
            if w.get("读卡器写入值") == reader_val:
                return {"success": False, "message": f"读卡器写入值 {reader_val} 已存在"}

        band_id_str = self.autonum.band_id()
        row_num = self.engine.find_next_empty_row(sheet_name)
        now = date.today()

        row_data = {
            "手环编号": band_id_str,
            "读卡器写入值": reader_val,
            "自定义编号": custom_id,
            "绑定会员编号": "",
            "绑定会员姓名": "",
            "绑定时间": "",
            "绑定状态": "未绑定",
            "注册时间": now,
            "备注": data.get("备注", ""),
        }
        for key, val in row_data.items():
            col = self.engine.get_header_col(sheet_name, key)
            if col:
                self.engine.write_cell(sheet_name, row_num, col, val)

        return {"success": True, "message": "手环注册成功", "band_id": band_id_str}

    def get_all_wristbands(self):
        """获取所有手环"""
        self._init_wristband_sheet()
        return self.engine.get_all_data(SHEETS["wristband"])

    def get_wristband(self, band_id):
        """根据手环编号获取单个手环"""
        bands = self.get_all_wristbands()
        for b in bands:
            if b.get("手环编号") == band_id:
                return b
        return None

    def find_by_reader_value(self, reader_value):
        """通过读卡器写入值查找手环"""
        bands = self.get_all_wristbands()
        for b in bands:
            if b.get("读卡器写入值") == str(reader_value).strip():
                return b
        return None

    def update_wristband(self, row_num, data):
        """更新手环信息"""
        sheet_name = SHEETS["wristband"]
        for key, value in data.items():
            if key in HEADERS["wristband"]:
                col = self.engine.get_header_col(sheet_name, key)
                if col:
                    self.engine.write_cell(sheet_name, row_num, col, value)
        return {"success": True, "message": "手环已更新"}

    def delete_wristband(self, row_num):
        """删除手环"""
        self.engine.delete_row(SHEETS["wristband"], row_num)
        return {"success": True, "message": "手环已删除"}

    # ── 绑定/解绑 ──

    def bind_wristband(self, band_id, member_id, member_name):
        """绑定手环到会员"""
        sheet_name = SHEETS["wristband"]
        bands = self.get_all_wristbands()

        for b in bands:
            if b.get("手环编号") == band_id:
                # 更新手环表
                for key, val in [
                    ("绑定会员编号", member_id),
                    ("绑定会员姓名", member_name),
                    ("绑定时间", date.today()),
                    ("绑定状态", "已绑定"),
                ]:
                    col = self.engine.get_header_col(sheet_name, key)
                    if col:
                        self.engine.write_cell(sheet_name, b["_row"], col, val)

                # 更新会员表手环编号
                member = self.get_member(member_id)
                if member:
                    col = self.engine.get_header_col(SHEETS["member"], "手环编号")
                    if col:
                        self.engine.write_cell(SHEETS["member"], member["_row"], col, band_id)
                    self._member_cache = None

                return {"success": True, "message": f"手环 {band_id} 已绑定给 {member_name}"}

        return {"success": False, "message": f"未找到手环 {band_id}"}

    def unbind_wristband(self, band_id, member_id=None):
        """解绑手环"""
        sheet_name = SHEETS["wristband"]
        bands = self.get_all_wristbands()

        for b in bands:
            if b.get("手环编号") == band_id:
                # 清空手环表绑定信息
                for key in ["绑定会员编号", "绑定会员姓名", "绑定时间"]:
                    col = self.engine.get_header_col(sheet_name, key)
                    if col:
                        self.engine.write_cell(sheet_name, b["_row"], col, "")
                col = self.engine.get_header_col(sheet_name, "绑定状态")
                if col:
                    self.engine.write_cell(sheet_name, b["_row"], col, "未绑定")

                # 清空会员表手环编号
                if member_id:
                    member = self.get_member(member_id)
                    if member:
                        col = self.engine.get_header_col(SHEETS["member"], "手环编号")
                        if col:
                            self.engine.write_cell(SHEETS["member"], member["_row"], col, "")
                        self._member_cache = None

                return {"success": True, "message": f"手环 {band_id} 已解绑"}

        return {"success": False, "message": f"未找到手环 {band_id}"}

    def get_member_wristband(self, member_id):
        """查询会员绑定的手环"""
        member = self.get_member(member_id)
        if not member:
            return None
        band_id = member.get("手环编号", "")
        if not band_id:
            return None
        return self.get_wristband(band_id)

    def get_unbound_wristbands(self):
        """获取所有未绑定的手环"""
        bands = self.get_all_wristbands()
        return [b for b in bands if b.get("绑定状态") == "未绑定" or not b.get("绑定状态")]
