"""
全局热键服务 - 处理快捷键注册与回调
"""
from . import HAS_KEYBOARD, keyboard


class HotkeyService:
    """
    全局热键服务
    负责注册和管理全局快捷键
    """
    
    DEFAULT_HOTKEY = "ctrl+`"
    
    def __init__(self, callback, hotkey: str = None):
        self.callback = callback
        self.hotkey = hotkey or self.DEFAULT_HOTKEY
        self._is_running = False
    
    def start(self) -> bool:
        """
        启动热键监听
        
        :return: 是否成功启动
        """
        if not HAS_KEYBOARD:
            return False
        try:
            keyboard.add_hotkey(self.hotkey, self.callback)
            self._is_running = True
            return True
        except Exception:
            return False
    
    def stop(self) -> None:
        """停止热键监听"""
        if not HAS_KEYBOARD or not self._is_running:
            return
        try:
            keyboard.remove_hotkey(self.hotkey)
        except Exception:
            pass
        self._is_running = False
    
    def is_running(self) -> bool:
        """检查热键是否正在运行"""
        return self._is_running