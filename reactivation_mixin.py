# -*- coding: utf-8 -*-
"""
产品重新激活 Mixin - V2.14.1
支持售卡记录、售课记录、课程包的过期产品重新激活
售课重新激活增强：使用 get_header_col 定位"售课状态"列，新增 _ensure_status_column 辅助方法
"""
from datetime import date, datetime, timedelta
from config import SHEETS


class ReactivationMixin:

    def _ensure_status_column(self, sheet, col_name):
        """确保指定 Sheet 存在某列，不存在则在尾部追加"""
        header_list = self.engine.get_headers(sheet)
        if col_name not in header_list:
            ws = self.engine.get_sheet(sheet)
            new_col = len(header_list) + 1
            ws.cell(row=3, column=new_col).value = col_name
            self.engine.apply_header_style(sheet, 3, new_col)
            self.engine.save()

    """重新激活相关方法"""

    def reactivate_membership(self, row_num, update_data):
        """重新激活会籍卡（售卡记录）
        
        Args:
            row_num: 会籍卡记录行号
            update_data: dict，包含新的状态、有效期等
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            sheet = SHEETS["membership"]

            # 更新状态
            status_col = self.engine.get_header_col(sheet, "状态")
            self.engine.write_cell(sheet, row_num, status_col, update_data.get("状态", "有效"))

            # 更新有效期起
            if "有效期起" in update_data:
                col = self.engine.get_header_col(sheet, "有效期起")
                if col:
                    self.engine.write_cell(sheet, row_num, col, update_data["有效期起"])

            # 更新有效期止
            if "有效期止" in update_data:
                col = self.engine.get_header_col(sheet, "有效期止")
                if col:
                    self.engine.write_cell(sheet, row_num, col, update_data["有效期止"])

            # 更新剩余次数（次卡）
            if "剩余次数" in update_data:
                col = self.engine.get_header_col(sheet, "剩余次数")
                if col:
                    self.engine.write_cell(sheet, row_num, col, update_data["剩余次数"])
                col2 = self.engine.get_header_col(sheet, "已消耗次数")
                if col2:
                    self.engine.write_cell(sheet, row_num, col2, update_data.get("已消耗次数", 0))

            # 更新余额（现金卡）
            if "余额" in update_data:
                col = self.engine.get_header_col(sheet, "余额")
                if col:
                    self.engine.write_cell(sheet, row_num, col, update_data["余额"])
                col2 = self.engine.get_header_col(sheet, "已消费金额")
                if col2:
                    self.engine.write_cell(sheet, row_num, col2, update_data.get("已消费金额", 0))

            # 获取会员信息，同步更新会员状态
            card = None
            for c in self.get_all_memberships():
                if c.get("_row") == row_num:
                    card = c
                    break

            if card:
                member_id = card.get("会员编号", "")
                if member_id:
                    member = self.get_member(member_id)
                    if member:
                        # 更新会员状态
                        self.update_member(member["_row"], {"会员状态": "有效"})
                        # 如果是期限卡，更新到期日期
                        if card.get("卡类型") == "期限卡" and update_data.get("有效期止"):
                            self.update_member(member["_row"], {
                                "到期日期": update_data["有效期止"],
                            })

            self.engine.save()
            return {"success": True, "message": f"会籍卡重新激活成功"}

        except Exception as e:
            return {"success": False, "error": f"重新激活失败: {str(e)}"}

    def reactivate_sale(self, row_num, new_expiry=None):
        """重新激活售课记录（将已过期/无效的售课变为有效）V2.14.1
        
        1. 重置售课记录的"有效期截止日"（延长）
        2. 更新售课记录的"售课状态"为"有效"
        3. 重新激活关联的已过期/已用完课程包
        """
        try:
            sheet = SHEETS["sale"]
            sale = None
            for s in self.engine.get_all_data(sheet):
                if s.get("_row") == row_num:
                    sale = s
                    break

            if not sale:
                return {"success": False, "error": "售课记录不存在"}

            sale_id = sale.get("售课编号", "")

            # 1. 重置售课记录的到期日期
            if new_expiry:
                col = self.engine.get_header_col(sheet, "有效期截止日")
                if col:
                    self.engine.write_cell(sheet, row_num, col, new_expiry)
                # 同时重置课时有效期(天) — 从旧到期日到今天重新计算剩余天数
                old_expiry = self._safe_to_str(sale.get("有效期截止日", ""))
                if old_expiry and old_expiry != "None":
                    try:
                        old_dt = datetime.strptime(str(old_expiry)[:10], "%Y-%m-%d")
                        new_dt = datetime.strptime(str(new_expiry)[:10], "%Y-%m-%d")
                        new_days = max((new_dt - old_dt).days, 30)
                        col_days = self.engine.get_header_col(sheet, "课时有效期(天)")
                        if col_days:
                            self.engine.write_cell(sheet, row_num, col_days, new_days)
                    except (ValueError, TypeError):
                        pass

            # 2. 更新售课状态为"有效"
            self._ensure_status_column(sheet, "售课状态")
            status_col = self.engine.get_header_col(sheet, "售课状态")
            if status_col:
                self.engine.write_cell(sheet, row_num, status_col, "有效")

            # 3. 重新激活关联的课程包
            packages = self.get_all_packages()
            matched = [p for p in packages if p.get("售课编号") == sale_id]
            activated = 0

            for pkg in matched:
                if pkg.get("状态") in ("已过期", "已用完"):
                    pkg_row = pkg.get("_row")
                    # 重置状态
                    status_col = self.engine.get_header_col(SHEETS["lesson_package"], "状态")
                    self.engine.write_cell(SHEETS["lesson_package"], pkg_row, status_col, "有效")

                    # 重置有效期
                    if new_expiry:
                        valid_to_col = self.engine.get_header_col(SHEETS["lesson_package"], "有效期止")
                        if valid_to_col:
                            self.engine.write_cell(SHEETS["lesson_package"], pkg_row, valid_to_col, new_expiry)

                    # 重置剩余课时（如果已用完）
                    remaining = self._safe_float(pkg.get("剩余课时", 0))
                    if remaining <= 0:
                        total = self._safe_float(pkg.get("总课时", 0))
                        if total <= 0:
                            total = self._safe_float(pkg.get("购买课时", 0))
                        if total > 0:
                            remain_col = self.engine.get_header_col(SHEETS["lesson_package"], "剩余课时")
                            if remain_col:
                                self.engine.write_cell(SHEETS["lesson_package"], pkg_row, remain_col, total)
                            consumed_col = self.engine.get_header_col(SHEETS["lesson_package"], "已消耗课时")
                            if consumed_col:
                                self.engine.write_cell(SHEETS["lesson_package"], pkg_row, consumed_col, 0)

                    activated += 1

            # 保存所有更改
            self.engine.save()

            msg = f"售课记录已重新激活（延长有效期至 {new_expiry}）"
            if activated > 0:
                msg += f"，已重置 {activated} 个关联课程包"
            return {"success": True, "message": msg}

        except Exception as e:
            return {"success": False, "error": f"重新激活失败: {str(e)}"}

    def reactivate_package(self, row_num):
        """重新激活课程包（将已过期/已用完的课程包重新设为有效）"""
        try:
            pkg = None
            for p in self.get_all_packages():
                if p.get("_row") == row_num:
                    pkg = p
                    break

            if not pkg:
                return {"success": False, "error": "课程包不存在"}

            status = pkg.get("状态", "")
            if status not in ("已过期", "已用完"):
                return {"success": True, "message": "该课程包当前状态无需重新激活"}

            # 重置状态
            status_col = self.engine.get_header_col(SHEETS["lesson_package"], "状态")
            self.engine.write_cell(SHEETS["lesson_package"], row_num, status_col, "有效")

            # 重置剩余课时（如果已用完）
            if status == "已用完":
                remain_col = self.engine.get_header_col(SHEETS["lesson_package"], "剩余课时")
                total_col = self.engine.get_header_col(SHEETS["lesson_package"], "总课时")
                if remain_col and total_col:
                    total = int(float(str(pkg.get("总课时", 0) or 0)))
                    self.engine.write_cell(SHEETS["lesson_package"], row_num, remain_col, total)
                    consumed_col = self.engine.get_header_col(SHEETS["lesson_package"], "已消耗课时")
                    if consumed_col:
                        self.engine.write_cell(SHEETS["lesson_package"], row_num, consumed_col, 0)

            # 重置有效期（延长一年）
            valid_to_col = self.engine.get_header_col(SHEETS["lesson_package"], "有效期止")
            if valid_to_col:
                new_valid_to = date.today() + timedelta(days=365)
                self.engine.write_cell(SHEETS["lesson_package"], row_num, valid_to_col, new_valid_to.strftime("%Y-%m-%d"))

            # 保存更改
            self.engine.save()

            return {"success": True, "message": "课程包重新激活成功"}

        except Exception as e:
            return {"success": False, "error": f"重新激活失败: {str(e)}"}
