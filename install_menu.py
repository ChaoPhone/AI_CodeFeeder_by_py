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
    # 更健壮的 pythonw.exe 获取
    python_exe = sys.executable
    if python_exe.endswith("python.exe"):
        pythonw = python_exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            python_exe = pythonw
    
    # 获取脚本的可靠路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "CodeFeeder.pyw")
    if not os.path.exists(script_path):
        script_path = os.path.join(script_dir, "CodeFeeder.py")

    menu_name = "📂 使用 AI CodeFeeder 打开"
    # 注册范围：文件夹、目录背景（右键空白处）、所有文件
    reg_paths = [r"Directory\shell", r"Directory\Background\shell", r"*\shell"]
    key_name = "AI_CodeFeeder_Pipeline"

    # --- 1. 定义两个不同的命令 ---
    # 【右键菜单命令】：必须带 "%V" 以获取选中的目录
    context_menu_cmd = f'"{python_exe}" "{script_path}" "%V"'
    # 【开机自启命令】：绝不能带 "%V"
    startup_cmd = f'"{python_exe}" "{script_path}"'
    
    # 添加调试输出
    print(f"调试：安装时的自启命令 = {startup_cmd}")

    try:
        for base in reg_paths:
            key_path = f"{base}\\{key_name}"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, menu_name)
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, python_exe)

            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command") as key:
                # 修复点：这里使用 context_menu_cmd
                winreg.SetValue(key, "", winreg.REG_SZ, context_menu_cmd)

        print(f"✅ 成功！右键菜单已更新。\n指向脚本: {script_path}")
        
        # --- 添加开机自启动注册逻辑 ---
        try:
            startup_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key_path, 0, winreg.KEY_SET_VALUE) as key:
                # 修复点：这里使用 startup_cmd (去掉 %V)
                winreg.SetValueEx(key, "AICodeFeeder", 0, winreg.REG_SZ, startup_cmd)
            print("✅ 成功！已添加开机自启动。")
        except Exception as startup_e:
            print(f"⚠️ 开机自启动设置失败: {startup_e}")

    except Exception as e:
        print(f"❌ 注册失败: {e}")


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
