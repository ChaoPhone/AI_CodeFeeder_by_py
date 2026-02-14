import os
import sys
import win32api
import win32con
import ctypes
import threading
import keyboard
import pystray
from PIL import Image
import win32com.client

def set_win11_corners(hwnd):
    """为 Windows 11 窗口设置圆角效果"""
    try:
        # DWMWA_WINDOW_CORNER_PREFERENCE = 33
        # DWMWCP_ROUND = 2
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        preference = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 
            DWMWA_WINDOW_CORNER_PREFERENCE, 
            ctypes.byref(preference), 
            ctypes.sizeof(preference)
        )
    except Exception as e:
        print(f"设置圆角失败: {e}")

class SystemHotkeyService:
    def __init__(self, callback):
        self.callback = callback
        self.hotkey = "ctrl+`"  # 使用 ctrl+` (即 ctrl+·)

    def start(self):
        try:
            keyboard.add_hotkey(self.hotkey, self.callback)
            print(f"✅ 全局快捷键已注册: {self.hotkey}")
        except Exception as e:
            print(f"❌ 快捷键注册失败: {e}")

class SystemTrayService:
    def __init__(self, on_show, on_quit, get_startup_status, toggle_startup):
        self.on_show = on_show
        self.on_quit = on_quit
        self.get_startup_status = get_startup_status
        self.toggle_startup = toggle_startup
        self.icon = None

    def _create_image(self):
        # 尝试加载图标文件，如果不存在则创建一个简单的
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
            if os.path.exists(icon_path):
                return Image.open(icon_path)
        except:
            pass
        
        # 创建一个简单的 64x64 图标
        image = Image.new('RGB', (64, 64), (45, 45, 48))
        return image

    def _on_toggle_startup(self, icon, item):
        # 直接调用传入的 toggle_startup 回调，并传递 icon 和 item
        self.toggle_startup(icon, item)

    def start(self):
        menu = pystray.Menu(
            pystray.MenuItem("显示主界面", self.on_show, default=True),
            pystray.MenuItem("开机自启", self._on_toggle_startup, checked=lambda item: self.get_startup_status()),
            # pystray 0.19.5 使用 Menu.SEPARATOR
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.on_quit)
        )
        
        self.icon = pystray.Icon("AICodeFeeder", self._create_image(), "AI CodeFeeder", menu)
        
        # 在独立线程中运行托盘图标
        threading.Thread(target=self.icon.run, daemon=True).start()
        print("✅ 系统托盘服务已启动")

class ExplorerService:
    @staticmethod
    def get_selected_path():
        """获取当前 Windows 资源管理器中选中的路径"""
        try:
            shell = win32com.client.Dispatch("Shell.Application")
            windows = shell.Windows()
            
            # 获取当前活动的资源管理器窗口
            # 这里的逻辑是获取最后激活的窗口，或者遍历寻找
            # 这是一个常见的 trick
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            for window in windows:
                if int(window.hwnd) == hwnd:
                    # 获取选中的项目
                    selected_items = window.Document.SelectedItems()
                    if selected_items.Count > 0:
                        return selected_items.Item(0).Path
                    
                    # 如果没有选中项目，返回当前文件夹路径
                    return window.Document.Folder.Self.Path
        except Exception as e:
            print(f"获取资源管理器路径失败: {e}")
        return None

class StartupService:
    # 获取脚本绝对路径（更可靠）
    @staticmethod
    def _get_app_path():
        # 如果是冻结的EXE（PyInstaller等）
        if getattr(sys, 'frozen', False):
            return sys.executable
        
        # 否则是Python脚本，需要找到正确的入口文件
        # 优先使用 __file__ 的上级目录中的 CodeFeeder.pyw
        try:
            # 从 SystemServices.py 的位置推算
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            main_script = os.path.join(current_dir, "CodeFeeder.pyw")
            if os.path.exists(main_script):
                return main_script
            
            # 备选：CodeFeeder.py
            main_script = os.path.join(current_dir, "CodeFeeder.py")
            if os.path.exists(main_script):
                return main_script
        except:
            pass
        
        # 最后的备选：sys.argv[0]
        return os.path.abspath(sys.argv[0])

    @staticmethod
    def _build_command():
        app_path = StartupService._get_app_path()
        
        # 确保使用 pythonw.exe 运行（无窗口）
        if app_path.endswith('.py') or app_path.endswith('.pyw'):
            # 找到正确的 pythonw.exe
            python_dir = os.path.dirname(sys.executable)
            pythonw_exe = os.path.join(python_dir, "pythonw.exe")
            
            # 如果 pythonw.exe 不存在，尝试替换
            if not os.path.exists(pythonw_exe) and sys.executable.endswith("python.exe"):
                pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
            
            # 如果还是不存在，就用 sys.executable
            if not os.path.exists(pythonw_exe):
                pythonw_exe = sys.executable
                
            return f'"{pythonw_exe}" "{app_path}"'
        else:
            # EXE 直接运行
            return f'"{app_path}"'

    @staticmethod
    def is_startup_enabled():
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                0, 
                win32con.KEY_READ
            )
            win32api.RegQueryValueEx(key, "AICodeFeeder")
            win32api.RegCloseKey(key)
            return True
        except:
            return False

    @staticmethod
    def toggle_startup(enabled):
        cmd = StartupService._build_command()
        print(f"调试：准备写入注册表的命令 = {cmd}")  # 调试输出
        
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                0, 
                win32con.KEY_SET_VALUE
            )
            if enabled:
                win32api.RegSetValueEx(key, "AICodeFeeder", 0, win32con.REG_SZ, cmd)
                print(f"✅ 已添加开机自启: {cmd}")
            else:
                try:
                    win32api.RegDeleteValue(key, "AICodeFeeder")
                    print("✅ 已移除开机自启")
                except:
                    pass
            win32api.RegCloseKey(key)
            return True
        except Exception as e:
            print(f"❌ 设置自启动失败: {e}")
            import traceback
            traceback.print_exc()  # 打印完整错误堆栈
            return False