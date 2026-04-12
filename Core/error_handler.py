"""
统一错误处理模块
"""
import os
import sys
import traceback
import datetime
from typing import Optional, Dict, Any, Callable

try:
    import tkinter as tk
    from tkinter import messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False


class ErrorHandler:
    """
    统一错误处理类
    提供日志记录、错误显示、全局异常钩子等功能
    """
    
    _log_file: Optional[str] = None
    _log_dir: Optional[str] = None
    _root_window: Optional[Any] = None
    _initialized: bool = False
    
    @classmethod
    def setup(cls, log_dir: Optional[str] = None, root_window: Optional[Any] = None) -> None:
        """
        初始化错误处理器
        
        :param log_dir: 日志目录路径
        :param root_window: Tkinter 根窗口（用于显示对话框）
        """
        if cls._initialized:
            return
        
        cls._log_dir = log_dir or cls._get_default_log_dir()
        cls._log_file = os.path.join(cls._log_dir, "error_log.txt")
        cls._root_window = root_window
        
        cls._ensure_log_dir()
        cls._install_global_hook()
        cls._initialized = True
    
    @classmethod
    def _get_default_log_dir(cls) -> str:
        """获取默认日志目录"""
        if getattr(sys, 'frozen', False):
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            return os.path.join(appdata, 'AICodeFeeder', 'logs')
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_dir, 'logs')
    
    @classmethod
    def _ensure_log_dir(cls) -> None:
        """确保日志目录存在"""
        if cls._log_dir and not os.path.exists(cls._log_dir):
            os.makedirs(cls._log_dir, exist_ok=True)
    
    @classmethod
    def _install_global_hook(cls) -> None:
        """安装全局异常钩子"""
        def exception_hook(exc_type, exc_value, exc_traceback):
            cls._log_exception(exc_type, exc_value, exc_traceback)
            
            if HAS_TKINTER and cls._root_window:
                try:
                    cls._show_error_dialog(str(exc_value), title="程序错误")
                except:
                    pass
            
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = exception_hook
    
    @classmethod
    def handle(cls, 
               error: Exception, 
               context: Optional[Dict[str, Any]] = None,
               show_dialog: bool = True,
               log: bool = True) -> None:
        """
        处理错误
        
        :param error: 异常对象
        :param context: 错误上下文信息
        :param show_dialog: 是否显示对话框
        :param log: 是否记录日志
        """
        if log:
            cls._log_error(error, context)
        
        if show_dialog and HAS_TKINTER and cls._root_window:
            cls._show_error_dialog(str(error), context=context)
    
    @classmethod
    def _log_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """记录错误日志"""
        if not cls._log_file:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_type = type(error).__name__
        error_msg = str(error)
        
        log_entry = f"[{timestamp}] {error_type}: {error_msg}\n"
        
        if context:
            log_entry += f"  Context: {context}\n"
        
        log_entry += f"  Traceback:\n"
        for line in traceback.format_tb(error.__traceback__):
            log_entry += f"    {line.strip()}\n"
        log_entry += "\n"
        
        try:
            with open(cls._log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    @classmethod
    def _log_exception(cls, exc_type, exc_value, exc_traceback) -> None:
        """记录异常日志"""
        if not cls._log_file:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] Unhandled Exception:\n"
        log_entry += f"  Type: {exc_type.__name__}\n"
        log_entry += f"  Value: {exc_value}\n"
        log_entry += f"  Traceback:\n"
        for line in traceback.format_exception(exc_type, exc_value, exc_traceback):
            log_entry += f"    {line.strip()}\n"
        log_entry += "\n"
        
        try:
            with open(cls._log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    @classmethod
    def _show_error_dialog(cls, 
                          message: str, 
                          title: str = "错误",
                          context: Optional[Dict[str, Any]] = None) -> None:
        """显示错误对话框"""
        if not HAS_TKINTER or not cls._root_window:
            return
        
        full_message = message
        if context:
            full_message += f"\n\n上下文: {context}"
        
        try:
            messagebox.showerror(title, full_message, parent=cls._root_window)
        except:
            print(f"[ERROR] {title}: {full_message}")
    
    @classmethod
    def log_info(cls, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录信息日志"""
        if not cls._log_file:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] INFO: {message}"
        if context:
            log_entry += f" | Context: {context}"
        log_entry += "\n"
        
        try:
            with open(cls._log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    @classmethod
    def log_warning(cls, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """记录警告日志"""
        if not cls._log_file:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] WARNING: {message}"
        if context:
            log_entry += f" | Context: {context}"
        log_entry += "\n"
        
        try:
            with open(cls._log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    @classmethod
    def get_log_file_path(cls) -> Optional[str]:
        """获取日志文件路径"""
        return cls._log_file
    
    @classmethod
    def clear_log(cls) -> None:
        """清空日志文件"""
        if cls._log_file and os.path.exists(cls._log_file):
            try:
                os.remove(cls._log_file)
            except:
                pass