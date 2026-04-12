"""
v1.9.6 冒烟测试 - 设置页面修复验证
测试配置加载、保存、默认值
"""
import sys
import os
import json
import tempfile
import shutil

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)


def test_config_default_values():
    print("[1] 测试配置默认值...")
    try:
        from Core.ConfigLoader import load_config, get_config_path
        
        config_path = get_config_path()
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data.get("default_mode") == "normal", f"default_mode 应为 normal，实际为 {data.get('default_mode')}"
        assert data.get("save_txt") == False, f"save_txt 应为 false，实际为 {data.get('save_txt')}"
        
        print(f"    OK 配置默认值正确")
        print(f"       default_mode={data.get('default_mode')}")
        print(f"       save_txt={data.get('save_txt')}")
        return True
    except Exception as e:
        print(f"    FAIL 配置默认值测试失败: {e}")
        return False


def test_config_load_save():
    print("[2] 测试配置加载与保存...")
    try:
        from Core.ConfigLoader import load_config, read_config_text, save_config_text, get_config_write_path
        
        write_path = get_config_write_path()
        backup_data = None
        
        if os.path.exists(write_path):
            with open(write_path, 'r', encoding='utf-8') as f:
                backup_data = f.read()
        
        test_config = {
            "allowed_extensions": [".py", ".txt"],
            "ignore_dirs": ["test_dir"],
            "ignore_files": [],
            "ignore_prefixes": [],
            "default_mode": "gap",
            "full_load_timeout_seconds": 10,
            "full_load_max_files": 5000,
            "save_txt": True,
            "version": ["test", "测试"]
        }
        
        save_config_text(json.dumps(test_config, ensure_ascii=False, indent=2))
        
        loaded_text = read_config_text()
        loaded_data = json.loads(loaded_text)
        
        assert loaded_data.get("default_mode") == "gap", "保存后读取 default_mode 不匹配"
        assert loaded_data.get("save_txt") == True, "保存后读取 save_txt 不匹配"
        assert loaded_data.get("full_load_timeout_seconds") == 10, "保存后读取 timeout 不匹配"
        
        if backup_data:
            with open(write_path, 'w', encoding='utf-8') as f:
                f.write(backup_data)
        elif os.path.exists(write_path):
            os.remove(write_path)
        
        print(f"    OK 配置加载与保存成功")
        return True
    except Exception as e:
        print(f"    FAIL 配置加载与保存测试失败: {e}")
        return False


def test_config_service():
    print("[3] 测试 ConfigService...")
    try:
        from Core.services.ConfigService import ConfigService, get_config_path, get_config_write_path
        
        path = ConfigService.get_path()
        assert os.path.exists(path), f"配置路径不存在: {path}"
        
        text = ConfigService.read_text()
        data = json.loads(text)
        assert "allowed_extensions" in data, "配置缺少 allowed_extensions"
        
        print(f"    OK ConfigService 测试成功")
        print(f"       path={path}")
        return True
    except Exception as e:
        print(f"    FAIL ConfigService 测试失败: {e}")
        return False


def test_config_validation():
    print("[4] 测试配置验证...")
    try:
        from Core.ConfigLoader import validate_config_data
        
        valid_config = {
            "allowed_extensions": [".py"],
            "ignore_dirs": [],
            "ignore_files": [],
            "ignore_prefixes": [],
            "version": ["v1.0"],
            "default_mode": "normal"
        }
        
        result = validate_config_data(valid_config)
        assert result is not None, "验证有效配置失败"
        
        invalid_config = {
            "allowed_extensions": ".py",
            "ignore_dirs": [],
            "ignore_files": [],
            "ignore_prefixes": [],
            "version": ["v1.0"]
        }
        
        try:
            validate_config_data(invalid_config)
            print(f"    FAIL 应拒绝无效配置（allowed_extensions 不是数组）")
            return False
        except ValueError:
            pass
        
        invalid_mode_config = {
            "allowed_extensions": [".py"],
            "ignore_dirs": [],
            "ignore_files": [],
            "ignore_prefixes": [],
            "version": ["v1.0"],
            "default_mode": "invalid_mode"
        }
        
        try:
            validate_config_data(invalid_mode_config)
            print(f"    FAIL 应拒绝无效 default_mode")
            return False
        except ValueError:
            pass
        
        print(f"    OK 配置验证测试成功")
        return True
    except Exception as e:
        print(f"    FAIL 配置验证测试失败: {e}")
        return False


def test_mainwindow_settings_methods():
    print("[5] 测试 MainWindow 设置方法存在性...")
    try:
        from AppUI.MainWindow import CodeFeederApp
        
        required_methods = [
            'open_settings',
            '_render_all_settings',
            '_reload_settings_from_file',
            '_save_settings_config',
            '_close_settings',
            '_collect_visual_data'
        ]
        
        for method in required_methods:
            assert hasattr(CodeFeederApp, method), f"缺少方法: {method}"
        
        removed_methods = [
            '_switch_settings_tab',
            '_update_settings_tab_visual',
            '_render_general_settings',
            '_render_scan_settings',
            '_render_perf_settings'
        ]
        
        for method in removed_methods:
            assert not hasattr(CodeFeederApp, method), f"应已删除方法: {method}"
        
        print(f"    OK MainWindow 设置方法检查成功")
        print(f"       保留方法: {len(required_methods)}")
        print(f"       已删除方法: {len(removed_methods)}")
        return True
    except Exception as e:
        print(f"    FAIL MainWindow 设置方法检查失败: {e}")
        return False


def test_settings_controller():
    print("[6] 测试 SettingsController...")
    try:
        import tkinter as tk
        from AppUI.controllers.SettingsController import SettingsController
        from AppUI.models.AppState import AppState
        
        root = tk.Tk()
        root.withdraw()
        
        state = AppState()
        
        controller = SettingsController(
            state=state,
            on_config_changed=lambda: None,
            on_status_update=lambda s, i: None
        )
        
        data = controller.load_config_data()
        assert isinstance(data, dict), "load_config_data 应返回 dict"
        
        test_window = tk.Toplevel(root)
        controller.create_vars(test_window)
        assert controller.settings_mode_var is not None, "settings_mode_var 未创建"
        assert controller.settings_save_txt_var is not None, "settings_save_txt_var 未创建"
        
        root.destroy()
        
        print(f"    OK SettingsController 测试成功")
        return True
    except Exception as e:
        print(f"    FAIL SettingsController 测试失败: {e}")
        return False


def test_full_module_import():
    print("[7] 测试完整模块导入...")
    try:
        from Core import Config, load_config, read_config_text, save_config_text
        from Core.services import ConfigService
        from AppUI import CodeFeederApp
        from AppUI.controllers import SettingsController
        from AppUI.models import AppState
        
        print("    OK 完整模块导入测试成功")
        return True
    except Exception as e:
        print(f"    FAIL 完整模块导入测试失败: {e}")
        return False


def main():
    print("=== v1.9.6 冒烟测试 ===\n")
    
    results = []
    results.append(test_config_default_values())
    results.append(test_config_load_save())
    results.append(test_config_service())
    results.append(test_config_validation())
    results.append(test_mainwindow_settings_methods())
    results.append(test_settings_controller())
    results.append(test_full_module_import())
    
    print("\n=== v1.9.6 冒烟测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("=== v1.9.6 冒烟测试全部通过 ===")
        return 0
    else:
        print("!!! v1.9.6 冒烟测试失败 !!!")
        return 1


if __name__ == "__main__":
    sys.exit(main())