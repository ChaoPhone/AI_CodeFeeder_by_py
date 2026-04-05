"""
系统服务层 - 热键、托盘、资源管理器集成
"""
import os
import sys
import ctypes
import threading
import subprocess
import time

# 依赖导入状态
PYWIN32_IMPORT_ERROR = ""
KEYBOARD_IMPORT_ERROR = ""
PYSTRAY_IMPORT_ERROR = ""
PIL_IMPORT_ERROR = ""

try:
    import win32api
    import win32con
    import win32com.client
    HAS_PYWIN32 = True
except ImportError:
    win32api = None
    win32con = None
    HAS_PYWIN32 = False
    PYWIN32_IMPORT_ERROR = str(sys.exc_info()[1] or "")

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    keyboard = None
    HAS_KEYBOARD = False
    KEYBOARD_IMPORT_ERROR = str(sys.exc_info()[1] or "")

try:
    import pystray
    HAS_PYSTRAY = True
except ImportError:
    pystray = None
    HAS_PYSTRAY = False
    PYSTRAY_IMPORT_ERROR = str(sys.exc_info()[1] or "")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None
    HAS_PIL = False
    PIL_IMPORT_ERROR = str(sys.exc_info()[1] or "")


def is_frozen_exe():
    return getattr(sys, 'frozen', False)


def get_exe_path():
    if is_frozen_exe():
        return sys.executable
    return os.path.abspath(sys.argv[0])


def set_win11_corners(hwnd):
    """为 Windows 11 窗口设置圆角效果"""
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        preference = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(preference),
            ctypes.sizeof(preference)
        )
    except Exception:
        pass


def get_missing_dependency_messages():
    messages = []
    if not HAS_PYWIN32:
        messages.append("缺少 pywin32：资源管理器联动不可用")
    if not HAS_KEYBOARD:
        messages.append("缺少 keyboard：全局快捷键 Ctrl+` 不可用")
    if not HAS_PYSTRAY:
        messages.append("缺少 pystray：系统托盘不可用")
    if not HAS_PIL:
        messages.append("缺少 Pillow：托盘图标不可用")
    return messages


def get_missing_dependency_categories():
    def check_dep(name):
        var_name = f"HAS_{name.upper().replace('32', '')}"
        return globals().get(var_name, False)

    return {
        "critical": [s for s in ["pywin32", "keyboard", "pystray", "Pillow"] if not check_dep(s)],
        "optional": [],
    }


def get_dependency_debug_details():
    details = []
    if not HAS_PYWIN32 and PYWIN32_IMPORT_ERROR:
        details.append(f"pywin32: {PYWIN32_IMPORT_ERROR}")
    if not HAS_KEYBOARD and KEYBOARD_IMPORT_ERROR:
        details.append(f"keyboard: {KEYBOARD_IMPORT_ERROR}")
    if not HAS_PYSTRAY and PYSTRAY_IMPORT_ERROR:
        details.append(f"pystray: {PYSTRAY_IMPORT_ERROR}")
    if not HAS_PIL and PIL_IMPORT_ERROR:
        details.append(f"Pillow: {PIL_IMPORT_ERROR}")
    return details


class SystemHotkeyService:
    def __init__(self, callback):
        self.callback = callback
        self.hotkey = "ctrl+`"

    def start(self):
        if not HAS_KEYBOARD:
            return False
        try:
            keyboard.add_hotkey(self.hotkey, self.callback)
            return True
        except Exception:
            return False


class SystemTrayService:
    def __init__(self, on_show, on_quit, get_startup_status, toggle_startup, on_register=None):
        self.on_show = on_show
        self.on_quit = on_quit
        self.get_startup_status = get_startup_status
        self.toggle_startup = toggle_startup
        self.on_register = on_register  # 注册菜单回调
        self.icon = None

    def _create_image(self):
        if not HAS_PIL:
            return None
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
            if os.path.exists(icon_path):
                return Image.open(icon_path)
        except Exception:
            pass
        return Image.new('RGB', (64, 64), (45, 45, 48))

    def _is_menu_registered(self):
        """检测右键菜单是否已注册"""
        if not HAS_PYWIN32:
            return False
        try:
            key = win32api.RegOpenKeyEx(win32con.HKEY_CLASSES_ROOT, r"Directory\shell\AI_CodeFeeder_Pipeline", 0, win32con.KEY_READ)
            win32api.RegCloseKey(key)
            return True
        except Exception:
            return False

    def start(self):
        if not HAS_PYSTRAY or not HAS_PIL:
            return False

        # 构建菜单
        menu_items = [
            pystray.MenuItem("显示主界面", self.on_show, default=True),
            pystray.MenuItem("开机自启", self._on_toggle_startup, checked=lambda item: self.get_startup_status()),
        ]

        # exe 模式下显示注册/卸载选项
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
        self.icon = pystray.Icon("AICodeFeeder", self._create_image(), "AI CodeFeeder", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()
        return True

    def stop(self):
        if self.icon:
            self.icon.stop()

    def _on_toggle_startup(self, icon, item):
        self.toggle_startup(icon, item)

    def _on_register_menu(self, icon, item):
        """托盘菜单触发注册"""
        if self.on_register:
            self.on_register()

    def _on_unregister_menu(self, icon, item):
        """托盘菜单触发卸载"""
        from Core.Installer import unregister_context_menu
        unregister_context_menu()


class ExplorerService:
    @staticmethod
    def get_selected_path():
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
    def reveal_file_in_new_window(file_path):
        try:
            subprocess.Popen(["explorer", f"/select,{os.path.normpath(file_path)}"])
            return True
        except Exception:
            return False

    @staticmethod
    def highlight_file_in_existing_window(file_path):
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


class StartupService:
    STARTUP_NAME = "AICodeFeeder"

    @staticmethod
    def _get_app_path():
        if is_frozen_exe():
            return sys.executable
        return get_exe_path()

    @staticmethod
    def is_startup_enabled():
        if not HAS_PYWIN32:
            return False
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                win32con.KEY_READ
            )
            win32api.RegQueryValueEx(key, StartupService.STARTUP_NAME)
            win32api.RegCloseKey(key)
            return True
        except Exception:
            return False

    @staticmethod
    def toggle_startup(enabled):
        if not HAS_PYWIN32:
            return False

        exe_path = StartupService._get_app_path()
        cmd = f'"{exe_path}"'

        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
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