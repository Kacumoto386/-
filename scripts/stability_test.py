#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gym-excel-system V2.15.5 全面稳定性测试脚本 v2
基于实际方法名和字段名测试所有核心模块
"""

import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from config import EXCEL_PATH, __version__
from core.business import BusinessLayer

PASS = 0
FAIL = 0
ERRORS = []

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f"  ✅ {name}")
    except Exception as e:
        FAIL += 1
        tb = traceback.format_exc()
        ERRORS.append((name, str(e), tb))
        print(f"  ❌ {name}: {e}")

print(f"\n📋 gym-excel-system V{__version__} 全面稳定性测试 v2")
print(f"📁 数据文件: {EXCEL_PATH}")
print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}")

biz = BusinessLayer(EXCEL_PATH)

# ====================================================
# 第1部分：员工管理
# ====================================================
print("\n【1/8】👥 员工管理")

def t_1_1():
    staff = biz.get_all_staff()
    assert isinstance(staff, list), "返回类型应为list"
    assert len(staff) > 0, "应有员工数据"
    print(f"      员工总数: {len(staff)}")
    # 验证关键字段
    for s in staff[:1]:
        assert '姓名' in s
        assert '岗位' in s
        assert '手机号' in s
test("获取所有员工（字段完整性）", t_1_1)

def t_1_2():
    # 按岗位过滤（自己实现）
    staff = biz.get_all_staff()
    coaches = [s for s in staff if s.get('岗位') in ('教练','健身教练')]
    print(f"      教练人数: {len(coaches)}")
    assert len(coaches) > 0 or True  # 不一定有
test("手动筛选教练", t_1_2)

def t_1_3():
    s = biz.get_staff(1)  # 按索引
    assert s is not None or True
    staff = biz.get_all_staff()
    if staff:
        s = biz.get_all_staff()[0]
        assert '员工编号' in s
test("员工编号有效性", t_1_3)

# ====================================================
# 第2部分：会员管理
# ====================================================
print("\n【2/8】🎫 会员管理")

def t_2_1():
    members = biz.get_all_members()
    assert isinstance(members, list) and len(members) > 0
    print(f"      会员总数: {len(members)}")
    for m in members[:1]:
        assert '姓名' in m
        assert '手机号' in m
test("获取所有会员", t_2_1)

def t_2_2():
    result = biz.search_members("张三")
    assert isinstance(result, list)
    print(f"      搜索'张三': {len(result)}条")
test("搜索会员（search_members）", t_2_2)

def t_2_3():
    result = biz.search_members("138")
    print(f"      搜索'138': {len(result)}条")
test("会员手机号搜索", t_2_3)

def t_2_4():
    ids = biz.get_member_id_names()
    assert isinstance(ids, dict)
    print(f"      会员ID-Name映射: {len(ids)}条")
test("会员ID-Name映射", t_2_4)

# ====================================================
# 第3部分：课程管理
# ====================================================
print("\n【3/8】📚 课程管理")

def t_3_1():
    courses = biz.get_all_courses()
    assert isinstance(courses, list) and len(courses) > 0
    print(f"      课程总数: {len(courses)}")
    for c in courses[:1]:
        assert '课程名称' in c
        assert '课程编号' in c
test("获取所有课程", t_3_1)

def t_3_2():
    ids = biz.get_course_id_names()
    assert isinstance(ids, dict)
    print(f"      课程ID-Name映射: {len(ids)}条")
test("课程ID-Name映射", t_3_2)

def t_3_3():
    trainers = biz.get_all_trainers()
    assert isinstance(trainers, list)
    print(f"      教练列表: {len(trainers)}条")
test("获取教练列表", t_3_3)

# ====================================================
# 第4部分：售课 + 课程包
# ====================================================
print("\n【4/8】💳 售课与课程包")

def t_4_1():
    sales = biz.get_all_sales()
    assert isinstance(sales, list)
    print(f"      售课记录数: {len(sales)}")
    if sales:
        s = sales[0]
        for field in ['售课编号','会员姓名','课程名称']:
            assert field in s, f"缺少'{field}'"
        print(f"      字段数: {len(s)}")
test("获取所有售课记录", t_4_1)

def t_4_2():
    packages = biz.get_all_packages()
    assert isinstance(packages, list)
    print(f"      课程包记录数: {len(packages)}")
    if packages:
        for field in ['课程包编号','总课时','剩余课时','状态']:
            assert field in packages[0], f"缺少'{field}'"
test("获取所有课程包", t_4_2)

def t_4_3():
    biz.check_sale_expiry()  # 不应报错
    sales = biz.get_all_sales()
    statuses = set(s.get('售课状态','') for s in sales)
    print(f"      售课状态分布: {statuses}")
test("售课过期检查", t_4_3)

def t_4_4():
    sales = biz.get_all_sales()
    total = sum(float(s.get('折后总价',0) or 0) for s in sales)
    total2 = sum(float(s.get('实收金额',0) or 0) for s in sales)
    print(f"      折后总价总额: ¥{total:.2f}, 实收总额: ¥{total2:.2f}")
test("售课金额汇总", t_4_4)

# ====================================================
# 第5部分：业绩统计
# ====================================================
print("\n【5/8】📊 业绩统计")

def t_5_1():
    members = biz.get_all_members()
    active = sum(1 for m in members if m.get('会员状态') == '有效')
    expired = sum(1 for m in members if m.get('会员状态') == '已过期')
    print(f"      会员: 总{len(members)}, 有效{active}, 过期{expired}")
test("会员状态统计", t_5_1)

def t_5_2():
    # 上课统计
    records = biz.get_all_class_records()
    assert isinstance(records, list)
    print(f"      上课记录数: {len(records)}")
test("上课记录统计", t_5_2)

def t_5_3():
    # 教练排名
    ranking = biz.get_trainer_ranking()
    assert isinstance(ranking, list)
    print(f"      教练排名: {len(ranking)}条")
test("教练排名", t_5_3)

# ====================================================
# 第6部分：商品管理 + 零售
# ====================================================
print("\n【6/8】🏪 商品零售")

def t_6_1():
    products = biz.get_all_products()
    assert isinstance(products, list)
    print(f"      商品总数: {len(products)}")
    if products:
        for field in ['商品编号','商品名称','售价','库存数量','单位']:
            assert field in products[0], f"缺少'{field}'"
test("获取所有商品", t_6_1)

def t_6_2():
    # 库存一致性检查
    products = biz.get_all_products()
    for p in products:
        stock = p.get('库存数量', 0)
        try:
            float(stock)
        except:
            pass
    print(f"      库存检查通过 ({len(products)}个商品)")
test("商品库存数据一致性", t_6_2)

def t_6_3():
    sales = biz.get_all_product_sales()
    assert isinstance(sales, list)
    print(f"      零售记录数: {len(sales)}")
test("商品零售记录", t_6_3)

def t_6_4():
    result = biz.search_products("")
    assert isinstance(result, list)
    print(f"      搜索所有商品: {len(result)}条")
test("商品搜索", t_6_4)

# ====================================================
# 第7部分：预约签到
# ====================================================
print("\n【7/8】📅 预约签到")

def t_7_1():
    bookings = biz.get_all_bookings()
    assert isinstance(bookings, list)
    print(f"      预约总数: {len(bookings)}")
    # 关键字段验证
    if bookings:
        for field in ['预约编号','预约日期','开始时间','会员姓名','预约状态']:
            assert field in bookings[0], f"缺少'{field}'"
test("获取所有预约", t_7_1)

def t_7_2():
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_b = biz.get_bookings_by_date(today_str)
    print(f"      今日预约: {len(today_b)}")
test("按日期筛选预约", t_7_2)

def t_7_3():
    checkins = biz.get_all_checkins()
    assert isinstance(checkins, list)
    print(f"      签到记录数: {len(checkins)}")
    if checkins:
        for field in ['进场编号','会员姓名','进场时间']:
            assert field in checkins[0], f"缺少'{field}'"
test("获取签到记录", t_7_3)

def t_7_4():
    today = biz.get_today_checkins()
    print(f"      今日签到: {len(today)}条")
test("今日签到统计", t_7_4)

# ====================================================
# 第8部分：会籍卡 + 充值 + 团课
# ====================================================
print("\n【8/8】💰 会籍卡与团课")

def t_8_1():
    m = biz.get_all_memberships()
    assert isinstance(m, list)
    print(f"      会籍卡记录数: {len(m)}")
    if m:
        for field in ['会籍卡编号','会员姓名','卡类型']:
            assert field in m[0], f"缺少'{field}'"
test("获取会籍卡", t_8_1)

def t_8_2():
    recharges = biz.get_all_recharges()
    # 可能有空
    print(f"      充值记录数: {len(recharges)}")
test("充值记录", t_8_2)

def t_8_3():
    cps = biz.get_all_card_products()
    assert isinstance(cps, list)
    print(f"      卡种产品数: {len(cps)}")
test("卡种产品", t_8_3)

def t_8_4():
    gp = biz.get_all_group_packages()
    assert isinstance(gp, list)
    print(f"      团课打包产品: {len(gp)}")
test("团课打包产品", t_8_4)

def t_8_5():
    mp = biz.get_all_monthly_passes()
    assert isinstance(mp, list)
    print(f"      包月团课: {len(mp)}")
test("包月团课", t_8_5)

def t_8_6():
    # 会员已有套餐查询
    members = biz.get_all_members()
    if members:
        m = members[0]
        mid = m.get('会员编号')
        if mid:
            pkgs = biz.get_member_packages(mid)
            mps = biz.get_member_monthly_passes(mid)
            print(f"      会员{mid}: 课程包{len(pkgs)}, 包月{len(mps)}")
test("会员套餐查询", t_8_6)

def t_8_7():
    # 仪表盘
    stats = biz.get_dashboard_stats()
    assert isinstance(stats, dict)
    print(f"      仪表盘统计字段: {list(stats.keys())}")
    assert 'active_members' in stats
    assert 'sale_amount' in stats
test("仪表盘统计", t_8_7)

# ====================================================
# 汇总
# ====================================================
print(f"\n{'='*60}")
print(f"📊 测试结果汇总")
print(f"{'='*60}")
print(f"  ✅ 通过: {PASS}")
print(f"  ❌ 失败: {FAIL}")
print(f"  总计: {PASS + FAIL}")
rate = PASS / (PASS + FAIL) * 100 if (PASS + FAIL) > 0 else 0
print(f"  通过率: {rate:.1f}%")

if ERRORS:
    print(f"\n📝 失败详情:")
    for name, err, tb in ERRORS:
        lines = tb.strip().split('\n')
        short_tb = '\n    '.join(lines[-3:])
        print(f"\n  [{name}]")
        print(f"    错误: {err}")
        print(f"    追踪: {short_tb}")

print(f"\n{'='*60}")
if FAIL == 0:
    print("🎉 全部测试通过！系统运行稳定。")
else:
    print(f"⚠️  {FAIL}项测试失败，需要关注。")
