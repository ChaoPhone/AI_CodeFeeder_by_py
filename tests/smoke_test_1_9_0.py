"""
v1.9.0 冒烟测试脚本
"""
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)

print('=== v1.9.0 冒烟测试 ===')
print()

print('[1] 测试 Core 模块导入...')
try:
    from Core import (
        ProjectManager, ScanCancelledError, ScanTimeoutError,
        clean_content_deeply, remove_license_header, is_junk_filename,
        Config, load_config, get_config_path, read_config_text, save_config_text,
        RuntimeBootstrapper, ErrorHandler, ThreadManager
    )
    print('    OK Core 模块导入成功')
except Exception as e:
    print(f'    FAIL Core 模块导入失败: {e}')
    sys.exit(1)

print()
print('[2] 测试 AppUI 模块导入...')
try:
    from AppUI import (
        CodeFeederApp, COLORS, FONTS,
        RoundedFrame, TagCloudFrame,
        TreeBuilder, AppState,
        ScanController, GenerateController, SettingsController
    )
    print('    OK AppUI 模块导入成功')
except Exception as e:
    print(f'    FAIL AppUI 模块导入失败: {e}')
    sys.exit(1)

print()
print('[3] 测试 AppState 初始化...')
try:
    state = AppState()
    print(f'    OK AppState 创建成功: is_topmost={state.is_topmost}')
    cancel_event = state.create_cancel_event()
    print(f'    OK create_cancel_event 成功: event={cancel_event}')
except Exception as e:
    print(f'    FAIL AppState 测试失败: {e}')
    sys.exit(1)

print()
print('[4] 测试 ErrorHandler...')
try:
    ErrorHandler.setup()
    print('    OK ErrorHandler.setup 成功')
except Exception as e:
    print(f'    FAIL ErrorHandler 测试失败: {e}')
    sys.exit(1)

print()
print('[5] 测试 ThreadManager...')
try:
    ThreadManager.cleanup_finished()
    print('    OK ThreadManager.cleanup_finished 成功')
except Exception as e:
    print(f'    FAIL ThreadManager 测试失败: {e}')
    sys.exit(1)

print()
print('[6] 测试 Config 加载...')
try:
    cfg = load_config()
    print(f'    OK Config 加载成功: allowed_exts={len(cfg.allowed_exts)} 个')
except Exception as e:
    print(f'    FAIL Config 加载失败: {e}')
    sys.exit(1)

print()
print('[7] 测试 ScanController 初始化...')
try:
    manager = ProjectManager(cfg)
    state = AppState()
    controller = ScanController(manager, state)
    print(f'    OK ScanController 创建成功')
except Exception as e:
    print(f'    FAIL ScanController 测试失败: {e}')
    sys.exit(1)

print()
print('[8] 测试 GenerateController 初始化...')
try:
    gen_controller = GenerateController(manager, state, cfg)
    print(f'    OK GenerateController 创建成功')
except Exception as e:
    print(f'    FAIL GenerateController 测试失败: {e}')
    sys.exit(1)

print()
print('[9] 测试 SettingsController 初始化...')
try:
    settings_controller = SettingsController(state)
    data = settings_controller.load_config_data()
    mode = data.get('default_mode', 'unknown')
    print(f'    OK SettingsController 创建成功: default_mode={mode}')
except Exception as e:
    print(f'    FAIL SettingsController 测试失败: {e}')
    sys.exit(1)

print()
print('=== v1.9.0 冒烟测试全部通过 ===')