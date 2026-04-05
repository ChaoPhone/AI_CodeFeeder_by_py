"""
内置安装器 - 支持从 exe 内部注册右键菜单
用户只需下载一个 exe，首次运行时自动检测并提示注册
"""
import os
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox
import winreg


MENU_KEY = "AI_CodeFeeder_Pipeline"
STARTUP_NAME = "AICodeFeeder"


def is_frozen_exe():
    """检测是否为打包后的 exe"""
    return getattr(sys, 'frozen', False)


def get_exe_path():
    """获取当前 exe 或脚本路径"""
    if is_frozen_exe():
        return sys.executable
    return os.path.abspath(sys.argv[0])


def is_admin():
    """检测是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin(args=None):
    """以管理员权限重新运行"""
    exe_path = get_exe_path()
    params = args or []
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe_path, " ".join(params), None, 1
    )


def is_context_menu_registered():
    """检测右键菜单是否已注册"""
    reg_paths = [
        r"Directory\shell",
        r"Directory\Background\shell",
        r"*\shell",
    ]

    for base in reg_paths:
        key_path = f"{base}\\{MENU_KEY}"
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                winreg.QueryValue(key, "")
            return True
        except (FileNotFoundError, OSError):
            continue

    return False


def register_context_menu():
    """注册右键菜单（需要管理员权限）"""
    if not is_admin():
        run_as_admin(["--register-silent"])
        return False  # 当前进程退出，由新进程完成

    exe_path = get_exe_path()
    menu_name = "使用 AI CodeFeeder 打开"
    cmd_template = f'"{exe_path}"'

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
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, exe_path)

            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"{cmd_template} {arg}")

            success_count += 1
        except Exception as e:
            print(f"注册 {base} 失败: {e}")

    # 注册开机自启
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, STARTUP_NAME, 0, winreg.REG_SZ, cmd_template)
    except Exception:
        pass

    return success_count > 0


def unregister_context_menu():
    """卸载右键菜单（需要管理员权限）"""
    if not is_admin():
        run_as_admin(["--unregister-silent"])
        return False

    reg_paths = [
        r"Directory\shell",
        r"Directory\Background\shell",
        r"*\shell",
    ]

    for base in reg_paths:
        key_path = f"{base}\\{MENU_KEY}"
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command")
        except (FileNotFoundError, OSError):
            pass
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
        except (FileNotFoundError, OSError):
            pass

    # 移除开机自启
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, STARTUP_NAME)
    except (FileNotFoundError, OSError):
        pass

    return True


class FirstRunDialog:
    """首次运行提示对话框"""

    def __init__(self, parent=None):
        self.result = "skip"  # "register" | "skip"
        self._show_dialog(parent)

    def _show_dialog(self, parent):
        root = tk.Toplevel(parent) if parent else tk.Tk()
        if not parent:
            root.withdraw()

        root.title("AI CodeFeeder - 首次运行")
        root.geometry("480x280")
        root.resizable(False, False)
        root.configure(bg="#181818")

        # 居中显示
        root.update_idletasks()
        x = (root.winfo_screenwidth() - 480) // 2
        y = (root.winfo_screenheight() - 280) // 2
        root.geometry(f"+{x}+{y}")

        if parent:
            root.transient(parent)
            root.grab_set()

        container = tk.Frame(root, bg="#181818", padx=24, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="🚀 欢迎使用 AI CodeFeeder",
            bg="#181818",
            fg="#FFFFFF",
            font=("Microsoft YaHei UI", 16, "bold"),
            anchor="w"
        ).pack(fill=tk.X)

        tk.Label(
            container,
            text="\n检测到右键菜单尚未注册。\n\n注册后可：",
            bg="#181818",
            fg="#CCCCCC",
            font=("Microsoft YaHei UI", 10),
            anchor="w"
        ).pack(fill=tk.X)

        features = tk.Frame(container, bg="#181818")
        features.pack(fill=tk.X, pady=10)

        for text in ["• 右键文件夹/文件 → 快速打开", "• 快捷键 Ctrl+` → 随时唤起", "• 开机自动启动"]:
            tk.Label(features, text=text, bg="#181818", fg="#858585", font=("Microsoft YaHei UI", 10), anchor="w").pack(fill=tk.X)

        btn_row = tk.Frame(container, bg="#181818")
        btn_row.pack(fill=tk.X, pady=(20, 0))

        register_btn = tk.Button(
            btn_row,
            text="立即注册",
            command=lambda: self._on_register(root),
            bg="#007ACC",
            fg="#FFFFFF",
            relief=tk.FLAT,
            activebackground="#0098FF",
            font=("Microsoft YaHei UI", 11, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        )
        register_btn.pack(side=tk.LEFT)

        skip_btn = tk.Button(
            btn_row,
            text="稍后手动",
            command=lambda: self._on_skip(root),
            bg="#2A2D2E",
            fg="#CCCCCC",
            relief=tk.FLAT,
            activebackground="#37373D",
            font=("Microsoft YaHei UI", 10),
            cursor="hand2",
            padx=20,
            pady=8
        )
        skip_btn.pack(side=tk.RIGHT)

        root.mainloop() if not parent else root.wait_window(root)

    def _on_register(self, root):
        self.result = "register"
        root.destroy()

    def _on_skip(self, root):
        self.result = "skip"
        root.destroy()


def check_first_run_and_prompt(parent=None):
    """
    检测首次运行，提示注册
    返回 True 表示已注册或用户选择跳过，可继续运行
    返回 False 表示正在注册（需要重启）
    """
    if not is_frozen_exe():
        return True  # 源码模式不检测

    if is_context_menu_registered():
        return True  # 已注册

    dialog = FirstRunDialog(parent)

    if dialog.result == "register":
        success = register_context_menu()
        if success:
            messagebox.showinfo("注册成功", "右键菜单已注册成功！\n\n现在可以：\n• 右键任意文件夹/文件快速打开\n• 按 Ctrl+` 快捷键唤起")
            return True
        else:
            # 以管理员权限重新启动
            return False  # 当前进程会退出

    return True  # 用户选择跳过