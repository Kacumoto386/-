"""
主窗口 - 健身房Excel管理系统的GUI主界面
包含导航菜单、仪表盘和各功能模块的入口
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SHEETS, PROJECT_NAME, __version__
from core.business import BusinessLayer
from core.store_manager import StoreManager


class MainWindow:
    """系统主窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1280x800")
        self.root.minsize(1024, 680)

        # 初始化业务层
        self.biz = BusinessLayer()

        # 读取自定义名称，更新窗口标题
        self.custom_name = self.biz.get_custom_name()
        self.root.title(f"{self.custom_name} v{__version__}")

        # 初始化门店管理器
        self.store_mgr = StoreManager(self.biz.engine)
        self.biz.store_mgr = self.store_mgr  # 让新增操作自动注入门店编号
        self.current_store_id = self.store_mgr.ensure_default_store(self.biz)

        # 设置样式
        self.setup_styles()

        # 构建界面
        self.build_layout()

        # 加载首页
        self.show_dashboard()

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        """设置全局样式"""
        style = ttk.Style()
        style.theme_use("clam")

        # 导航按钮样式
        style.configure("Nav.TButton", font=("微软雅黑", 11), padding=12)

        # 标题样式
        style.configure("Title.TLabel", font=("微软雅黑", 16, "bold"),
                        foreground="#1F4E79")
        style.configure("Header.TLabel", font=("微软雅黑", 12, "bold"),
                        foreground="#2E75B6")

        # 指标卡片样式
        style.configure("Metric.TFrame", relief="solid", borderwidth=1)
        style.configure("MetricValue.TLabel", font=("微软雅黑", 24, "bold"),
                        foreground="#4472C4")
        style.configure("MetricLabel.TLabel", font=("微软雅黑", 10),
                        foreground="#666666")

    def build_layout(self):
        """构建整体布局"""
        # 主容器分为左侧导航和右侧内容区
        self.main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_panel.pack(fill=tk.BOTH, expand=True)

        # 左侧导航栏
        self.nav_frame = ttk.Frame(self.main_panel, width=200)
        self.main_panel.add(self.nav_frame, weight=0)

        # 右侧内容区
        self.content_frame = ttk.Frame(self.main_panel)
        self.main_panel.add(self.content_frame, weight=1)

        # 构建导航菜单
        self.build_nav()

        # 内容区域容器
        self.content_canvas = tk.Canvas(self.content_frame, bg="#F5F5F5",
                                        highlightthickness=0)
        self.content_canvas.pack(fill=tk.BOTH, expand=True)

        # 当前显示的子框架引用
        self.current_frame = None

    def build_nav(self):
        """构建左侧导航菜单"""
        # 系统标题
        title_frame = ttk.Frame(self.nav_frame)
        title_frame.pack(fill=tk.X, pady=(15, 10), padx=10)

        title_label = ttk.Label(title_frame, text="🏋️ 健身房管理",
                                style="Title.TLabel")
        title_label.pack(anchor=tk.W)

        sub_label = ttk.Label(title_frame, text="Excel管理系統",
                              font=("微软雅黑", 9), foreground="#999999")
        sub_label.pack(anchor=tk.W)

        # 分隔线
        sep = ttk.Separator(self.nav_frame, orient=tk.HORIZONTAL)
        sep.pack(fill=tk.X, padx=10, pady=5)

        # 导航按钮组
        self.nav_buttons = []

        nav_items = [
            ("🏠  首页看板", self.show_dashboard),
            ("─── 财务管理 ───", None),
            ("💰  收入总账", self.show_finance_income),
            ("💸  支出管理", self.show_finance_expense),
            ("📋  财务报表", self.show_finance_report),
            ("─── 课后服务 ───", None),
            ("👤  会员分析", self.show_member_analysis),
            ("🚨  流失预警", self.show_churn_warning),
            ("─── 基础数据 ───", None),
            ("👤  会员管理", self.show_member),
            ("🏷️  手环管理", self.show_wristband),
            ("🃏  可售会籍卡", self.show_card_product),
            ("📦  团课打包产品", self.show_group_package),
            ("🎫  包月团课", self.show_monthly_pass),
            ("👨‍💼  员工管理", self.show_staff),
            ("📚  课程管理", self.show_course),
            ("🏪  商品管理", self.show_product),
            ("─── 业务记录 ───", None),
            ("💰  售课记录", self.show_sale),
            ("📦  课程包", self.show_package),
            ("🃏  售卡记录", self.show_membership_sale),
            ("📅  预约管理", self.show_booking),
            ("🎓  上课记录", self.show_class_record),
            ("💳  会员充值", self.show_recharge),
            ("🛒  商品零售", self.show_product_sale),
            ("─── 业绩统计 ───", None),
            ("📊 业绩总览", self.show_performance_overview),
            ("💳 售课业绩", self.show_performance_sale),
            ("📦 课程包业绩", self.show_performance_package),
            ("🎫 会籍卡业绩", self.show_performance_membership),
            ("🏃 会员进场", self.show_performance_checkin),
            ("💵 员工提成", self.show_stat_commission),
            ("📅  教练排班", self.show_schedule),
            ("─── 辅助工具 ───", None),
            ("📊  体测记录", self.show_body_measurement),
            ("⏰  到期提醒", self.show_alert),
            ("📝  操作日志", self.show_log),
            ("📄  合同管理", self.show_contract),
            ("📤  数据导出", self.show_export),
        ]

        # 滚动区域（用于导航较多的情况）
        nav_canvas = tk.Canvas(self.nav_frame, width=190, highlightthickness=0)
        nav_scrollbar = ttk.Scrollbar(self.nav_frame, orient="vertical",
                                      command=nav_canvas.yview)
        nav_scrollable = ttk.Frame(nav_canvas)

        nav_canvas.configure(yscrollcommand=nav_scrollbar.set)

        for text, command in nav_items:
            if text.startswith("───"):
                # 分隔标题
                lb = ttk.Label(nav_scrollable, text=text,
                               font=("微软雅黑", 9, "bold"),
                               foreground="#4472C4")
                lb.pack(fill=tk.X, padx=10, pady=(10, 2))
            else:
                btn = tk.Button(nav_scrollable,
                                text=text,
                                font=("微软雅黑", 10),
                                bg="#F0F0F0",
                                fg="#333333",
                                activebackground="#4472C4",
                                activeforeground="white",
                                bd=0,
                                padx=15,
                                pady=6,
                                anchor="w",
                                cursor="hand2",
                                command=command)
                btn.pack(fill=tk.X, padx=5, pady=1)
                self.nav_buttons.append(btn)

        nav_canvas.create_window((0, 0), window=nav_scrollable, anchor="nw",
                                 width=185)

        nav_scrollable.bind("<Configure>",
                           lambda e: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")))

        nav_canvas.pack(side="left", fill=tk.BOTH, expand=True, padx=(5, 0))
        nav_scrollbar.pack(side="right", fill="y")

        # 底部区域：系统设置 + 版本信息
        bottom_frame = ttk.Frame(self.nav_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)

        sys_btn = tk.Button(bottom_frame, text="⚙️ 系统设置", font=("微软雅黑", 9),
                            bg="#E8E8E8", fg="#555", bd=0, padx=8, pady=3,
                            cursor="hand2", anchor="w",
                            command=self.show_system_settings)
        sys_btn.pack(fill=tk.X, pady=(0, 3))

        self.version_label = ttk.Label(bottom_frame,
                                       text=f"{self.custom_name} v{__version__}",
                                       font=("微软雅黑", 8), foreground="#CCCCCC")
        self.version_label.pack()

    def clear_content(self):
        """清空内容区域"""
        self.content_canvas.delete("all")
        # 销毁旧的子框架
        for widget in self.content_canvas.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        """显示首页看板"""
        self.clear_content()
        from gui.dashboard_frame import DashboardFrame
        self.current_frame = DashboardFrame(self.content_canvas, self.biz, main_window=self, store_id=self.current_store_id)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_member(self):
        """显示会员管理"""
        self.clear_content()
        from gui.member_frame import MemberFrame
        self.current_frame = MemberFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_wristband(self):
        """显示手环管理"""
        self.clear_content()
        from gui.wristband_frame import WristbandFrame
        self.current_frame = WristbandFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_card_product(self):
        """显示可售会籍卡管理"""
        self.clear_content()
        from gui.card_product_frame import CardProductFrame
        self.current_frame = CardProductFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_group_package(self):
        """显示团课打包产品管理"""
        self.clear_content()
        from gui.group_package_frame import GroupPackageFrame
        self.current_frame = GroupPackageFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_monthly_pass(self):
        """显示包月团课管理"""
        self.clear_content()
        from gui.monthly_pass_frame import MonthlyPassFrame
        self.current_frame = MonthlyPassFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_staff(self):
        """显示员工管理"""
        self.clear_content()
        from gui.staff_frame import StaffFrame
        self.current_frame = StaffFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_course(self):
        """显示课程管理"""
        self.clear_content()
        from gui.course_frame import CourseFrame
        self.current_frame = CourseFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_sale(self):
        """显示售课记录"""
        self.clear_content()
        from gui.sale_frame import SaleFrame
        self.current_frame = SaleFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_package(self):
        """显示课程包管理"""
        self.clear_content()
        from gui.package_frame import PackageFrame
        self.current_frame = PackageFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_booking(self):
        """显示预约管理"""
        self.clear_content()
        from gui.booking_frame import BookingFrame
        self.current_frame = BookingFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_class_record(self):
        """显示上课记录"""
        self.clear_content()
        from gui.class_frame import ClassFrame
        self.current_frame = ClassFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_recharge(self):
        """显示会员充值"""
        self.clear_content()
        from gui.recharge_frame import RechargeFrame
        self.current_frame = RechargeFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_stat_sale(self):
        """显示售课统计"""
        self.clear_content()
        from gui.stats_frame import SaleStatsFrame
        self.current_frame = SaleStatsFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_stat_class(self):
        """显示上课统计"""
        self.clear_content()
        from gui.stats_frame import ClassStatsFrame
        self.current_frame = ClassStatsFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_stat_commission(self):
        """显示员工提成"""
        self.clear_content()
        from gui.stats_frame import CommissionFrame
        self.current_frame = CommissionFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_performance_overview(self):
        """显示业绩总览"""
        self.clear_content()
        from gui.performance_overview_frame import PerformanceOverviewFrame
        self.current_frame = PerformanceOverviewFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_performance_sale(self):
        """显示售课业绩"""
        self.clear_content()
        from gui.performance_sale_frame import PerformanceSaleFrame
        self.current_frame = PerformanceSaleFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_performance_package(self):
        """显示课程包业绩"""
        self.clear_content()
        from gui.performance_package_frame import PerformancePackageFrame
        self.current_frame = PerformancePackageFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_performance_membership(self):
        """显示会籍卡业绩"""
        self.clear_content()
        from gui.performance_membership_frame import PerformanceMembershipFrame
        self.current_frame = PerformanceMembershipFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_performance_checkin(self):
        """显示会员进场"""
        self.clear_content()
        from gui.performance_checkin_frame import PerformanceCheckinFrame
        self.current_frame = PerformanceCheckinFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_schedule(self):
        """显示教练排班"""
        self.clear_content()
        from gui.schedule_frame import ScheduleFrame
        self.current_frame = ScheduleFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_body_measurement(self):
        """显示体测记录"""
        self.clear_content()
        from gui.body_measurement_frame import BodyMeasurementFrame
        self.current_frame = BodyMeasurementFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_alert(self):
        """显示到期提醒"""
        self.clear_content()
        from gui.alert_frame import AlertFrame
        self.current_frame = AlertFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)


    def show_finance_income(self):
        """显示收入总账"""
        self.clear_content()
        from gui.finance_income_frame import FinanceIncomeFrame
        self.current_frame = FinanceIncomeFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_finance_expense(self):
        """显示支出管理"""
        self.clear_content()
        from gui.finance_expense_frame import FinanceExpenseFrame
        self.current_frame = FinanceExpenseFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_finance_report(self):
        """显示财务报表"""
        self.clear_content()
        from gui.finance_report_frame import FinanceReportFrame
        self.current_frame = FinanceReportFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
    def show_log(self):
        """显示操作日志"""
        self.clear_content()
        from gui.log_frame import LogFrame
        self.current_frame = LogFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_product(self):
        """显示商品管理"""
        self.clear_content()
        from gui.product_frame import ProductFrame
        self.current_frame = ProductFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_product_sale(self):
        """显示商品零售"""
        self.clear_content()
        from gui.product_sale_frame import ProductSaleFrame
        self.current_frame = ProductSaleFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_export(self):
        """显示数据导出"""
        self.clear_content()
        from gui.export_frame import ExportFrame
        self.current_frame = ExportFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_membership_sale(self):
        """显示售卡记录"""
        self.clear_content()
        from gui.membership_sale_frame import MembershipSaleFrame
        self.current_frame = MembershipSaleFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_contract(self):
        """显示合同管理"""
        self.clear_content()
        from gui.contract_frame import ContractFrame
        self.current_frame = ContractFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_member_analysis(self):
        """显示会员分析"""
        self.clear_content()
        from gui.member_analysis_frame import MemberAnalysisFrame
        self.current_frame = MemberAnalysisFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def show_churn_warning(self):
        """显示流失预警"""
        self.clear_content()
        from gui.churn_warning_frame import ChurnWarningFrame
        self.current_frame = ChurnWarningFrame(self.content_canvas, self.biz)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def on_close(self):
        """窗口关闭事件"""
        self.biz.save()
        self.biz.close()
        self.root.destroy()

    def show_system_settings(self):
        """显示系统设置"""
        self.clear_content()
        from gui.system_settings_frame import SystemSettingsFrame
        self.current_frame = SystemSettingsFrame(self.content_canvas, self.biz,
                                                  callback=self._on_name_changed)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def _on_name_changed(self, new_name):
        """系统名称变更后的回调"""
        self.custom_name = new_name
        self.root.title(f"{new_name} v{__version__}")
        self.version_label.config(text=f"{new_name} v{__version__}")

    def run(self):
        """运行主循环"""
        self.root.mainloop()
