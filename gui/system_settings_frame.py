"""
系统设置 - 自定义系统名称
"""
import tkinter as tk
from tkinter import ttk, messagebox
from config import PROJECT_NAME, __version__


class SystemSettingsFrame(ttk.Frame):
    """系统设置界面"""

    def __init__(self, parent, biz, callback=None):
        super().__init__(parent)
        self.biz = biz
        self.callback = callback
        self.build_ui()
        self.load_current_name()

    def build_ui(self):
        # 标题
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=30, pady=(30, 10))
        ttk.Label(header, text="⚙️ 系统设置",
                  font=("微软雅黑", 18, "bold"), foreground="#1F4E79").pack(anchor=tk.W)

        # 分隔线
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=30, pady=5)

        # 内容区
        content = ttk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # ── 系统名称设置 ──
        name_section = ttk.LabelFrame(content, text="系统名称", padding=20)
        name_section.pack(fill=tk.X, pady=10)

        ttk.Label(name_section, text="当前名称：", font=("微软雅黑", 11)).grid(
            row=0, column=0, sticky=tk.W, pady=6)

        self.current_label = tk.Label(name_section, text="",
                                       font=("微软雅黑", 12, "bold"),
                                       fg="#4472C4", anchor=tk.W)
        self.current_label.grid(row=0, column=1, sticky=tk.W, padx=10)

        ttk.Label(name_section, text="新名称：", font=("微软雅黑", 11)).grid(
            row=1, column=0, sticky=tk.W, pady=6)

        self.name_entry = tk.Entry(name_section, font=("微软雅黑", 12), width=30)
        self.name_entry.grid(row=1, column=1, sticky=tk.W, padx=10)
        self.name_entry.insert(0, PROJECT_NAME)

        tip_frame = ttk.Frame(name_section)
        tip_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        ttk.Label(tip_frame, text="💡 修改后将更新窗口标题、底部版本号显示",
                  font=("微软雅黑", 9), foreground="#999").pack(anchor=tk.W)
        ttk.Label(tip_frame, text="💡 改动将保存到 Excel 首页看板，重启后自动加载",
                  font=("微软雅黑", 9), foreground="#999").pack(anchor=tk.W)

        btn_frame = ttk.Frame(name_section)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=15)
        tk.Button(btn_frame, text="✅ 保存名称", font=("微软雅黑", 11),
                  bg="#4472C4", fg="white", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_save_name).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 恢复默认", font=("微软雅黑", 11),
                  bg="#E0E0E0", fg="#333", padx=25, pady=5, bd=0, cursor="hand2",
                  command=self.on_reset_default).pack(side=tk.LEFT, padx=5)

        # ── 关于信息 ──
        about_section = ttk.LabelFrame(content, text="关于", padding=20)
        about_section.pack(fill=tk.X, pady=10)

        info_items = [
            ("版本号", f"v{__version__}"),
            ("引擎", "openpyxl + Tkinter"),
            ("项目路径", ""),
        ]

        for i, (label, value) in enumerate(info_items):
            ttk.Label(about_section, text=f"{label}：",
                      font=("微软雅黑", 10)).grid(row=i, column=0, sticky=tk.W, pady=4)
            val_label = tk.Label(about_section, text=value if value else "",
                                 font=("微软雅黑", 10), fg="#555", anchor=tk.W)
            val_label.grid(row=i, column=1, sticky=tk.W, padx=10)
            if label == "项目路径":
                import os
                val_label.config(text=os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__))))

    def load_current_name(self):
        """加载当前系统名称"""
        custom_name = self.biz.get_custom_name()
        if custom_name:
            self.current_label.config(text=f"「{custom_name}」")
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, custom_name)

    def on_save_name(self):
        """保存系统名称"""
        new_name = self.name_entry.get().strip()
        if not new_name:
            messagebox.showwarning("提示", "系统名称不能为空")
            return
        if len(new_name) > 30:
            messagebox.showwarning("提示", "系统名称不能超过30个字符")
            return

        result = self.biz.set_custom_name(new_name)
        if result.get("success"):
            self.current_label.config(text=f"「{new_name}」")
            if self.callback:
                self.callback(new_name)
            messagebox.showinfo("成功", f"系统名称已更新为「{new_name}」\n重启后自动生效")
        else:
            messagebox.showerror("错误", result.get("error", "保存失败"))

    def on_reset_default(self):
        """恢复为默认名称"""
        if not messagebox.askyesno("确认", f"恢复为默认名称「{PROJECT_NAME}」吗？"):
            return
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, PROJECT_NAME)
        result = self.biz.set_custom_name(PROJECT_NAME)
        if result.get("success"):
            self.current_label.config(text=f"「{PROJECT_NAME}」")
            if self.callback:
                self.callback(PROJECT_NAME)
            messagebox.showinfo("成功", f"已恢复为默认名称「{PROJECT_NAME}」")
