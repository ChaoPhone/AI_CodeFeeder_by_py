"""
资源管理器服务 - 处理文件路径获取与高亮显示
"""
import os
import subprocess
import ctypes
from typing import Optional

from . import HAS_PYWIN32

if HAS_PYWIN32:
    import win32com.client


class ExplorerService:
    """
    资源管理器服务
    负责获取选中路径、文件高亮显示等
    """
    
    @staticmethod
    def get_selected_path() -> Optional[str]:
        """
        获取资源管理器中当前选中的路径
        
        :return: 选中的文件或目录路径
        """
        if not HAS_PYWIN32:
            return None
        try:
            shell = win32com.client.Dispatch("Shell.Application")
            windows = shell.Windows()
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            for window in windows:
                if int(window.hwnd) == hwnd:
                    selected_items = window.Document.SelectedItems()
                    if selected_items.Count > 0:
                        return selected_items.Item(0).Path
                    return window.Document.Folder.Self.Path
        except Exception:
            pass
        return None
    
    @staticmethod
    def reveal_file_in_new_window(file_path: str) -> bool:
        """
        在新资源管理器窗口中显示文件
        
        :param file_path: 文件路径
        :return: 是否成功
        """
        try:
            subprocess.Popen(["explorer", f"/select,{os.path.normpath(file_path)}"])
            return True
        except Exception:
            return False
    
    @staticmethod
    def highlight_file_in_existing_window(file_path: str) -> bool:
        """
        在现有资源管理器窗口中高亮显示文件
        
        :param file_path: 文件路径
        :return: 是否成功
        """
        if not HAS_PYWIN32:
            return False
        try:
            norm_file = os.path.normcase(os.path.normpath(file_path))
            target_dir = os.path.normcase(os.path.dirname(norm_file))
            target_name = os.path.basename(norm_file)
            
            shell = win32com.client.Dispatch("Shell.Application")
            active_hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            for window in shell.Windows():
                try:
                    folder_path = window.Document.Folder.Self.Path
                    if os.path.normcase(os.path.normpath(folder_path)) != target_dir:
                        continue
                    
                    file_item = window.Document.Folder.ParseName(target_name)
                    if file_item:
                        window.Document.SelectItem(file_item, 29)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False