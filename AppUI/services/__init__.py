"""
系统服务层 - 热键、托盘、资源管理器集成
"""
import os
import sys
import ctypes

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

SINGLE_INSTANCE_MUTEX_NAME = "Global\\AICodeFeeder_SingleInstance_v1_9_2"
TRAY_ICON_ID = "AICodeFeeder_v192"


def is_frozen_exe():
    return getattr(sys, 'frozen', False)


def get_exe_path():
    if is_frozen_exe():
        return sys.executable
    return os.path.abspath(sys.argv[0])


def set_win11_corners(hwnd):
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


from .SingleInstanceService import SingleInstanceService
from .HotkeyService import HotkeyService
from .TrayService import TrayService
from .ExplorerService import ExplorerService
from .StartupService import StartupService

__all__ = [
    "is_frozen_exe",
    "get_exe_path",
    "set_win11_corners",
    "get_missing_dependency_messages",
    "get_missing_dependency_categories",
    "get_dependency_debug_details",
    "SingleInstanceService",
    "HotkeyService",
    "TrayService",
    "ExplorerService",
    "StartupService",
    "HAS_PYWIN32",
    "HAS_KEYBOARD",
    "HAS_PYSTRAY",
    "HAS_PIL",
    "win32api",
    "win32con",
    "keyboard",
    "pystray",
    "Image",
]