"""
AI CodeFeeder 主入口
支持两种运行模式：
1. 源码模式：自动检测并切换到 .venv，处理依赖
2. exe 模式：直接启动，内置首次运行注册检测
"""
import os
import sys
import subprocess

# Windows 高 DPI 感知 - 必须在创建任何 tkinter 窗口之前设置
# manifest 文件已处理 DPI，这里作为备用
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

import tkinter as tk

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)


def is_frozen_exe():
    """检测是否为打包后的 exe"""
    return getattr(sys, 'frozen', False)


def normalize_case_path(path):
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def get_venv_python_executable():
    """获取 .venv 中的 Python 解释器"""
    scripts_dir = os.path.join(PROJECT_DIR, ".venv", "Scripts")
    for exe_name in ("pythonw.exe", "python.exe"):
        candidate = os.path.join(scripts_dir, exe_name)
        if os.path.exists(candidate):
            return candidate
    return None


def is_runtime_isolated():
    return os.environ.get("AICF_RUNTIME_ISOLATED") == "1"


def ensure_venv_runtime():
    """源码模式：确保在 .venv 中运行"""
    if is_frozen_exe():
        return  # exe 模式跳过

    venv_python = get_venv_python_executable()
    target_python = venv_python or sys.executable

    current_python = normalize_case_path(sys.executable)
    desired_python = normalize_case_path(target_python)

    if current_python == desired_python and is_runtime_isolated():
        return

    relaunch_args = [target_python, "-s", os.path.abspath(__file__)]
    relaunch_args.extend(sys.argv[1:])
    child_env = os.environ.copy()
    child_env["PYTHONNOUSERSITE"] = "1"
    child_env["PYTHONUTF8"] = "1"
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["AICF_RUNTIME_ISOLATED"] = "1"

    subprocess.Popen(relaunch_args, cwd=PROJECT_DIR, env=child_env)
    sys.exit(0)


def resolve_launch_context():
    """解析启动参数"""
    init_path = None
    launch_source = "manual"

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        # 处理静默注册/卸载参数
        if arg == "--register-silent":
            from Core.Installer import register_context_menu
            register_context_menu()
            sys.exit(0)
        elif arg == "--unregister-silent":
            from Core.Installer import unregister_context_menu
            unregister_context_menu()
            sys.exit(0)

        # 处理路径参数
        if os.path.exists(arg):
            init_path = os.path.abspath(arg)
            launch_source = "arg"

    return init_path, launch_source


def bootstrap_source_mode():
    """源码模式的依赖检测与加载"""
    from Core.RuntimeBootstrap import RuntimeBootstrapper

    bootstrapper = RuntimeBootstrapper(PROJECT_DIR)
    bootstrapper.install_exception_hook()
    bootstrapper.refresh_site_packages()

    missing = bootstrapper.get_missing_statuses()
    if missing:
        from AppUI.BootstrapDialog import DependencyBootstrapDialog
        dialog = DependencyBootstrapDialog(bootstrapper, missing)
        result = dialog.show()

        if result == "installed":
            bootstrapper.refresh_site_packages()
            os.environ["AICF_BOOTSTRAP_WARNED"] = "1"
        elif result == "compatibility":
            os.environ["AICF_BOOTSTRAP_WARNED"] = "1"
        else:
            sys.exit(1)


def start_main_app(init_path=None, launch_source="manual", single_instance=None):
    """启动主应用"""
    from AppUI.MainWindow import CodeFeederApp

    root = tk.Tk()
    app = CodeFeederApp(root, init_path, launch_source=launch_source, single_instance=single_instance)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        try:
            root.destroy()
        except Exception:
            pass


def main():
    init_path, launch_source = resolve_launch_context()

    # 单实例检测必须在创建任何 Tk 窗口之前
    from AppUI.SystemServices import SingleInstanceService
    single_instance = SingleInstanceService()
    if not single_instance.try_acquire():
        # 已有实例运行，尝试激活并退出
        single_instance.notify_existing_instance()
        sys.exit(0)

    if is_frozen_exe():
        # exe 模式：简化启动流程
        from Core.Installer import check_first_run_and_prompt

        # 首次运行检测（需要先创建临时 root 以便显示对话框）
        temp_root = tk.Tk()
        temp_root.withdraw()

        if not check_first_run_and_prompt(temp_root):
            temp_root.destroy()
            single_instance.release()
            sys.exit(0)  # 正在注册，会重启

        temp_root.destroy()
        start_main_app(init_path, launch_source, single_instance)

    else:
        # 源码模式：完整的 venv 和依赖处理
        ensure_venv_runtime()
        bootstrap_source_mode()
        start_main_app(init_path, launch_source, single_instance)


if __name__ == "__main__":
    main()