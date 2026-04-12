"""
v1.9.4 冒烟测试 - 逻辑完善验证
测试 CodeCleaner 增强、ConfigService 分离
"""
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

def test_code_cleaner_import():
    print("[1] 测试 CodeCleaner 模块导入...")
    try:
        from Core.CodeCleaner import (
            clean_content_deeply,
            remove_license_header,
            is_junk_filename,
            hollow_out_function_bodies,
            hollow_out_python_bodies,
            remove_python_docstring,
        )
        print("    OK CodeCleaner 模块导入成功")
        return True
    except Exception as e:
        print(f"    FAIL 导入失败: {e}")
        return False

def test_python_skeleton():
    print("[2] 测试 Python 骨架模式...")
    try:
        from Core.CodeCleaner import hollow_out_python_bodies
        
        test_code = """
def hello():
    print("world")
    return 42

class MyClass:
    def method(self):
        x = 1
        y = 2
        return x + y
"""
        
        result = hollow_out_python_bodies(test_code)
        
        if 'def hello():' in result and '...' in result:
            print("    OK Python 骨架模式测试成功")
            return True
        else:
            print(f"    FAIL 骨架模式结果不符合预期: {result[:100]}")
            return False
    except Exception as e:
        print(f"    FAIL Python 骨架模式测试失败: {e}")
        return False

def test_clean_content_deeply():
    print("[3] 测试深度清洗...")
    try:
        from Core.CodeCleaner import clean_content_deeply
        
        test_code = """
import os
# comment
def hello():
    print("world")
    return 42

class MyClass:
    def method(self):
        x = 1
        y = 2
        return x + y
"""
        
        result_gap = clean_content_deeply(test_code, '.py', aggressive_mode=False)
        result_skeleton = clean_content_deeply(test_code, '.py', aggressive_mode=True)
        
        if 'import' not in result_gap and '# comment' not in result_gap:
            print("    OK Gap 模式清洗测试成功")
        else:
            print(f"    FAIL Gap 模式清洗结果不符合预期")
            return False
        
        if '...' in result_skeleton and 'def hello():' in result_skeleton:
            print("    OK Skeleton 模式清洗测试成功")
            return True
        else:
            print(f"    FAIL Skeleton 模式清洗结果不符合预期")
            return False
    except Exception as e:
        print(f"    FAIL 深度清洗测试失败: {e}")
        return False

def test_config_service():
    print("[4] 测试 ConfigService...")
    try:
        from Core.services import ConfigService, Config, validate_config_data
        
        config = ConfigService.load()
        
        if hasattr(config, 'allowed_exts') and hasattr(config, 'default_mode'):
            print(f"    OK ConfigService.load 成功: exts_count={len(config.allowed_exts)}")
            return True
        else:
            print("    FAIL ConfigService.load 结果不符合预期")
            return False
    except Exception as e:
        print(f"    FAIL ConfigService 测试失败: {e}")
        return False

def test_config_service_methods():
    print("[5] 测试 ConfigService 方法...")
    try:
        from Core.services import ConfigService
        
        read_path = ConfigService.get_read_path()
        write_path = ConfigService.get_write_path()
        appdata_dir = ConfigService.get_appdata_dir()
        
        print(f"    OK ConfigService 方法测试成功")
        print(f"       read_path={read_path}")
        print(f"       write_path={write_path}")
        print(f"       appdata_dir={appdata_dir}")
        return True
    except Exception as e:
        print(f"    FAIL ConfigService 方法测试失败: {e}")
        return False

def test_junk_filename_filter():
    print("[6] 测试垃圾文件名过滤...")
    try:
        from Core.CodeCleaner import is_junk_filename
        
        junk_files = ['__init__.py', 'setup.py', 'test_main.py', 'main_test.py', 'stm32f4xx_it.c']
        normal_files = ['main.py', 'utils.py', 'app.py']
        
        for f in junk_files:
            if not is_junk_filename(f):
                print(f"    FAIL 垃圾文件未被过滤: {f}")
                return False
        
        for f in normal_files:
            if is_junk_filename(f):
                print(f"    FAIL 正常文件被误过滤: {f}")
                return False
        
        print("    OK 垃圾文件名过滤测试成功")
        return True
    except Exception as e:
        print(f"    FAIL 垃圾文件名过滤测试失败: {e}")
        return False

def test_core_exports():
    print("[7] 测试 Core 模块导出...")
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
        print("    OK Core 模块导出测试成功")
        return True
    except Exception as e:
        print(f"    FAIL Core 模块导出测试失败: {e}")
        return False

def main():
    print("=== v1.9.4 冒烟测试 ===\n")
    
    results = []
    results.append(test_code_cleaner_import())
    results.append(test_python_skeleton())
    results.append(test_clean_content_deeply())
    results.append(test_config_service())
    results.append(test_config_service_methods())
    results.append(test_junk_filename_filter())
    results.append(test_core_exports())
    
    print("\n=== v1.9.4 冒烟测试结果 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("=== v1.9.4 冒烟测试全部通过 ===")
        return 0
    else:
        print("!!! v1.9.4 冒烟测试失败 !!!")
        return 1

if __name__ == "__main__":
    sys.exit(main())