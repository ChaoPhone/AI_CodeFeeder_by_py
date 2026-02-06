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
    python_exe = sys.executable
    # 如果不想看到黑框，取消下面这行的注释:
    # python_exe = python_exe.replace("python.exe", "pythonw.exe")

    # ✨ 修改点：指向新的入口文件 CodeFeeder.py
    script_path = os.path.abspath("CodeFeeder.py")

    menu_name = "📂 使用 AI CodeFeeder 打开"
    reg_paths = [r"Directory\shell", r"Directory\Background\shell"]
    key_name = "AI_CodeFeeder_Pipeline"

    try:
        for base in reg_paths:
            key_path = f"{base}\\{key_name}"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, menu_name)
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, python_exe)

            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command") as key:
                # 传递 "%V" 参数
                cmd = f'"{python_exe}" "{script_path}" "%V"'
                winreg.SetValue(key, "", winreg.REG_SZ, cmd)

        print(f"✅ 成功！右键菜单已更新。\n指向脚本: {script_path}")

    except Exception as e:
        print(f"❌ 注册失败: {e}")


if __name__ == "__main__":
    # 检查入口文件是否存在
    if not os.path.exists("CodeFeeder.py"):
        print("❌ 错误：当前目录下找不到 CodeFeeder.py")
        input("按回车退出...")
        sys.exit(1)

    if is_admin():
        register_context_menu()
        input("\n按回车键退出...")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)