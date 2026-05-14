# -*- coding: utf-8 -*-
"""
会员分析引擎 v2.8.4 — 升级版会员画像
新增：消费画像/教练偏好/出勤日历/体测趋势图/事件时间线/多因子流失评分
"""
import datetime
from collections import defaultdict, Counter
import math


class MemberAnalysisEngine:
    """会员分析引擎，依赖 BusinessLayer 提供原始数据"""

    def __init__(self, biz):
        self.biz = biz
        self.today = datetime.date.today()

    # ============================================================
    # 1. 完整画像（7Tab 统一入口）
    # ============================================================

    def get_detailed_profile(self, member_id):
        """获取升级版完整画像 —— 供新7Tab UI 使用"""
        members = self.biz.get_all_members()
        member = None
        for m in members:
            if m.get("会员编号") == member_id:
                member = m
                break
        if not member:
            return None

        classes = self._filter(member_id, self.biz.get_all_class_records(), "会员编号")
        sales = self._filter(member_id, self.biz.get_all_sales(), "会员编号")
        recharges = self._filter(member_id, self.biz.get_all_recharges(), "会员编号")
        measurements = self._filter(member_id, self.biz.get_all_measurements(), "会员编号")
        product_sales = self._filter(member_id, self.biz.get_all_product_sales(), "会员编号")
        bookings = self._filter(member_id, self.biz.get_all_bookings(), "会员编号")
        packages = self._filter(member_id, self.biz.get_all_lesson_packages(), "会员编号")

        return {
            "basic": self._basic_info(member),
            "consumption": self._consumption_profile(member, sales, recharges, product_sales),
            "course_pref": self._course_preference(classes),
            "coach_pref": self._coach_preference(classes),
            "attendance": self._attendance_summary(classes),
            "active_calendar": self._active_calendar(classes, days=90),
            "measurement": self._measurement_trend(measurements),
            "churn_risk": self._calc_churn_score(member, classes),
            "timeline": self._build_timeline(member, sales, classes, recharges,
                                             measurements, product_sales, bookings),
            "payment_pref": self._payment_preference(sales, recharges, product_sales),
            "consumption_trend": self._consumption_trend(sales, recharges, product_sales),
            "consumption_rating": self._consumption_rating(sales, recharges, product_sales),
            "peak_hours": self._peak_hours(classes),
        }

    # ============================================================
    # 2. 个人信息
    # ============================================================

    def _basic_info(self, member):
        return {
            "会员编号": member.get("会员编号"),
            "姓名": member.get("姓名"),
            "性别": member.get("性别"),
            "手机号": member.get("手机号"),
            "出生日期": self._fmt(member.get("出生日期")),
            "年龄": member.get("年龄"),
            "身高(cm)": member.get("身高(cm)"),
            "体重(kg)": member.get("体重(kg)"),
            "体脂率(%)": member.get("体脂率(%)"),
            "会员等级": member.get("会员等级"),
            "会员状态": member.get("会员状态"),
            "开卡日期": self._fmt(member.get("开卡日期")),
            "到期日期": self._fmt(member.get("到期日期")),
            "累计签到天数": member.get("累计签到天数", 0) or 0,
            "最近签到日期": self._fmt(member.get("最近签到日期")),
            "客户来源": member.get("客户来源", ""),
            "紧急联系人": member.get("紧急联系人", ""),
            "联系电话": member.get("联系电话", ""),
            "身份证号": member.get("身份证号", ""),
            "备注": member.get("备注", ""),
            "门店编号": member.get("门店编号", ""),
        }

    # ============================================================
    # 3. 消费画像
    # ============================================================

    def _consumption_profile(self, member, sales, recharges, product_sales):
        """消费汇总"""
        total_sale = sum(float(s.get("实收金额", 0) or 0) for s in sales)
        total_recharge = sum(float(r.get("实付金额", 0) or 0) for r in recharges)
        total_retail = sum(float(p.get("总价", 0) or 0) for p in product_sales)
        total_spent = total_sale + total_recharge + total_retail

        return {
            "总消费金额": round(total_spent, 2),
            "总购课金额": round(total_sale, 2),
            "总充值金额": round(total_recharge, 2),
            "总零售金额": round(total_retail, 2),
            "总购课时": self._safe_int(member.get("总购课时", 0)),
            "已消耗课时": self._safe_int(member.get("已消耗课时", 0)),
            "剩余课时": self._safe_int(member.get("剩余课时", 0)),
            "充值总额": self._safe_float(member.get("充值总额", 0)),
            "剩余金额": self._safe_float(member.get("剩余金额", 0)),
            "已消耗金额": self._safe_float(member.get("已消耗金额", 0)),
            "售课笔数": len(sales),
            "充值笔数": len(recharges),
            "零售笔数": len(product_sales),
        }

    def _consumption_rating(self, sales, recharges, product_sales):
        """消费能力评级"""
        total = sum(float(s.get("实收金额", 0) or 0) for s in sales)
        total += sum(float(r.get("实付金额", 0) or 0) for r in recharges)
        total += sum(float(p.get("总价", 0) or 0) for p in product_sales)

        if total >= 50000:
            return {"level": "VIP", "label": "👑 钻石VIP", "threshold": "≥¥50,000"}
        elif total >= 20000:
            return {"level": "gold", "label": "🥇 金卡", "threshold": "≥¥20,000"}
        elif total >= 10000:
            return {"level": "silver", "label": "🥈 银卡", "threshold": "≥¥10,000"}
        elif total >= 3000:
            return {"level": "bronze", "label": "🥉 铜卡", "threshold": "≥¥3,000"}
        else:
            return {"level": "regular", "label": "⚪ 普通", "threshold": "<¥3,000"}

    def _consumption_trend(self, sales, recharges, product_sales, months=12):
        """月度消费趋势"""
        from collections import defaultdict
        monthly = defaultdict(float)

        cutoff = self.today - datetime.timedelta(days=months * 31)

        for s in sales:
            d = self._to_date(s.get("售课日期"))
            if d and d >= cutoff:
                key = d.strftime("%Y-%m")
                monthly[key] += float(s.get("实收金额", 0) or 0)

        for r in recharges:
            d = self._to_date(r.get("充值日期"))
            if d and d >= cutoff:
                key = d.strftime("%Y-%m")
                monthly[key] += float(r.get("实付金额", 0) or 0)

        for p in product_sales:
            d = self._to_date(p.get("零售日期"))
            if d and d >= cutoff:
                key = d.strftime("%Y-%m")
                monthly[key] += float(p.get("总价", 0) or 0)

        # 生成完整月份序列
        result = []
        for i in range(months - 1, -1, -1):
            dt = self.today.replace(day=1) - datetime.timedelta(days=i * 31)
            key = dt.strftime("%Y-%m")
            result.append({"month": key, "amount": round(monthly.get(key, 0), 2)})

        return result

    def _payment_preference(self, sales, recharges, product_sales):
        """付款方式偏好统计"""
        counter = Counter()
        for s in sales:
            pm = s.get("付款方式", "").strip()
            if pm:
                counter[pm] += 1
        for r in recharges:
            pm = r.get("付款方式", "").strip()
            if pm:
                counter[pm] += 1
        for p in product_sales:
            pm = p.get("支付方式", "").strip()
            if pm:
                counter[pm] += 1
        total = sum(counter.values()) or 1
        return [{"method": k, "count": v, "ratio": round(v / total * 100, 1)}
                for k, v in counter.most_common()]

    # ============================================================
    # 4. 课程偏好 + 教练偏好
    # ============================================================

    def _course_preference(self, classes):
        """课程偏好 — 按课程类型统计"""
        counter = Counter()
        for c in classes:
            ct = c.get("课程类型") or c.get("课程名称") or "未知"
            counter[ct] += 1
        total = sum(counter.values()) or 1
        return [
            {"type": k, "count": v, "ratio": round(v / total * 100, 1)}
            for k, v in counter.most_common()
        ]

    def _coach_preference(self, classes):
        """教练偏好 — 按教练统计"""
        counter = Counter()
        for c in classes:
            coach = c.get("教练姓名") or c.get("授课教练") or "未知"
            counter[coach] += 1
        total = sum(counter.values()) or 1
        return [
            {"coach": k, "count": v, "ratio": round(v / total * 100, 1)}
            for k, v in counter.most_common()
        ]

    # ============================================================
    # 5. 出勤分析 + 出勤日历
    # ============================================================

    def _attendance_summary(self, classes):
        """出勤汇总"""
        total = len(classes)
        if total == 0:
            return {
                "总上课次数": 0, "月均上课": 0, "周均上课": 0,
                "最近上课": "无", "连续未上课天数": 0,
                "出勤率": 0, "日均上课": 0,
            }

        dates = []
        for c in classes:
            d = self._to_date(c.get("上课日期"))
            if d:
                dates.append(d)
        dates.sort(reverse=True)

        if not dates:
            return {"总上课次数": total, "月均上课": 0, "周均上课": 0,
                    "最近上课": "无", "连续未上课天数": 0,
                    "出勤率": 0, "日均上课": 0}

        last_date = dates[0]
        days_since_last = (self.today - last_date).days

        if len(dates) >= 2:
            span = (dates[0] - dates[-1]).days or 1
            monthly = round(total / span * 30, 1)
            weekly = round(total / span * 7, 1)
            daily = round(total / span, 2)
        else:
            monthly = total
            weekly = total
            daily = total

        # 出勤率 = 有课天数 / 最近30天
        active_days_30 = len(set(
            self._to_date(c.get("上课日期"))
            for c in classes
            if self._to_date(c.get("上课日期")) and
            (self.today - self._to_date(c.get("上课日期"))).days <= 30
        ))
        attendance_rate = round(active_days_30 / 30 * 100, 1)

        return {
            "总上课次数": total,
            "月均上课": monthly,
            "周均上课": weekly,
            "日均上课": daily,
            "最近上课": str(last_date),
            "连续未上课天数": days_since_last,
            "出勤率": attendance_rate,
            "活跃天数(近30天)": active_days_30,
        }

    def _active_calendar(self, classes, days=90):
        """出勤日历 — 返回近 N 天每日上课次数"""
        cutoff = self.today - datetime.timedelta(days=days)
        daily = Counter()
        for c in classes:
            d = self._to_date(c.get("上课日期"))
            if d and d >= cutoff:
                daily[str(d)] += 1
        result = []
        for i in range(days - 1, -1, -1):
            dt = self.today - datetime.timedelta(days=i)
            key = str(dt)
            result.append({"date": key, "count": daily.get(key, 0),
                           "weekday": dt.weekday()})
        return result

    # ============================================================
    # 6. 体测趋势
    # ============================================================

    def _measurement_trend(self, measurements):
        """体测趋势 — 按时间排序"""
        sorted_m = sorted(
            measurements,
            key=lambda x: str(x.get("体测日期", "")),
        )
        return [
            {
                "date": str(m.get("体测日期", ""))[:10] if m.get("体测日期") else "",
                "身高(cm)": self._safe_float(m.get("身高(cm)")),
                "体重(kg)": self._safe_float(m.get("体重(kg)")),
                "体脂率(%)": self._safe_float(m.get("体脂率(%)")),
                "BMI": self._safe_float(m.get("BMI")),
                "肌肉量(kg)": self._safe_float(m.get("肌肉量(kg)")),
                "基础代谢(kcal)": self._safe_float(m.get("基础代谢(kcal)")),
                "体年龄": self._safe_int(m.get("体年龄")),
            }
            for m in sorted_m
        ]

    # ============================================================
    # 7. 流失评估（多因子评分版）
    # ============================================================

    def _calc_churn_score(self, member, classes):
        """多因子加权流失评分 (0-100)，越高越危险"""
        # 因子1: 连续未上课天数 (40%)
        dates = sorted(set(
            self._to_date(c.get("上课日期"))
            for c in classes
            if self._to_date(c.get("上课日期"))
        ), reverse=True)

        days_since_last = 999
        if dates:
            days_since_last = (self.today - dates[0]).days

        if days_since_last >= 90:
            score1 = 100
        elif days_since_last >= 60:
            score1 = 80 + (days_since_last - 60) / 30 * 20
        elif days_since_last >= 30:
            score1 = 50 + (days_since_last - 30) / 30 * 30
        elif days_since_last >= 14:
            score1 = 20 + (days_since_last - 14) / 16 * 30
        elif days_since_last >= 7:
            score1 = 10 + (days_since_last - 7) / 7 * 10
        else:
            score1 = 0

        # 因子2: 剩余课时 (20%) — 课时越少越危险
        remaining = self._safe_int(member.get("剩余课时", 0))
        if remaining <= 0:
            score2 = 100
        elif remaining <= 3:
            score2 = 70
        elif remaining <= 10:
            score2 = 40 + (10 - remaining) / 7 * 30
        elif remaining <= 20:
            score2 = 20 + (20 - remaining) / 10 * 20
        else:
            score2 = 10

        # 因子3: 会员即将到期 (20%)
        expire = self._to_date(member.get("到期日期"))
        if not expire:
            score3 = 20  # 无到期日 = 中等风险
        else:
            days_to_expire = (expire - self.today).days
            if days_to_expire <= 0:
                score3 = 100
            elif days_to_expire <= 7:
                score3 = 80
            elif days_to_expire <= 30:
                score3 = 60 + (30 - days_to_expire) / 23 * 20
            elif days_to_expire <= 90:
                score3 = 30 + (90 - days_to_expire) / 60 * 30
            else:
                score3 = 10

        # 因子4: 到店频率下降趋势 (20%)
        if len(dates) >= 4:
            recent_30 = sum(1 for d in dates if (self.today - d).days <= 30)
            prev_30 = sum(1 for d in dates if 30 < (self.today - d).days <= 60)
            if prev_30 > 0 and recent_30 < prev_30 * 0.5:
                score4 = 70 + (1 - recent_30 / max(prev_30, 1)) * 30
            elif prev_30 > 0 and recent_30 < prev_30:
                score4 = 40
            else:
                score4 = 10
        else:
            score4 = 30 if len(dates) > 0 else 80

        # 加权总分
        total_score = score1 * 0.40 + score2 * 0.20 + score3 * 0.20 + score4 * 0.20

        # 等级判定
        if total_score >= 80:
            level = "extreme"
            level_label = "🔴 极高风险"
        elif total_score >= 60:
            level = "high"
            level_label = "🟠 高风险"
        elif total_score >= 40:
            level = "medium"
            level_label = "🟡 中风险"
        elif total_score >= 20:
            level = "low"
            level_label = "🟢 低风险"
        else:
            level = "normal"
            level_label = "✅ 正常"

        # 叠加标签
        tags = []
        if remaining <= 3:
            tags.append("课时不足")
        if days_since_last > 14 and remaining > 3:
            tags.append("低频到店")
        if expire and 0 <= (expire - self.today).days <= 30:
            tags.append("即将到期")
        if days_since_last > 60:
            tags.append("长期未到")

        # 因子详情，用于UI展示
        factors = {
            "连续未上课得分": round(score1, 1),
            "课时不足得分": round(score2, 1),
            "到期临近得分": round(score3, 1),
            "频率下降得分": round(score4, 1),
        }

        return {
            "score": round(total_score, 1),
            "level": level,
            "level_label": level_label,
            "factors": factors,
            "tags": tags,
            "连续未上课天数": days_since_last,
            "剩余课时": remaining,
            "reason": self._churn_reason(level, days_since_last, remaining, tags),
            "suggestion": self._churn_suggestion(level, tags, days_since_last, remaining),
        }

    def _churn_reason(self, level, days_since, remaining, tags):
        """生成流失原因描述"""
        parts = []
        if days_since > 60:
            parts.append(f"已{days_since}天未上课")
        elif days_since > 30:
            parts.append(f"已{days_since}天未上课")

        if remaining <= 3:
            parts.append(f"仅剩{remaining}课时")

        if "即将到期" in tags:
            parts.append("会员即将到期")

        return "；".join(parts) if parts else "会员状态正常"

    def _churn_suggestion(self, level, tags, days_since, remaining):
        """根据风险因子组合生成定制挽回建议"""
        if level == "extreme":
            if "课时不足" in tags and "长期未到" in tags:
                return "📞 建议立即电话回访，了解会员近况，赠送体验课或限时课时包促销"
            elif "即将到期" in tags:
                return "📞 建议主动联系续费，推出老会员续费优惠方案"
            else:
                return "📞 紧急回访，安排教练一对一沟通，了解流失原因"

        elif level == "high":
            if "课时不足" in tags:
                return "💡 发送课时包优惠信息，推荐购买小额课程包继续锻炼"
            elif "低频到店" in tags:
                return "💡 推荐新课程或活动，增加到店频率；可发送关怀消息"
            else:
                return "💡 发送健身提醒和课程更新，保持会员互动"

        elif level == "medium":
            if "即将到期" in tags:
                return "📋 提前推送续费提醒，推荐续费优惠方案"
            else:
                return "📋 发送健身小贴士，推荐感兴趣的课程活动"

        elif level == "low":
            return "👍 发送提醒消息保持互动，观察后续到店情况"

        else:
            return "🎉 会员状态良好，继续保持规律锻炼"

    # ============================================================
    # 8. 事件时间线
    # ============================================================

    def _build_timeline(self, member, sales, classes, recharges,
                        measurements, product_sales, bookings):
        """构建会员所有事件的时间线"""
        events = []

        # 开卡事件
        open_date = self._to_date(member.get("开卡日期"))
        if open_date:
            events.append({
                "date": str(open_date),
                "type": "open",
                "icon": "📋",
                "title": "开卡入会",
                "detail": f"会员等级: {member.get('会员等级', '')}",
                "amount": None,
            })

        # 售课事件
        for s in sales:
            d = self._to_date(s.get("售课日期"))
            if d:
                events.append({
                    "date": str(d),
                    "type": "sale",
                    "icon": "💰",
                    "title": "购买课程",
                    "detail": f"{s.get('课程名称', '')} × {s.get('购买课时数', '')}节",
                    "amount": self._safe_float(s.get("实收金额", 0)),
                })

        # 上课事件
        for c in classes:
            d = self._to_date(c.get("上课日期"))
            if d:
                events.append({
                    "date": str(d),
                    "type": "class",
                    "icon": "🏋️",
                    "title": "上体育课",
                    "detail": f"{c.get('课程名称', '')} - {c.get('教练姓名', '')}",
                    "amount": None,
                })

        # 充值事件
        for r in recharges:
            d = self._to_date(r.get("充值日期"))
            if d:
                events.append({
                    "date": str(d),
                    "type": "recharge",
                    "icon": "💳",
                    "title": "会员充值",
                    "detail": r.get("充值类型", ""),
                    "amount": self._safe_float(r.get("实付金额", 0)),
                })

        # 体测事件
        for m in measurements:
            d = self._to_date(m.get("体测日期"))
            if d:
                events.append({
                    "date": str(d),
                    "type": "measurement",
                    "icon": "📏",
                    "title": "体测记录",
                    "detail": f"体重:{m.get('体重(kg)', '')}kg 体脂:{m.get('体脂率(%)', '')}%",
                    "amount": None,
                })

        # 零售事件
        for p in product_sales:
            d = self._to_date(p.get("零售日期"))
            if d:
                events.append({
                    "date": str(d),
                    "type": "product",
                    "icon": "🛒",
                    "title": "购买商品",
                    "detail": f"{p.get('商品名称', '')} × {p.get('数量', '')}",
                    "amount": self._safe_float(p.get("总价", 0)),
                })

        # 预约事件
        for b in bookings:
            d = self._to_date(b.get("预约日期"))
            if d:
                events.append({
                    "date": str(d),
                    "type": "booking",
                    "icon": "📅",
                    "title": "课程预约",
                    "detail": f"{b.get('课程名称', '')} - {b.get('预约状态', '')}",
                    "amount": None,
                })

        # 按日期排序（倒序）
        events.sort(key=lambda e: e["date"], reverse=True)
        return events

    # ============================================================
    # 9. 热门时段分析
    # ============================================================

    def _peak_hours(self, classes):
        """热门时段分析"""
        time_counter = Counter()
        for c in classes:
            t = c.get("上课时间", "").strip()
            if t and ":" in t:
                hour = t.split(":")[0]
                time_counter[f"{hour}:00"] += 1
        return time_counter.most_common()

    # ============================================================
    # 10. 原有兼容方法（供流失预警看板等使用）
    # ============================================================

    def get_member_profile(self, member_id):
        """兼容旧版 —— 返回精简版画像"""
        profile = self.get_detailed_profile(member_id)
        if not profile:
            return None
        return {
            "basic": profile["basic"],
            "finance": profile["consumption"],
            "class_trend": self._class_trend_from_calendar(profile["active_calendar"]),
            "course_preference": profile["course_pref"],
            "measurement_trend": profile["measurement"],
            "attendance": profile["attendance"],
            "churn_risk": profile["churn_risk"],
            "peak_hours": profile["peak_hours"],
        }

    def _class_trend_from_calendar(self, calendar):
        """从日历数据还原上课趋势（兼容旧版）"""
        from collections import Counter
        daily = Counter()
        for d in calendar:
            if d["count"] > 0:
                daily[d["date"]] = d["count"]
        sorted_dates = sorted(daily.keys())
        return [{"date": d, "count": daily[d]} for d in sorted_dates]

    def get_churn_warnings(self):
        """获取所有会员的流失预警列表（兼容旧版，使用新版评分）"""
        members = self.biz.get_all_members()
        all_classes = self.biz.get_all_class_records()

        warnings = []
        for m in members:
            mid = m.get("会员编号")
            if not mid:
                continue
            member_classes = self._filter(mid, all_classes, "会员编号")
            risk = self._calc_churn_score(m, member_classes)
            if risk["level"] != "normal":
                warnings.append({
                    "会员编号": mid,
                    "姓名": m.get("姓名"),
                    "手机号": m.get("手机号"),
                    "会员等级": m.get("会员等级"),
                    "剩余课时": m.get("剩余课时", 0) or 0,
                    **risk,
                })

        level_order = {"extreme": 0, "high": 1, "medium": 2, "low": 3, "normal": 4}
        warnings.sort(key=lambda w: level_order.get(w["level"], 99))
        return warnings

    def get_course_popularity(self, days=30):
        """热门课程排行"""
        cutoff = self.today - datetime.timedelta(days=days)
        counter = Counter()
        for c in self.biz.get_all_class_records():
            d = self._to_date(c.get("上课日期"))
            if not d or d < cutoff:
                continue
            name = c.get("课程名称", "未知")
            counter[name] += 1
        return counter.most_common()

    def get_peak_hours(self, days=30):
        """热门时段分析（兼容旧版，所有会员）"""
        classes = self.biz.get_all_class_records()
        cutoff = self.today - datetime.timedelta(days=days)
        time_counter = Counter()
        for c in classes:
            d = self._to_date(c.get("上课日期"))
            if not d or d < cutoff:
                continue
            t = c.get("上课时间", "").strip()
            if t and ":" in t:
                hour = t.split(":")[0]
                time_counter[f"{hour}:00"] += 1
        return time_counter.most_common()

    # ============================================================
    # 辅助方法
    # ============================================================

    def _filter(self, value, records, key):
        return [r for r in records if r.get(key) == value]

    def _fmt(self, val):
        if isinstance(val, datetime.datetime):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, datetime.date):
            return val.strftime("%Y-%m-%d")
        return str(val) if val else ""

    def _to_date(self, val):
        if val is None:
            return None
        if isinstance(val, datetime.datetime):
            return val.date()
        if isinstance(val, datetime.date):
            return val
        if isinstance(val, str):
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
                try:
                    return datetime.datetime.strptime(val, fmt).date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _safe_int(val, default=0):
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_float(val, default=0.0):
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
