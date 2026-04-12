"""
开机启动服务 - 处理注册表启动项管理
"""
import os
import sys
from typing import Optional

from . import HAS_PYWIN32, is_frozen_exe, get_exe_path

if HAS_PYWIN32:
    import win32api
    import win32con


class StartupService:
    """
    开机启动服务
    负责管理 Windows 注册表启动项
    """
    
    STARTUP_NAME = "AICodeFeeder"
    REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    @staticmethod
    def _get_app_path() -> str:
        """获取应用程序路径"""
        if is_frozen_exe():
            return sys.executable
        return get_exe_path()
    
    @staticmethod
    def is_startup_enabled() -> bool:
        """
        检查是否已设置开机启动
        
        :return: 是否已设置
        """
        if not HAS_PYWIN32:
            return False
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                StartupService.REGISTRY_PATH,
                0,
                win32con.KEY_READ
            )
            win32api.RegQueryValueEx(key, StartupService.STARTUP_NAME)
            win32api.RegCloseKey(key)
            return True
        except Exception:
            return False
    
    @staticmethod
    def enable_startup() -> bool:
        """
        启用开机启动
        
        :return: 是否成功
        """
        return StartupService.toggle_startup(True)
    
    @staticmethod
    def disable_startup() -> bool:
        """
        禁用开机启动
        
        :return: 是否成功
        """
        return StartupService.toggle_startup(False)
    
    @staticmethod
    def toggle_startup(enabled: bool) -> bool:
        """
        设置开机启动状态
        
        :param enabled: 是否启用
        :return: 是否成功
        """
        if not HAS_PYWIN32:
            return False
        
        exe_path = StartupService._get_app_path()
        cmd = f'"{exe_path}"'
        
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                StartupService.REGISTRY_PATH,
                0,
                win32con.KEY_SET_VALUE
            )
            if enabled:
                win32api.RegSetValueEx(key, StartupService.STARTUP_NAME, 0, win32con.REG_SZ, cmd)
            else:
                try:
                    win32api.RegDeleteValue(key, StartupService.STARTUP_NAME)
                except Exception:
                    pass
            win32api.RegCloseKey(key)
            return True
        except Exception:
            return False