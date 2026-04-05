"""
运行时引导器 - 仅用于源码模式
处理依赖检测、site-packages 刷新、异常捕获
exe 模式下此模块会被跳过
"""
import datetime
import importlib
import importlib.util
import os
import site
import sys
import traceback
from dataclasses import dataclass


@dataclass(frozen=True)
class DependencySpec:
    package: str
    module: str
    label: str
    reason: str
    dep_type: str = "module"


@dataclass
class DependencyStatus:
    spec: DependencySpec
    state: str
    error: str = ""

    @property
    def ok(self):
        return self.state == "available"


DEPENDENCY_SPECS = [
    DependencySpec(
        package="pywin32",
        module="win32api",
        label="pywin32",
        reason="资源管理器联动、开机自启和 Windows 集成功能",
        dep_type="pywin32",
    ),
    DependencySpec(
        package="keyboard",
        module="keyboard",
        label="keyboard",
        reason="全局快捷键 Ctrl+`",
    ),
    DependencySpec(
        package="pystray",
        module="pystray",
        label="pystray",
        reason="系统托盘",
    ),
    DependencySpec(
        package="Pillow",
        module="PIL",
        label="Pillow",
        reason="托盘图标与图片资源",
    ),
]


class RuntimeBootstrapper:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.log_file = os.path.join(project_dir, "launch_error.log")

    def log_error(self, message):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def install_exception_hook(self):
        def exception_hook(exctype, value, tb):
            if issubclass(exctype, KeyboardInterrupt):
                self.log_error("Process interrupted by KeyboardInterrupt")
                sys.exit(0)

            if issubclass(exctype, SystemExit):
                raise value

            error_msg = "".join(traceback.format_exception(exctype, value, tb))
            self.log_error(f"Uncaught exception:\n{error_msg}")

            try:
                import tkinter as tk
                import tkinter.messagebox

                root = tk.Tk()
                root.withdraw()
                tkinter.messagebox.showerror(
                    "CodeFeeder Error",
                    f"启动发生错误，请查看日志:\n{self.log_file}\n\n{value}"
                )
                root.destroy()
            except Exception:
                pass
            sys.exit(1)

        sys.excepthook = exception_hook

    def module_available(self, module_name):
        try:
            return importlib.util.find_spec(module_name) is not None
        except Exception:
            return False

    def get_site_packages_paths(self):
        """获取当前环境中的 site-packages 路径"""
        seen = set()
        paths = []
        in_venv = self._in_virtualenv()
        current_prefix = os.path.normcase(os.path.normpath(sys.prefix))

        for path in site.getsitepackages():
            norm_path = os.path.normcase(os.path.normpath(path))
            if in_venv and not norm_path.startswith(current_prefix):
                continue
            if norm_path not in seen and os.path.exists(path):
                seen.add(norm_path)
                paths.append(path)

        return paths

    def _in_virtualenv(self):
        return getattr(sys, "base_prefix", sys.prefix) != sys.prefix or hasattr(sys, "real_prefix")

    def refresh_site_packages(self):
        """刷新 site-packages 并确保 pywin32 可用"""
        for path in self.get_site_packages_paths():
            site.addsitedir(path)

        self._augment_pywin32_paths()
        importlib.invalidate_caches()

    def _augment_pywin32_paths(self):
        """处理 pywin32 的 DLL 路径"""
        dll_handles = []
        for base_path in self.get_site_packages_paths():
            for relative in ("win32", os.path.join("win32", "lib"), "Pythonwin", "pywin32_system32"):
                candidate = os.path.join(base_path, relative)
                if not os.path.exists(candidate):
                    continue

                if candidate not in sys.path:
                    sys.path.append(candidate)

                if relative == "pywin32_system32":
                    os.environ["PATH"] = candidate + os.pathsep + os.environ.get("PATH", "")
                    if hasattr(os, "add_dll_directory"):
                        try:
                            dll_handles.append(os.add_dll_directory(candidate))
                        except Exception:
                            pass
        return dll_handles

    def verify_pywin32_available(self):
        dll_handles = self._augment_pywin32_paths()
        try:
            importlib.invalidate_caches()
            importlib.import_module("win32api")
            importlib.import_module("win32con")
            importlib.import_module("win32com.client")
            return True, ""
        except Exception as e:
            self.log_error(f"pywin32 verify failed: {e}")
            return False, str(e)
        finally:
            for h in dll_handles:
                try:
                    h.close()
                except Exception:
                    pass

    def pywin32_files_present(self):
        for base_path in self.get_site_packages_paths():
            markers = [
                os.path.join(base_path, "pywin32.pth"),
                os.path.join(base_path, "win32", "win32api.pyd"),
            ]
            if any(os.path.exists(m) for m in markers):
                return True
        return False

    def get_dependency_status(self, spec):
        if spec.dep_type == "pywin32":
            ok, error_text = self.verify_pywin32_available()
            if ok:
                return DependencyStatus(spec=spec, state="available")
            state = "installed_but_unloadable" if self.pywin32_files_present() else "missing"
            return DependencyStatus(spec=spec, state=state, error=error_text)

        is_available = self.module_available(spec.module)
        return DependencyStatus(spec=spec, state="available" if is_available else "missing")

    def get_missing_statuses(self):
        statuses = [self.get_dependency_status(spec) for spec in DEPENDENCY_SPECS]
        return [s for s in statuses if not s.ok]

    def get_pip_executable(self):
        executable = sys.executable
        if executable.lower().endswith("pythonw.exe"):
            candidate = executable[:-5] + ".exe"
            if os.path.exists(candidate):
                return candidate
        return executable

    def run_pip_command(self, args):
        import subprocess
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        output, _ = process.communicate()
        return process.returncode, output

    def install_packages(self, package_args):
        import subprocess
        python_exe = self.get_pip_executable()
        install_cmd = [python_exe, "-m", "pip", "install", "--disable-pip-version-check", "--no-input"]
        install_cmd.extend(package_args)

        if not self._in_virtualenv():
            install_cmd.append("--user")

        returncode, output = self.run_pip_command(install_cmd)
        if returncode == 0:
            return True, output

        if "No module named pip" in output:
            ensure_code, _ = self.run_pip_command([python_exe, "-m", "ensurepip", "--upgrade"])
            if ensure_code == 0:
                returncode, output = self.run_pip_command(install_cmd)
                return (returncode == 0), output

        return False, output

    def repair_dependencies(self, missing_statuses):
        packages = [s.spec.package for s in missing_statuses if s.state == "missing"]
        broken_pywin32 = [s for s in missing_statuses if s.spec.package == "pywin32" and s.state == "installed_but_unloadable"]

        if packages:
            success, output = self.install_packages(packages)
            if not success:
                return False, output

        for s in broken_pywin32:
            success, output = self.install_packages(["--force-reinstall", "--no-cache-dir", s.spec.package])
            if not success:
                return False, output

        self.refresh_site_packages()
        return True, ""

    def build_missing_summary(self, missing_statuses):
        return ", ".join(
            f"{s.spec.label}({'已安装但不可用' if s.state == 'installed_but_unloadable' else '缺失'})"
            for s in missing_statuses
        )