"""
v1.9.5 冒烟测试 - 集成测试验证
测试各模块之间的集成与协作
"""
import sys
import os
import json
import threading
import time

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)


def test_app_state_integration():
    print("[1] 测试 AppState 与 Controllers 集成...")
    try:
        from AppUI.models.AppState import AppState
        from AppUI.controllers import ScanController, GenerateController, SettingsController
        from Core import Config, load_config
        
        state = AppState()
        config = load_config()
        
        from Core.Analyzer import ProjectManager
        manager = ProjectManager(config)
        
        scan_ctrl = ScanController(
            manager=manager,
            state=state,
            on_complete=lambda r: None,
            on_error=lambda e: None,
            on_progress=lambda s: None
        )
        
        gen_ctrl = GenerateController(
            manager=manager,
            state=state,
            config=config,
            on_success=lambda p, t, s: None,
            on_error=lambda e: None,
            on_progress=lambda p: None
        )
        
        settings_ctrl = SettingsController(
            state=state,
            on_config_changed=lambda: None,
            on_status_update=lambda s, i: None
        )
        
        state.toggle_whitelist_mode()
        state.set_output_mode('skeleton')
        
        print(f"    OK AppState 与 Controllers 集成成功")
        print(f"       whitelist_mode={state.whitelist_mode}")
        print(f"       output_mode={state.output_mode}")
        return True
    except Exception as e:
        print(f"    FAIL AppState 与 Controllers 集成失败: {e}")
        return False


def test_scan_cancel_integration():
    print("[2] 测试扫描取消机制...")
    try:
        from AppUI.models.AppState import AppState
        from Core import ThreadManager
        
        state = AppState()
        thread_mgr = ThreadManager()
        
        cancel_event = state.create_cancel_event()
        
        def long_task():
            for i in range(10):
                if cancel_event.is_set():
                    return
                time.sleep(0.1)
        
        thread = threading.Thread(target=long_task, daemon=True)
        thread.start()
        
        time.sleep(0.05)
        cancel_event.set()
        
        thread.join(timeout=0.5)
        
        if not thread.is_alive():
            print("    OK 扫描取消机制测试成功")
            return True
        else:
            print("    FAIL 取消后线程仍在运行")
            return False
    except Exception as e:
        print(f"    FAIL 扫描取消机制测试失败: {e}")
        return False


def test_config_flow_integration():
    print("[3] 测试配置流程集成...")
    try:
        from Core.services import ConfigService, validate_config_data
        
        raw_text = ConfigService.read_text()
        data = json.loads(raw_text)
        data = validate_config_data(data)
        
        config = ConfigService.load()
        
        if config.default_mode in ['normal', 'gap', 'skeleton']:
            print(f"    OK 配置流程集成成功: default_mode={config.default_mode}")
            return True
        else:
            print(f"    FAIL 配置流程结果不符合预期")
            return False
    except Exception as e:
        print(f"    FAIL 配置流程集成测试失败: {e}")
        return False


def test_code_cleaner_pipeline():
    print("[4] 测试代码清洗流水线...")
    try:
        from Core.CodeCleaner import clean_content_deeply, is_junk_filename
        
        test_files = {
            'test.py': """
import os
import sys
# This is a comment
def main():
    '''Docstring'''
    print("Hello")
    return 42
""",
            'test.cpp': """
#include <iostream>
// Comment
int main() {
    std::cout << "Hello" << std::endl;
    return 0;
}
""",
            'test.js': """
// JavaScript comment
function hello() {
    console.log("Hello");
}
""",
        }
        
        results = {}
        for filename, content in test_files.items():
            ext = os.path.splitext(filename)[1]
            if not is_junk_filename(filename):
                results[filename] = clean_content_deeply(content, ext, aggressive_mode=False)
        
        if all('import' not in r and '#include' not in r for r in results.values()):
            print("    OK 代码清洗流水线测试成功")
            return True
        else:
            print("    FAIL 清洗结果不符合预期")
            return False
    except Exception as e:
        print(f"    FAIL 代码清洗流水线测试失败: {e}")
        return False


