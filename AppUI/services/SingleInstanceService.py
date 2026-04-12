"""
单实例检测服务 - 使用 Windows 互斥锁
"""
import ctypes


class SingleInstanceService:
    """
    单实例检测服务
    使用 Windows Mutex 确保只有一个实例运行
    """
    
    SINGLE_INSTANCE_MUTEX_NAME = "Global\\AICodeFeeder_SingleInstance_v1_9_2"
    
    def __init__(self):
        self.mutex_handle = None
        self.is_first_instance = False
    
    def try_acquire(self) -> bool:
        """
        尝试获取单实例锁
        返回 True 表示是第一个实例，False 表示已有其他实例运行
        """
        try:
            ERROR_ALREADY_EXISTS = 183
            
            self.mutex_handle = ctypes.windll.kernel32.CreateMutexW(
                None,
                False,
                self.SINGLE_INSTANCE_MUTEX_NAME
            )
            
            if not self.mutex_handle:
                return True
            
            last_error = ctypes.windll.kernel32.GetLastError()
            if last_error == ERROR_ALREADY_EXISTS:
                self.is_first_instance = False
                return False
            else:
                self.is_first_instance = True
                return True
        except Exception:
            return True
    
    def release(self) -> None:
        """释放互斥锁"""
        if self.mutex_handle and self.is_first_instance:
            try:
                ctypes.windll.kernel32.CloseHandle(self.mutex_handle)
            except Exception:
                pass
        self.mutex_handle = None
    
    def notify_existing_instance(self) -> None:
        """通知已存在的实例显示窗口"""
        try:
            target_title_prefix = "AI CodeFeeder"
            
            @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def enum_callback(hwnd, lParam):
                try:
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buffer = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
                        title = buffer.value
                        if title.startswith(target_title_prefix):
                            self._activate_window(hwnd)
                            return False
                except Exception:
                    pass
                return True
            
            ctypes.windll.user32.EnumWindows(enum_callback, 0)
        except Exception:
            pass
    
    def _activate_window(self, hwnd) -> bool:
        """激活指定窗口"""
        try:
            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.ShowWindow(hwnd, 5)
            return True
        except Exception:
            return False