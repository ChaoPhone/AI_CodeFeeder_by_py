"""
v1.9.2 冒烟测试 - 服务分离验证
测试 services 模块的独立服务
"""
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

def test_services_import():
    print("[1] 测试 services 模块导入...")
    try:
        from AppUI.services import (
            SingleInstanceService,
            HotkeyService,
            TrayService,
            ExplorerService,
            StartupService,
            set_win11_corners,
            get_missing_dependency_messages,
        )
        print("    OK services 模块导入成功")
        return True
    except Exception as e:
        print(f"    FAIL 导入失败: {e}")
        return False

def test_single_instance_service():
    print("[2] 测试 SingleInstanceService...")
    try:
        from AppUI.services import SingleInstanceService
        service = SingleInstanceService()
        is_first = service.try_acquire()
        print(f"    OK SingleInstanceService 创建成功: is_first_instance={is_first}")
        service.release()
        return True
    except Exception as e:
        print(f"    FAIL SingleInstanceService 测试失败: {e}")
        return False

def test_hotkey_service():
    print("[3] 测试 HotkeyService...")
    try:
        from AppUI.services import HotkeyService
        service = HotkeyService(lambda: None)
        print(f"    OK HotkeyService 创建成功: hotkey={service.hotkey}")
        return True
    except Exception as e:
        print(f"    FAIL HotkeyService 测试失败: {e}")
        return False

def test_tray_service():
    print("[4] 测试 TrayService...")
    try:
        from AppUI.services import TrayService
        service = TrayService(
            on_show=lambda: None,
            on_quit=lambda: None,
            get_startup_status=lambda: False,
            toggle_startup=lambda i, item: None
        )
        print(f"    OK TrayService 创建成功: running={service.is_running()}")
        return True
    except Exception as e:
        print(f"    FAIL TrayService 测试失败: {e}")
        return False

def test_explorer_service():
    print("[5] 测试 ExplorerService...")
    try:
        from AppUI.services import ExplorerService
        path = ExplorerService.get_selected_path()
        print(f"    OK ExplorerService 方法测试成功: selected_path={path}")
        return True
    except Exception as e:
        print(f"    FAIL ExplorerService 测试失败: {e}")
        return False

def test_startup_service():
    print("[6] 测试 StartupService...")
    try:
        from AppUI.services import StartupService
        is_enabled = StartupService.is_startup_enabled()
        print(f"    OK StartupService 方法测试成功: is_startup_enabled={is_enabled}")
        return True
    except Exception as e:
        print(f"    FAIL StartupService 测试失败: {e}")
        return False

def test_dependency_helpers():
    print("[7] 测试依赖检测辅助函数...")
    try:
        from AppUI.services import get_missing_dependency_messages, get_missing_dependency_categories
        messages = get_missing_dependency_messages()
        categories = get_missing_dependency_categories()
        print(f"    OK 依赖检测辅助函数测试成功: messages_count={len(messages)}")
        return True
    except Exception as e:
        print(f"    FAIL 依赖检测辅助函数测试失败: {e}")
        return False

def test_main_window_with_services():
    print("[8] 测试 MainWindow 与 services 集成...")
    try:
        from AppUI.MainWindow import CodeFeederApp
        print("    OK MainWindow 与 services 集成成功")
        return True
    except Exception as e:
        print(f"    FAIL MainWindow 与 services 集成失败: {e}")
        return False

def main():
    print("=== v1.9.2 冒烟测试 ===\n")
    
    results = []
    results.append(test_services_import())
    results.append(test_single_instance_service())
    results.append(test_hotkey_service())
    results.append(test_tray_service())
    results.append(test_explorer_service())
    results.append(test_startup_service())
    results.append(test_dependency_helpers())
    results.append(test_main_window_with_services())
    
    print("\n=== v1.9.2 冒烟测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("=== v1.9.2 冒烟测试全部通过 ===")
        return 0
    else:
        print("!!! v1.9.2 冒烟测试失败 !!!")
        return 1

if __name__ == "__main__":
    sys.exit(main())