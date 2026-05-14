"""
全局异常层次 - unified exception handling
"""
from tkinter import messagebox


class GymSystemError(Exception):
    """系统基础异常"""
    def __init__(self, message, detail=None):
        self.message = message
        self.detail = detail
        super().__init__(message)

    def show_dialog(self, title="操作失败"):
        """弹出错误提示框"""
        msg = self.message
        if self.detail:
            msg += f"\n\n详细信息: {self.detail}"
        messagebox.showerror(title, msg)


class ValidationError(GymSystemError):
    """数据验证错误"""
    def __init__(self, field, reason):
        self.field = field
        self.reason = reason
        super().__init__(f"「{field}」{reason}")


class DataNotFoundError(GymSystemError):
    """数据未找到"""
    pass


class DuplicateDataError(GymSystemError):
    """数据重复"""
    pass


class ExcelError(GymSystemError):
    """Excel 操作错误"""
    pass


class BusinessLogicError(GymSystemError):
    """业务逻辑错误"""
    pass


def safe_catch(parent=None, title="操作失败"):
    """装饰器：统一异常捕获
    
    用法:
        @safe_catch(parent=self, title="保存失败")
        def on_save(self):
            ...
    """
    import functools
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                e.show_dialog(title)
            except GymSystemError as e:
                e.show_dialog(title)
            except Exception as e:
                msg = f"发生未知错误: {type(e).__name__}: {e}"
                if parent:
                    try:
                        messagebox.showerror(title, msg)
                    except Exception:
                        pass
                else:
                    messagebox.showerror(title, msg)
            return None
        return wrapper
    return decorator


def confirm_action(title="确认操作", message="确定要执行此操作吗？"):
    """统一确认对话框"""
    return messagebox.askyesno(title, message)


def show_success(title="操作成功", message="操作已完成"):
    """统一成功提示"""
    messagebox.showinfo(title, message)


def show_error(title="操作失败", message="操作执行时发生错误"):
    """统一错误提示"""
    messagebox.showerror(title, message)
