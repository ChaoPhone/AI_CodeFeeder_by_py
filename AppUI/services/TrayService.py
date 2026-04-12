"""
系统托盘服务 - 处理托盘图标与菜单
"""
import os
import threading
from typing import Callable, Optional

from . import (
    HAS_PYSTRAY, HAS_PIL, HAS_PYWIN32,
    pystray, is_frozen_exe
)

if HAS_PIL:
    from PIL import Image

if HAS_PYWIN32:
    import win32api
    import win32con


TRAY_ICON_ID = "AICodeFeeder_v192"


class TrayService:
    """
    系统托盘服务
    负责托盘图标显示、菜单管理
    """
    
    def __init__(self,
                 on_show: Callable,
                 on_quit: Callable,
                 get_startup_status: Callable,
                 toggle_startup: Callable,
                 on_register: Optional[Callable] = None):
        self.on_show = on_show
        self.on_quit = on_quit
        self.get_startup_status = get_startup_status
        self.toggle_startup = toggle_startup
        self.on_register = on_register
        self.icon = None
        self._running = False
    
    def _create_image(self):
        """创建托盘图标"""
        if not HAS_PIL:
            return None
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
            if os.path.exists(icon_path):
                return Image.open(icon_path)
        except Exception:
            pass
        return Image.new('RGB', (64, 64), (45, 45, 48))
    
    def _is_menu_registered(self) -> bool:
        """检测右键菜单是否已注册"""
        if not HAS_PYWIN32:
            return False
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CLASSES_ROOT,
                r"Directory\shell\AI_CodeFeeder_Pipeline",
                0,
                win32con.KEY_READ
            )
            win32api.RegCloseKey(key)
            return True
        except Exception:
            return False
    
    def start(self) -> bool:
        """
        启动托盘服务
        
        :return: 是否成功启动
        """
        if not HAS_PYSTRAY or not HAS_PIL:
            return False
        
        if self._running:
            return True
        
        menu_items = [
            pystray.MenuItem("显示主界面", self.on_show, default=True),
            pystray.MenuItem("开机自启", self._on_toggle_startup, checked=lambda item: self.get_startup_status()),
        ]
        
        if is_frozen_exe():
            if not self._is_menu_registered():
                menu_items.append(pystray.MenuItem("注册右键菜单", self._on_register_menu))
            else:
                menu_items.append(pystray.MenuItem("卸载右键菜单", self._on_unregister_menu))
        
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.on_quit)
        ])
        
        menu = pystray.Menu(*menu_items)
        self.icon = pystray.Icon(TRAY_ICON_ID, self._create_image(), "AI CodeFeeder", menu)
        self._running = True
        threading.Thread(target=self._run_icon, daemon=True).start()
        return True
    
    def _run_icon(self) -> None:
        """托盘图标运行线程"""
        try:
            self.icon.run()
        except Exception:
            pass
        self._running = False
    
    def stop(self) -> None:
        """停止托盘服务"""
        if self.icon and self._running:
            try:
                self.icon.stop()
            except Exception:
                pass
        self._running = False
        self.icon = None
    
    def is_running(self) -> bool:
        """检查托盘是否正在运行"""
        return self._running
    
    def _on_toggle_startup(self, icon, item) -> None:
        self.toggle_startup(icon, item)
    
    def _on_register_menu(self, icon, item) -> None:
        if self.on_register:
            self.on_register()
    
    def _on_unregister_menu(self, icon, item) -> None:
        from Core.Installer import unregister_context_menu
        unregister_context_menu()