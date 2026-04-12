"""
AppUI 模块导出
"""
from .MainWindow import CodeFeederApp
from .Theme import COLORS, FONTS
from .Components import RoundedFrame, TagCloudFrame
from .Tree import TreeBuilder
from .models import AppState
from .controllers import ScanController, GenerateController, SettingsController
from .services import (
    SingleInstanceService,
    HotkeyService,
    TrayService,
    ExplorerService,
    StartupService,
    set_win11_corners,
    get_missing_dependency_messages,
)

__all__ = [
    "CodeFeederApp",
    "COLORS",
    "FONTS",
    "RoundedFrame",
    "TagCloudFrame",
    "TreeBuilder",
    "AppState",
    "ScanController",
    "GenerateController",
    "SettingsController",
    "SingleInstanceService",
    "HotkeyService",
    "TrayService",
    "ExplorerService",
    "StartupService",
    "set_win11_corners",
    "get_missing_dependency_messages",
]