def test_tree_builder_integration():
    print("[5] 测试 TreeBuilder 与 TreeView 集成...")
    try:
        from AppUI.Tree import TreeBuilder
        from AppUI.views import TreeView
        import tkinter as tk
        
        flat_files = [
            ("src/main.py", "/project/src/main.py"),
            ("src/utils.py", "/project/src/utils.py"),
            ("tests/test_main.py", "/project/tests/test_main.py"),
            ("README.md", "/project/README.md"),
        ]
        
        visual_items, collapsed = TreeBuilder.build_visual_data(flat_files)
        
        root = tk.Tk()
        scroll_frame = tk.Frame(root)
        
        tree_view = TreeView(
            scroll_frame,
            on_toggle_file=lambda p: None,
            on_toggle_folder=lambda p: None,
            on_toggle_collapse=lambda p: None
        )
        
        selection_state = {}
        all_files_map = {}
        
        tree_view.render_tree(flat_files, collapsed, selection_state, all_files_map, False)
        
        root.destroy()
        
        print(f"    OK TreeBuilder 与 TreeView 集成成功: items={len(visual_items)}")
        return True
    except Exception as e:
        print(f"    FAIL TreeBuilder 与 TreeView 集成失败: {e}")
        return False


def test_services_integration():
    print("[6] 测试服务层集成...")
    try:
        from AppUI.services import (
            SingleInstanceService,
            HotkeyService,
            TrayService,
            ExplorerService,
            StartupService,
        )
        
        instance_svc = SingleInstanceService()
        hotkey_svc = HotkeyService(lambda: None)
        explorer_svc = ExplorerService()
        startup_svc = StartupService()
        
        acquired = instance_svc.try_acquire()
        if acquired:
            instance_svc.release()
        
        print(f"    OK 服务层集成测试成功")
        return True
    except Exception as e:
        print(f"    FAIL 服务层集成测试失败: {e}")
        return False


def test_error_handler_integration():
    print("[7] 测试错误处理器集成...")
    try:
        from Core.error_handler import ErrorHandler
        
        handler = ErrorHandler()
        handler.setup()
        
        print("    OK 错误处理器集成测试成功")
        return True
    except Exception as e:
        print(f"    FAIL 错误处理器集成测试失败: {e}")
        return False


def test_full_module_import():
    print("[8] 测试完整模块导入...")
    try:
        from Core import (
            ProjectManager,
            ScanTimeoutError,
            ScanCancelledError,
            clean_content_deeply,
            remove_license_header,
            is_junk_filename,
            hollow_out_python_bodies,
            Config,
            load_config,
            get_config_path,
            read_config_text,
            save_config_text,
            RuntimeBootstrapper,
            ErrorHandler,
            ThreadManager,
            ConfigService,
            validate_config_data,
            get_appdata_dir,
            get_config_read_path,
            get_config_write_path,
        )
        
        from AppUI import (
            CodeFeederApp,
            COLORS,
            FONTS,
            RoundedFrame,
            TagCloudFrame,
            TreeBuilder,
            AppState,
            ScanController,
            GenerateController,
            SettingsController,
            SingleInstanceService,
            HotkeyService,
            TrayService,
            ExplorerService,
            StartupService,
        )
        
        from AppUI.views import TreeView
        
        print("    OK 完整模块导入测试成功")
        return True
    except Exception as e:
        print(f"    FAIL 完整模块导入测试失败: {e}")
        return False


def main():
    print("=== v1.9.5 冒烟测试 ===\n")
    
    results = []
    results.append(test_app_state_integration())
    results.append(test_scan_cancel_integration())
    results.append(test_config_flow_integration())
    results.append(test_code_cleaner_pipeline())
    results.append(test_tree_builder_integration())
    results.append(test_services_integration())
    results.append(test_error_handler_integration())
    results.append(test_full_module_import())
    
    print("\n=== v1.9.5 冒烟测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("=== v1.9.5 冒烟测试全部通过 ===")
        return 0
    else:
        print("!!! v1.9.5 冒烟测试失败 !!!")
        return 1


if __name__ == "__main__":
    sys.exit(main())