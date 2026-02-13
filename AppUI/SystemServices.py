import os
import sys
import win32api
import win32con

class StartupService:
    # 获取脚本绝对路径（更可靠）
    @staticmethod
    def _get_app_path():
        # 如果是冻结的EXE（PyInstaller等）
        if getattr(sys, 'frozen', False):
            return sys.executable
        
        # 否则是Python脚本，需要找到正确的入口文件
        # 优先使用 __file__ 的上级目录中的 CodeFeeder.pyw
        try:
            # 从 SystemServices.py 的位置推算
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            main_script = os.path.join(current_dir, "CodeFeeder.pyw")
            if os.path.exists(main_script):
                return main_script
            
            # 备选：CodeFeeder.py
            main_script = os.path.join(current_dir, "CodeFeeder.py")
            if os.path.exists(main_script):
                return main_script
        except:
            pass
        
        # 最后的备选：sys.argv[0]
        return os.path.abspath(sys.argv[0])

    @staticmethod
    def _build_command():
        app_path = StartupService._get_app_path()
        
        # 确保使用 pythonw.exe 运行（无窗口）
        if app_path.endswith('.py') or app_path.endswith('.pyw'):
            # 找到正确的 pythonw.exe
            python_dir = os.path.dirname(sys.executable)
            pythonw_exe = os.path.join(python_dir, "pythonw.exe")
            
            # 如果 pythonw.exe 不存在，尝试替换
            if not os.path.exists(pythonw_exe) and sys.executable.endswith("python.exe"):
                pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
            
            # 如果还是不存在，就用 sys.executable
            if not os.path.exists(pythonw_exe):
                pythonw_exe = sys.executable
                
            return f'"{pythonw_exe}" "{app_path}"'
        else:
            # EXE 直接运行
            return f'"{app_path}"'

    @staticmethod
    def is_startup_enabled():
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                0, 
                win32con.KEY_READ
            )
            win32api.RegQueryValueEx(key, "AICodeFeeder")
            win32api.RegCloseKey(key)
            return True
        except:
            return False

    @staticmethod
    def toggle_startup(enabled):
        cmd = StartupService._build_command()
        print(f"调试：准备写入注册表的命令 = {cmd}")  # 调试输出
        
        try:
            key = win32api.RegOpenKeyEx(
                win32con.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                0, 
                win32con.KEY_SET_VALUE
            )
            if enabled:
                win32api.RegSetValueEx(key, "AICodeFeeder", 0, win32con.REG_SZ, cmd)
                print(f"✅ 已添加开机自启: {cmd}")
            else:
                try:
                    win32api.RegDeleteValue(key, "AICodeFeeder")
                    print("✅ 已移除开机自启")
                except:
                    pass
            win32api.RegCloseKey(key)
            return True
        except Exception as e:
            print(f"❌ 设置自启动失败: {e}")
            import traceback
            traceback.print_exc()  # 打印完整错误堆栈
            return False