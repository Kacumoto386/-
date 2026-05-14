# -
一个轻量化+数字健身俱乐部管理系统
README.md
健身房Excel管理系统 (GymExcelSystem)
基于Excel的健身房会员管理系统，通过Python GUI启动器增强功能。

功能特点
全功能Excel工作簿：12个Sheet页，完整覆盖健身房业务
Python GUI启动器：一键操作，无需记忆Excel公式
自动化流程：编号生成、数据校验、公式填充、提醒检测
操作日志：所有数据变更自动记录，可审计追溯
一键报表：自动生成统计报表和图表
项目结构
gym-excel-system/
├── main.py                    # 启动器主入口
├── config.py                  # 全局配置
├── core/                      # 核心模块
│   ├── excel_engine.py        # Excel读写引擎
│   ├── logger.py              # 操作日志模块
│   ├── validator.py           # 数据校验
│   └── auto_num.py            # 自动编号生成
├── gui/                       # 界面模块
│   ├── main_window.py         # 主窗口
│   └── ...
├── data/                      # 数据文件
│   └── 健身房会员系统.xlsx     # 主工作簿
├── scripts/                   # 工具脚本
│   └── init_workbook.py       # 初始化工作簿
└── requirements.txt           # 依赖
技术栈
Python 3.12+
openpyxl (Excel读写)
tkinter (GUI)
matplotlib (图表)
使用说明
安装依赖：pip install -r requirements.txt
运行主程序：python main.py
