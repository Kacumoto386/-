# -*- coding: utf-8 -*-
"""在 BaseDataFrame 的工具栏追加"重新激活"按钮"""

def add_reactivation_button(target_frame, btn_frame, text, command):
    """在 BaseDataFrame 的工具栏追加操作按钮
    
    Args:
        target_frame: Frame 实例（SaleFrame 等）
        btn_frame: 按钮所在的 Frame
        text: 按钮文字
        command: 回调函数
    """
    configs = {
        "text": text,
        "font": ("微软雅黑", 10),
        "bg": "#E67E22", "fg": "white",
        "padx": 12, "pady": 3, "bd": 0, "cursor": "hand2",
        "command": command,
    }
    return tk.Button(btn_frame, **configs)
