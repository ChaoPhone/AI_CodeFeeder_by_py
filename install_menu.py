import os
import sys
import winreg
import ctypes


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def register_context_menu():
    print("🔍 正在检测环境...")
    
    # 1. 判定是运行的脚本还是已编译好的 EXE
    if getattr(sys, 'frozen', False):
        # 如果是 EXE 模式运行
        exe_path = sys.executable
        # 寻找同目录下的 AICodeFeeder.exe (基于 build_exe.py 的命名)
        dist_dir = os.path.dirname(exe_path)
        script_path = os.path.join(dist_dir, "AICodeFeeder.exe")
        
        # 兜底：如果就是 AICodeFeeder.exe 运行的 (虽然通常是单独的安装器)
        if not os.path.exists(script_path):
            script_path = exe_path
            
        python_exe = "" # EXE 模式不需要 python 前缀
        cmd_template = f'"{script_path}"'
        icon_path = script_path
        print(f"✅ 检测到 EXE 模式运行: {script_path}")
    else:
        # 2. 如果是 Python 脚本模式运行
        python_exe = sys.executable
        if python_exe.lower().endswith("python.exe"):
            pythonw = python_exe[:-4] + "w.exe"
            if os.path.exists(pythonw):
                python_exe = pythonw
                print(f"✅ 已找到无窗口运行环境: {python_exe}")
            else:
                print(f"⚠️ 未找到 pythonw.exe，将使用 python.exe (会有控制台窗口)")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "CodeFeeder.pyw")
        if not os.path.exists(script_path):
            script_path = os.path.join(script_dir, "CodeFeeder.py")
        
        if not os.path.exists(script_path):
             print(f"❌ 严重错误：找不到脚本文件 CodeFeeder.pyw 或 CodeFeeder.py")
             return
             
        cmd_template = f'"{python_exe}" "{script_path}"'
        icon_path = python_exe

    menu_name = "📂 使用 AI CodeFeeder 打开"
    key_name = "AI_CodeFeeder_Pipeline"

    # 定义注册表路径和对应的参数
    reg_configs = [
        (r"Directory\shell", '"%V"'),
        (r"Directory\Background\shell", '"%V"'),
        (r"*\shell", '"%1"')
    ]

    # 【开机自启命令】：绝不能带 "%V" 或 "%1"
    startup_cmd = cmd_template
    
    print(f"调试：安装时的自启命令 = {startup_cmd}")

    try:
        success_count = 0
        for base, arg in reg_configs:
            key_path = f"{base}\\{key_name}"
            # 构建针对该类型的命令
            cmd_str = f'{cmd_template} {arg}'
            
            try:
                # 创建/打开主键
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, menu_name)
                    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)

                # 创建/打开 command 子键
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command") as key:
                    winreg.SetValue(key, "", winreg.REG_SZ, cmd_str)
                
                print(f"✅ 注册成功: {base} -> {cmd_str}")
                success_count += 1
            except Exception as e:
                print(f"❌ 注册失败 ({base}): {e}")


        if success_count > 0:
            print(f"\n✅ 右键菜单更新完成！(成功 {success_count}/{len(reg_configs)})")
        else:
            print("\n❌ 所有注册表项均写入失败，请检查权限或杀毒软件拦截。")
        
        # --- 添加开机自启动注册逻辑 ---
        try:
            startup_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AICodeFeeder", 0, winreg.REG_SZ, startup_cmd)
            print("✅ 成功！已添加开机自启动。")
        except Exception as startup_e:
            print(f"⚠️ 开机自启动设置失败: {startup_e}")

    except Exception as e:
        print(f"❌ 发生未预期的错误: {e}")


if __name__ == "__main__":
    # 检查入口文件是否存在
    if not os.path.exists("CodeFeeder.pyw"):
        print("❌ 错误：当前目录下找不到 CodeFeeder.pyw")
        input("按回车退出...")
        sys.exit(1)

    if is_admin():
        register_context_menu()
        input("\n按回车键退出...")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
