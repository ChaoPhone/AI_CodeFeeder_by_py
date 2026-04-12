"""
v1.9.3 冒烟测试 - 视图优化验证
测试 views 模块的 TreeView 组件
"""
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

def test_views_import():
    print("[1] 测试 views 模块导入...")
    try:
        from AppUI.views import TreeView
        print("    OK views 模块导入成功")
        return True
    except Exception as e:
        print(f"    FAIL 导入失败: {e}")
        return False

def test_tree_view_class():
    print("[2] 测试 TreeView 类...")
    try:
        from AppUI.views import TreeView
        import tkinter as tk
        
        root = tk.Tk()
        scroll_frame = tk.Frame(root)
        
        tree_view = TreeView(
            scroll_frame,
            on_toggle_file=lambda p: None,
            on_toggle_folder=lambda p: None,
            on_toggle_collapse=lambda p: None
        )
        
        print(f"    OK TreeView 创建成功: path_to_label_count={len(tree_view.path_to_label)}")
        root.destroy()
        return True
    except Exception as e:
        print(f"    FAIL TreeView 类测试失败: {e}")
        return False

def test_tree_view_methods():
    print("[3] 测试 TreeView 方法...")
    try:
        from AppUI.views import TreeView
        import tkinter as tk
        
        root = tk.Tk()
        scroll_frame = tk.Frame(root)
        
        tree_view = TreeView(
            scroll_frame,
            on_toggle_file=lambda p: None,
            on_toggle_folder=lambda p: None,
            on_toggle_collapse=lambda p: None
        )
        
        tree_view.clear()
        tree_view.show_message("测试消息")
        tree_view.show_loading("加载中...")
        
        print("    OK TreeView 方法测试成功: clear/show_message/show_loading")
        root.destroy()
        return True
    except Exception as e:
        print(f"    FAIL TreeView 方法测试失败: {e}")
        return False

def test_tree_builder_integration():
    print("[4] 测试 TreeBuilder 与 TreeView 集成...")
    try:
        from AppUI.Tree import TreeBuilder
        from AppUI.views import TreeView
        
        flat_files = [
            ("file1.py", "/path/file1.py"),
            ("folder/file2.py", "/path/folder/file2.py"),
        ]
        
        visual_items, collapsed = TreeBuilder.build_visual_data(flat_files)
        print(f"    OK TreeBuilder 集成成功: items_count={len(visual_items)}, collapsed_count={len(collapsed)}")
        return True
    except Exception as e:
        print(f"    FAIL TreeBuilder 集成测试失败: {e}")
        return False

def test_main_window_with_views():
    print("[5] 测试 MainWindow 与 views 模块...")
    try:
        from AppUI.MainWindow import CodeFeederApp
        print("    OK MainWindow 与 views 模块集成成功")
        return True
    except Exception as e:
        print(f"    FAIL MainWindow 与 views 模块集成失败: {e}")
        return False

def test_appui_exports():
    print("[6] 测试 AppUI 模块导出...")
    try:
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
        print("    OK AppUI 模块导出测试成功")
        return True
    except Exception as e:
        print(f"    FAIL AppUI 模块导出测试失败: {e}")
        return False

def main():
    print("=== v1.9.3 冒烟测试 ===\n")
    
    results = []
    results.append(test_views_import())
    results.append(test_tree_view_class())
    results.append(test_tree_view_methods())
    results.append(test_tree_builder_integration())
    results.append(test_main_window_with_views())
    results.append(test_appui_exports())
    
    print("\n=== v1.9.3 冒烟测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("=== v1.9.3 冒烟测试全部通过 ===")
        return 0
    else:
        print("!!! v1.9.3 冒烟测试失败 !!!")
        return 1

if __name__ == "__main__":
    sys.exit(main())