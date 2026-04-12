"""
v1.9.1 冒烟测试 - 控制器分离验证
测试 MainWindow 与 AppState、Controllers 的集成
"""
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

def test_main_window_import():
    print("[1] 测试 MainWindow 模块导入...")
    try:
        from AppUI.MainWindow import CodeFeederApp
        print("    OK MainWindow 模块导入成功")
        return True
    except Exception as e:
        print(f"    FAIL 导入失败: {e}")
        return False

def test_state_integration():
    print("[2] 测试 AppState 集成...")
    try:
        from AppUI.models import AppState
        state = AppState()
        state.set_path("/test/path", "manual")
        state.set_output_mode("gap")
        state.toggle_whitelist_mode()
        state.toggle_topmost()
        print(f"    OK AppState 集成成功: target_dir={state.target_dir}, output_mode={state.output_mode}")
        return True
    except Exception as e:
        print(f"    FAIL AppState 集成失败: {e}")
        return False

def test_scan_controller_methods():
    print("[3] 测试 ScanController 方法...")
    try:
        from Core.ConfigLoader import load_config
        from Core.Analyzer import ProjectManager
        from AppUI.models import AppState
        from AppUI.controllers import ScanController
        
        cfg = load_config()
        manager = ProjectManager(cfg)
        state = AppState()
        
        controller = ScanController(
            manager, state,
            on_complete=lambda r: None,
            on_error=lambda m: None,
            on_progress=lambda m: None
        )
        
        result = controller.get_scan_summary({"cancelled": True, "files": []})
        print(f"    OK ScanController 方法测试成功: summary='{result}'")
        return True
    except Exception as e:
        print(f"    FAIL ScanController 方法测试失败: {e}")
        return False

def test_generate_controller_methods():
    print("[4] 测试 GenerateController 方法...")
    try:
        from Core.ConfigLoader import load_config
        from Core.Analyzer import ProjectManager
        from AppUI.models import AppState
        from AppUI.controllers import GenerateController
        
        cfg = load_config()
        manager = ProjectManager(cfg)
        state = AppState()
        
        controller = GenerateController(
            manager, state, cfg,
            on_success=lambda p, t, s: None,
            on_error=lambda m: None,
            on_progress=lambda p: None
        )
        
        path = controller.build_output_path("/test/project", "gap")
        can_gen = controller.can_generate()
        print(f"    OK GenerateController 方法测试成功: path='{path}', can_generate={can_gen}")
        return True
    except Exception as e:
        print(f"    FAIL GenerateController 方法测试失败: {e}")
        return False

def test_settings_controller_methods():
    print("[5] 测试 SettingsController 方法...")
    try:
        from AppUI.models import AppState
        from AppUI.controllers import SettingsController
        
        state = AppState()
        controller = SettingsController(
            state,
            on_config_changed=lambda: None,
            on_status_update=lambda m: None
        )
        
        data = controller.load_config_data()
        print(f"    OK SettingsController 方法测试成功: default_mode={data.get('default_mode', 'unknown')}")
        return True
    except Exception as e:
        print(f"    FAIL SettingsController 方法测试失败: {e}")
        return False

def test_state_selection_methods():
    print("[6] 测试 AppState 选择方法...")
    try:
        from AppUI.models import AppState
        
        state = AppState()
        state.all_files_map = {
            "file1.py": "/path/file1.py",
            "file2.py": "/path/file2.py",
            "folder/file3.py": "/path/folder/file3.py"
        }
        state.selection_state = {
            "file1.py": True,
            "file2.py": False,
            "folder/file3.py": True
        }
        
        selected = state.get_selected_files()
        new_state = state.toggle_file_selection("file1.py")
        folder_state = state.toggle_folder_selection("folder")
        
        print(f"    OK AppState 选择方法测试成功: selected_count={len(selected)}, toggle_file={new_state}")
        return True
    except Exception as e:
        print(f"    FAIL AppState 选择方法测试失败: {e}")
        return False

def test_state_folder_methods():
    print("[7] 测试 AppState 文件夹方法...")
    try:
        from AppUI.models import AppState
        
        state = AppState()
        state.collapse_folder("folder1")
        is_collapsed = state.is_folder_collapsed("folder1")
        state.expand_folder("folder1")
        is_collapsed_after = state.is_folder_collapsed("folder1")
        
        print(f"    OK AppState 文件夹方法测试成功: collapsed={is_collapsed}, after_expand={is_collapsed_after}")
        return True
    except Exception as e:
        print(f"    FAIL AppState 文件夹方法测试失败: {e}")
        return False

def main():
    print("=== v1.9.1 冒烟测试 ===\n")
    
    results = []
    results.append(test_main_window_import())
    results.append(test_state_integration())
    results.append(test_scan_controller_methods())
    results.append(test_generate_controller_methods())
    results.append(test_settings_controller_methods())
    results.append(test_state_selection_methods())
    results.append(test_state_folder_methods())
    
    print("\n=== v1.9.1 冒烟测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("=== v1.9.1 冒烟测试全部通过 ===")
        return 0
    else:
        print("!!! v1.9.1 冒烟测试失败 !!!")
        return 1

if __name__ == "__main__":
    sys.exit(main())