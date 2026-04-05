"""
依赖引导对话框 - 仅用于源码模式
当检测到依赖缺失时，弹窗提示用户安装
"""
import threading
import tkinter as tk
from tkinter import ttk, messagebox


class DependencyBootstrapDialog:
    def __init__(self, bootstrapper, missing_statuses):
        self.bootstrapper = bootstrapper
        self.missing_statuses = missing_statuses
        self.root = tk.Tk()
        self.root.title("AI CodeFeeder - 启动自检")
        self.root.geometry("560x330")
        self.root.resizable(False, False)
        self.root.configure(bg="#181818")
        self.root.protocol("WM_DELETE_WINDOW", self._on_skip)

        self.result = "pending"
        self.install_error = ""

        self.status_var = tk.StringVar(value="启动自检未通过，检测到缺少运行依赖。")
        self.progress_var = tk.IntVar(value=0)

        self.install_btn = None
        self.skip_btn = None
        self.progress_bar = None

        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self.root, bg="#181818", padx=24, pady=22)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="启动自检",
            bg="#181818",
            fg="#FFFFFF",
            font=("Microsoft YaHei UI", 15, "bold"),
            anchor="w"
        ).pack(fill=tk.X)

        tk.Label(
            container,
            text="检测到以下依赖缺失，安装后可恢复完整功能：",
            bg="#181818",
            fg="#CCCCCC",
            font=("Microsoft YaHei UI", 10),
            anchor="w"
        ).pack(fill=tk.X, pady=(8, 12))

        list_frame = tk.Frame(container, bg="#1F1F1F", padx=14, pady=12)
        list_frame.pack(fill=tk.X)
        for status in self.missing_statuses:
            prefix = "缺失" if status.state == "missing" else "已安装但不可用"
            tk.Label(
                list_frame,
                text=f"• {status.spec.label}  [{prefix}]  用于：{status.spec.reason}",
                bg="#1F1F1F",
                fg="#CCCCCC",
                font=("Microsoft YaHei UI", 10),
                anchor="w",
                justify="left"
            ).pack(fill=tk.X, pady=2)

        tk.Label(
            container,
            textvariable=self.status_var,
            bg="#181818",
            fg="#A0A0A0",
            font=("Microsoft YaHei UI", 10),
            anchor="w",
            justify="left"
        ).pack(fill=tk.X, pady=(14, 10))

        self.progress_bar = ttk.Progressbar(
            container,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            length=500
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 16))

        btn_row = tk.Frame(container, bg="#181818")
        btn_row.pack(fill=tk.X)

        self.install_btn = tk.Button(
            btn_row,
            text="自动安装依赖",
            command=self._start_install,
            bg="#007ACC",
            fg="#FFFFFF",
            relief=tk.FLAT,
            activebackground="#0098FF",
            activeforeground="#FFFFFF",
            font=("Microsoft YaHei UI", 10, "bold"),
            cursor="hand2",
            padx=16,
            pady=7
        )
        self.install_btn.pack(side=tk.LEFT)

        self.skip_btn = tk.Button(
            btn_row,
            text="兼容模式启动",
            command=self._on_skip,
            bg="#2A2D2E",
            fg="#CCCCCC",
            relief=tk.FLAT,
            activebackground="#37373D",
            activeforeground="#FFFFFF",
            font=("Microsoft YaHei UI", 10),
            cursor="hand2",
            padx=16,
            pady=7
        )
        self.skip_btn.pack(side=tk.RIGHT)

    def _set_controls_enabled(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.install_btn.config(state=state)
        self.skip_btn.config(state=state)

    def _on_skip(self):
        self.result = "compatibility"
        self.root.destroy()

    def _start_install(self):
        self._set_controls_enabled(False)
        self.status_var.set("正在准备批量安装缺失依赖，请稍候...")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self):
        dep_names = [status.spec.label for status in self.missing_statuses]

        self.root.after(0, lambda: self._begin_bulk_install(dep_names))
        success, output = self.bootstrapper.repair_dependencies(self.missing_statuses)
        if not success:
            self.install_error = output
            failed_status = self.missing_statuses[0]
            self.root.after(0, lambda s=failed_status: self._on_install_failed(s))
            return

        self.root.after(0, self._begin_verify)
        self.root.after(0, self._mark_bulk_installed)

        self.result = "installed"
        self.root.after(250, self.root.destroy)

    def _begin_bulk_install(self, dep_names):
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)
        self.status_var.set(f"正在批量安装：{', '.join(dep_names)}")

    def _begin_verify(self):
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate")
        self.progress_var.set(85)
        self.status_var.set("安装完成，正在刷新模块路径并重新校验...")

    def _mark_bulk_installed(self):
        self.progress_var.set(100)
        self.status_var.set("依赖安装完成，准备启动主程序...")

    def _on_install_failed(self, failed_status):
        self.result = "failed"
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate")
        self._set_controls_enabled(True)
        self.skip_btn.config(text="关闭")
        self.status_var.set(f"{failed_status.spec.label} 安装失败，请检查网络或权限后重试。")
        messagebox.showerror(
            "依赖安装失败",
            f"{failed_status.spec.label} 安装失败。\n\n可尝试手动执行：\n"
            f"{self.bootstrapper.get_pip_executable()} -m pip install {failed_status.spec.package}\n\n"
            "详细输出已写入启动错误日志。"
        )
        self.bootstrapper.log_error(
            f"Dependency install failed for {failed_status.spec.package}:\n{self.install_error}"
        )

    def show(self):
        self.root.mainloop()
        return self.result