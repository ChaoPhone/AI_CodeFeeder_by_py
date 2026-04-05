#!/usr/bin/env python3
"""
源码模式安装脚本
用于：创建虚拟环境、安装依赖、注册右键菜单、创建桌面快捷方式
"""
import argparse
import os
import shutil
import subprocess
import sys
import winreg
import ctypes

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(PROJECT_DIR, ".venv")
REQ_FILE = os.path.join(PROJECT_DIR, "requirements.txt")
APP_SCRIPT = os.path.join(PROJECT_DIR, "CodeFeeder.pyw")
MENU_KEY = "AI_CodeFeeder_Pipeline"
STARTUP_NAME = "AICodeFeeder"


def find_python():
    for cmd in ["py", "python", "python3"]:
        if shutil.which(cmd):
            return cmd
    return None


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin(args):
    script = os.path.abspath(__file__)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}" {" ".join(args)}', None, 1
    )


def get_installed_startup_cmd():
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(key, STARTUP_NAME)
            return value
    except Exception:
        return None


def get_current_version():
    config_path = os.path.join(PROJECT_DIR, "Core", "config.json")
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version", [""])[0]
        except Exception:
            pass
    return "unknown"


def ensure_venv():
    venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
    if os.path.exists(venv_python):
        print("[INFO] 虚拟环境已存在，跳过创建")
        return True

    python_cmd = find_python()
    if not python_cmd:
        print("[ERROR] 未找到 Python，请先安装 Python 3.x")
        return False

    print("[INFO] 创建虚拟环境 .venv ...")
    try:
        subprocess.run([python_cmd, "-m", "venv", VENV_DIR], check=True, capture_output=True)
        print("[SUCCESS] 虚拟环境创建成功")
        return True
    except Exception as e:
        print(f"[ERROR] 虚拟环境创建失败: {e}")
        return False


def install_dependencies():
    venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")

    print("[INFO] 升级 pip ...")
    subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)

    print("[INFO] 安装项目依赖 ...")
    result = subprocess.run(
        [venv_python, "-m", "pip", "install", "-r", REQ_FILE],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print("[ERROR] 依赖安装失败")
        print(result.stderr)
        return False

    print("[SUCCESS] 依赖安装完成")
    return True


def verify_dependencies():
    print("[INFO] 验证依赖导入 ...")
    venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
    check_cmd = [
        venv_python,
        "-c",
        "import win32api, keyboard, pystray; from PIL import Image; print('OK')",
    ]
    result = subprocess.run(
        check_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode == 0 and "OK" in result.stdout:
        print("[SUCCESS] 依赖验证通过")
        return True
    print("[ERROR] 依赖验证失败")
    print(result.stderr)
    return False


def find_venv_python():
    for exe in ("pythonw.exe", "python.exe"):
        path = os.path.join(VENV_DIR, "Scripts", exe)
        if os.path.exists(path):
            return path
    return None


def create_shortcut():
    """创建桌面快捷方式"""
    try:
        import win32com.client

        venv_python = find_venv_python()
        if not venv_python or not os.path.exists(APP_SCRIPT):
            return False

        shell = win32com.client.Dispatch("WScript.Shell")
        desktop = shell.SpecialFolders("Desktop")
        shortcut = shell.CreateShortCut(os.path.join(desktop, "AI CodeFeeder.lnk"))
        shortcut.TargetPath = venv_python
        shortcut.Arguments = f'"{APP_SCRIPT}"'
        shortcut.WorkingDirectory = PROJECT_DIR
        shortcut.Description = "AI CodeFeeder - 代码整理工具"
        shortcut.Save()

        print("[SUCCESS] 已创建桌面快捷方式")
        return True
    except Exception as e:
        print(f"[WARN] 创建快捷方式失败: {e}")
        return False


def register_menu():
    python_exe = find_venv_python() or sys.executable

    if not os.path.exists(APP_SCRIPT):
        print(f"[ERROR] 找不到应用入口: {APP_SCRIPT}")
        return False

    cmd_template = f'"{python_exe}" "{APP_SCRIPT}"'
    menu_name = "使用 AI CodeFeeder 打开"

    reg_configs = [
        (r"Directory\shell", '"%V"'),
        (r"Directory\Background\shell", '"%V"'),
        (r"*\shell", '"%1"'),
    ]

    success_count = 0
    for base, arg in reg_configs:
        try:
            key_path = f"{base}\\{MENU_KEY}"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, menu_name)
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, python_exe)

            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"{cmd_template} {arg}")

            print(f"[SUCCESS] 注册: {base}")
            success_count += 1
        except Exception as e:
            print(f"[ERROR] 注册 {base} 失败: {e}")

    if success_count == 0:
        print("[ERROR] 所有注册失败")
        return False

    # 开机自启
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, STARTUP_NAME, 0, winreg.REG_SZ, cmd_template)
        print("[SUCCESS] 开机自启已注册")
    except Exception as e:
        print(f"[WARN] 开机自启注册失败: {e}")

    print("[SUCCESS] 注册完成")
    return True


def unregister_menu():
    reg_paths = [r"Directory\shell", r"Directory\Background\shell", r"*\shell"]

    success_count = 0
    for base in reg_paths:
        try:
            key_path = f"{base}\\{MENU_KEY}"
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command")
            except FileNotFoundError:
                pass
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
            print(f"[SUCCESS] 移除: {base}")
            success_count += 1
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[ERROR] 移除 {base} 失败: {e}")

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        ) as key:
            try:
                winreg.DeleteValue(key, STARTUP_NAME)
                print("[SUCCESS] 开机自启已移除")
            except FileNotFoundError:
                print("[INFO] 未发现开机自启项")
    except Exception as e:
        print(f"[ERROR] 移除开机自启失败: {e}")

    if success_count > 0:
        print("[SUCCESS] 卸载完成")
    else:
        print("[INFO] 未发现已安装的菜单项")

    return True


def main():
    parser = argparse.ArgumentParser(description="AI CodeFeeder 源码安装工具")
    parser.add_argument(
        "--register",
        action="store_true",
        help="安装依赖并注册右键菜单、开机自启和桌面快捷方式",
    )
    parser.add_argument("--uninstall", action="store_true", help="卸载右键菜单和开机自启")
    parser.add_argument("--install-only", action="store_true", help="仅安装依赖，不注册")
    parser.add_argument("--verify", action="store_true", help="验证依赖是否正常")
    parser.add_argument("--shortcut", action="store_true", help="仅创建桌面快捷方式")
    args = parser.parse_args()

    if args.shortcut:
        create_shortcut()
        return

    if args.uninstall:
        if not is_admin():
            run_as_admin(["--uninstall"])
            return
        unregister_menu()
        return

    if args.verify:
        if verify_dependencies():
            sys.exit(0)
        else:
            sys.exit(1)

    if args.register:
        if not is_admin():
            run_as_admin(["--register"])
            return

        if not ensure_venv():
            sys.exit(1)
        if not install_dependencies():
            sys.exit(1)
        if not verify_dependencies():
            sys.exit(1)
        register_menu()
        create_shortcut()
        return

    # 默认：仅安装依赖
    if not ensure_venv():
        sys.exit(1)
    if not install_dependencies():
        sys.exit(1)
    verify_dependencies()

    print()
    print("[INFO] 安装完成，可选操作:")
    print("  python setup.py --register   # 注册右键菜单+开机自启+桌面快捷方式")
    print("  python setup.py --shortcut   # 仅创建桌面快捷方式")
    print("  python setup.py --verify     # 验证依赖是否正常")


if __name__ == "__main__":
    main()