"""
主窗口控制器 - 协调 UI 与后台服务
"""
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import shutil
import ctypes

from Core.ConfigLoader import load_config, read_config_text, save_config_text
from Core.Analyzer import ProjectManager
from Core.Installer import is_frozen_exe, is_context_menu_registered, register_context_menu
from .Tree import TreeBuilder
from .Theme import COLORS, FONTS
from .Views import MainView
from .Components import RoundedFrame, RoundedButton, TagCloudFrame
from .SystemServices import (
    set_win11_corners,
    SystemHotkeyService,
    SystemTrayService,
    StartupService,
    ExplorerService,
    get_missing_dependency_messages,
    get_missing_dependency_categories,
    get_dependency_debug_details,
    SingleInstanceService,
)


class CodeFeederApp:
    def __init__(self, root, initial_path=None, launch_source="manual", single_instance=None):
        self.root = root
        self.single_instance = single_instance  # 单实例锁
        self.cfg = load_config()
        self.manager = ProjectManager(self.cfg)

        self.root.title(f"AI CodeFeeder - {self._get_version_title()}")
        self.root.geometry("1400x1000")
        self.root.configure(bg=COLORS["bg_main"])

        # 状态变量
        self.is_topmost = False
        self.target_dir = os.path.abspath(os.path.normpath(initial_path)) if initial_path else None
        self.current_input_path = self.target_dir
        self.current_root_path = None
        self.last_path_source = launch_source
        self.scan_request_id = 0
        self.is_scanning = False
        self.status_reset_job = None
        self.scan_cancel_event = None  # 扫描取消信号

        self.all_files_map = {}
        self.selection_state = {}
        self.path_to_label = {}
        self.mode_var = tk.StringVar(value=self._sanitize_mode(self.cfg.default_mode))
        self.whitelist_mode = False
        self.progress_var = tk.IntVar(value=0)
        self.collapsed_folders = set()

        self.progress_bar = None
        self.status_label = None
        self.settings_summary_label = None
        self.settings_window = None
        self.ext_tag_cloud = None
        self.ignore_tag_cloud = None
        self.tray_available = False

        # 初始化系统服务
        self.hotkey_service = SystemHotkeyService(self._on_hotkey_triggered)
        self.tray_service = SystemTrayService(
            on_show=self._show_window,
            on_quit=self._quit_app,
            get_startup_status=StartupService.is_startup_enabled,
            toggle_startup=self._toggle_startup,
            on_register=self._register_from_tray
        )

        # 设置 Win11 视觉效果
        self.root.update()
        set_win11_corners(ctypes.windll.user32.GetParent(self.root.winfo_id()))

        # 构建 UI
        self.view = MainView(self.root, self)

        # 快捷引用
        self.path_entry = self.view.path_entry
        self.canvas = self.view.canvas
        self.scroll_frame = self.view.scroll_frame
        self.btn_gen = self.view.btn_gen

        # 启动服务
        self.hotkey_service.start()
        self.tray_available = self.tray_service.start()
        self._notify_missing_dependencies()

        # 事件绑定
        self.root.bind("<Return>", lambda e: self.on_generate_click())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close if self.tray_available else self._quit_app)

        # 初始路径加载
        if self.target_dir:
            self._update_path_display(self.target_dir)
            self.refresh_file_list()

        self.mode_var.trace_add("write", lambda *args: self._update_settings_summary())
        self._update_settings_summary()

    def _get_version_title(self):
        if self.cfg.version_info:
            return self.cfg.version_info[0]
        return "Unknown Version"

    def _notify_missing_dependencies(self):
        if os.environ.get("AICF_BOOTSTRAP_WARNED") == "1":
            return

        messages = get_missing_dependency_messages()
        if not messages:
            return

        self._set_status("部分功能已降级运行", reset_after_ms=6000)
        self.root.after(200, lambda: messagebox.showwarning(
            "依赖缺失",
            "程序已以降级模式启动。\n\n" + "\n".join(f"• {m}" for m in messages) +
            "\n\n如需完整功能，请安装相应依赖。"
        ))

    def _sanitize_mode(self, mode):
        return mode if mode in {"normal", "gap", "skeleton"} else "normal"

    def _get_mode_display_name(self):
        mode_map = {"normal": "普通", "gap": "简洁", "skeleton": "骨架"}
        return mode_map.get(self.mode_var.get(), "普通")

    def _update_settings_summary(self):
        if not self.settings_summary_label:
            return
        self.settings_summary_label.config(text=f"输出模式：{self._get_mode_display_name()}")

    def _set_status(self, message, reset_after_ms=None):
        if self.status_reset_job:
            self.root.after_cancel(self.status_reset_job)
            self.status_reset_job = None

        if self.status_label:
            self.status_label.config(text=message)

        if reset_after_ms:
            self.status_reset_job = self.root.after(reset_after_ms, lambda: self._set_status("就绪"))

    def _restore_generate_button(self):
        self.btn_gen.config(state=tk.NORMAL, text="🚀 生成 Markdown", bg=COLORS["accent"])

    def _set_scanning_state(self):
        self.btn_gen.config(state=tk.DISABLED, text="扫描中...", bg=COLORS["bg_hover"])

    def _clear_tree(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    def _show_tree_message(self, message):
        self._clear_tree()
        tk.Label(self.scroll_frame, text=message, bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(pady=40)

    def _show_tree_loading_placeholder(self, message):
        self._clear_tree()
        tk.Label(self.scroll_frame, text=message, bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(anchor="w", padx=30, pady=(24, 12))
        for width in (0.88, 0.74, 0.93, 0.68, 0.82):
            bar = tk.Frame(self.scroll_frame, bg=COLORS["bg_hover"], height=18)
            bar.pack(fill=tk.X, padx=30, pady=8)
            bar.pack_propagate(False)
            tk.Frame(bar, bg=COLORS["bg_selected"], width=int(920 * width), height=18).pack(anchor="w")

    def _reload_runtime_config(self, preserve_mode=True):
        current_mode = self.mode_var.get()
        self.cfg = load_config()
        self.manager = ProjectManager(self.cfg)
        self.root.title(f"AI CodeFeeder - {self._get_version_title()}")
        if preserve_mode:
            self.mode_var.set(self._sanitize_mode(current_mode))
        else:
            self.mode_var.set(self._sanitize_mode(self.cfg.default_mode))

    def toggle_topmost(self):
        """已移除置顶功能"""
        pass

    def toggle_whitelist_mode(self):
        self.whitelist_mode = not self.whitelist_mode
        if hasattr(self, "whitelist_btn"):
            if self.whitelist_mode:
                self.whitelist_btn.config(bg=COLORS["accent"], text="✓ 白名单")
            else:
                self.whitelist_btn.config(bg=COLORS["bg_hover"], text="白名单")

        new_default = not self.whitelist_mode
        for rel_path in self.selection_state:
            self.selection_state[rel_path] = new_default
        self._refresh_tree_visual()

    def _refresh_tree_visual(self):
        for rel_path in self.path_to_label:
            is_selected = self._get_visual_selected_state(rel_path)
            self._update_item_visual(rel_path, is_selected)

    def _get_visual_selected_state(self, rel_path):
        widgets = self.path_to_label.get(rel_path)
        if not widgets:
            return self.selection_state.get(rel_path, False)
        if widgets["is_file"]:
            return self.selection_state.get(rel_path, False)
        affected_files = [path for path in self.all_files_map if path.startswith(rel_path + os.sep)]
        if not affected_files:
            return False
        return any(self.selection_state.get(path, False) for path in affected_files)

    def _on_hotkey_triggered(self):
        self.root.after(0, self._handle_hotkey)

    def _handle_hotkey(self):
        path = ExplorerService.get_selected_path()
        self._show_window()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(100, lambda: self.root.attributes("-topmost", self.is_topmost))
        self.root.focus_force()

        if path and os.path.exists(path):
            self.last_path_source = "hotkey"
            self.target_dir = os.path.abspath(os.path.normpath(path))
            self._update_path_display(self.target_dir)
            self.refresh_file_list()
        else:
            messagebox.showinfo("快捷键触发", "已识别快捷键 Ctrl+`\n\n请确保当前已打开 Windows 资源管理器窗口，或选中了某个文件夹。")

    def _toggle_startup(self, icon, item):
        current_state = StartupService.is_startup_enabled()
        StartupService.toggle_startup(not current_state)

    def _register_from_tray(self):
        """从托盘菜单触发注册"""
        if not is_frozen_exe():
            messagebox.showinfo("提示", "此功能仅在 exe 模式下可用。")
            return

        success = register_context_menu()
        if success:
            messagebox.showinfo("注册成功", "右键菜单已注册成功！")
        else:
            messagebox.showinfo("注册中", "正在请求管理员权限完成注册...")

    def _show_window(self):
        self.root.after(0, self.root.deiconify)

    def _on_close(self):
        if self.tray_available:
            self.root.withdraw()
        else:
            self._quit_app()

    def _quit_app(self):
        self.tray_service.stop()
        # 释放单实例锁
        if self.single_instance:
            self.single_instance.release()
        self.root.after(0, self.root.destroy)

    def _update_path_display(self, path):
        self.path_entry.delete(0, tk.END)
        self.path_entry.config(fg=COLORS["fg_text"])
        self.path_entry.insert(0, path)

    def _on_path_focus_in(self, event):
        if self.path_entry.get() == "输入或选择项目路径...":
            self.path_entry.delete(0, tk.END)
            self.path_entry.config(fg=COLORS["fg_text"])

    def _on_path_focus_out(self, event):
        if not self.path_entry.get():
            self.path_entry.insert(0, "输入或选择项目路径...")
            self.path_entry.config(fg=COLORS["fg_secondary"])

    def on_path_entry_click(self, event=None):
        self.browse_dir()
        return "break"

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def browse_dir(self):
        selected_dir = filedialog.askdirectory()
        if selected_dir:
            self.last_path_source = "browse"
            self.target_dir = os.path.abspath(os.path.normpath(selected_dir))
            self._update_path_display(self.target_dir)
            self.refresh_file_list()

    def refresh_file_list(self):
        path = self.path_entry.get().strip()
        if not path or path == "输入或选择项目路径...":
            return

        norm_path = os.path.abspath(os.path.normpath(path))
        if not os.path.exists(norm_path):
            self.current_input_path = None
            self.current_root_path = None
            self._show_tree_message("路径不存在，请重新选择。")
            self._set_status("路径不存在。", reset_after_ms=4000)
            self._restore_generate_button()
            return

        # 取消之前的扫描
        if self.scan_cancel_event:
            self.scan_cancel_event.set()

        if norm_path != self.target_dir:
            self.last_path_source = "manual"
            self.target_dir = norm_path

        self.current_input_path = norm_path
        self.current_root_path = None
        self.all_files_map.clear()
        self.selection_state.clear()
        self.path_to_label.clear()
        self.collapsed_folders.clear()

        self.scan_request_id += 1
        scan_id = self.scan_request_id
        self.is_scanning = True

        # 创建新的取消信号
        self.scan_cancel_event = threading.Event()

        self._set_scanning_state()
        self._show_tree_loading_placeholder("正在预加载项目文件...")
        self._set_status(f"正在扫描，最多等待 {self.cfg.full_load_timeout_seconds} 秒...")

        threading.Thread(target=self._scan_thread, args=(norm_path, scan_id, self.scan_cancel_event), daemon=True).start()

    def _scan_thread(self, path, scan_id, cancel_event):
        try:
            result = self.manager.scan_directory(path, cancel_event)
            self.root.after(0, lambda: self._on_scan_complete(scan_id, result))
        except Exception as e:
            self.root.after(0, lambda: self._on_scan_error(scan_id, str(e)))

    def _on_scan_complete(self, scan_id, result):
        if scan_id != self.scan_request_id:
            return

        # 检查是否被取消
        if result.get("cancelled"):
            self.is_scanning = False
            self._show_tree_message("扫描已取消。")
            self._set_status("扫描已取消。", reset_after_ms=4000)
            self._restore_generate_button()
            return

        self.is_scanning = False
        self.current_input_path = result["requested_path"]
        self.current_root_path = result["root_path"]
        flat_files = result["files"]

        self._clear_tree()
        if not flat_files:
            self._show_tree_message("未找到相关代码文件。")
            self._set_status("扫描完成，但没有找到可加载文件。", reset_after_ms=5000)
            self._restore_generate_button()
            return

        default_selected = not self.whitelist_mode
        visual_items, auto_collapsed = TreeBuilder.build_visual_data(flat_files, self.collapsed_folders)
        self.collapsed_folders = auto_collapsed
        for item in visual_items:
            if item["type"] == "file":
                self.all_files_map[item["rel_path"]] = item["full_path"]
                self.selection_state[item["rel_path"]] = default_selected
            self._create_tree_row(item)

        collapsed_count = len(self.collapsed_folders)
        collapse_hint = f"，{collapsed_count} 个大文件夹已自动折叠" if collapsed_count > 0 else ""
        scan_mode_text = "全量加载" if result["used_full_load"] else "扩展名过滤加载"
        self._set_status(f"扫描完成，耗时 {result['elapsed']:.2f}s，共 {len(flat_files)} 个文件，{scan_mode_text}{collapse_hint}。", reset_after_ms=7000)
        self._restore_generate_button()

    def _on_scan_error(self, scan_id, message):
        if scan_id != self.scan_request_id:
            return
        self.is_scanning = False
        self._show_tree_message("扫描失败，请稍后重试。")
        self._set_status(f"扫描失败：{message}", reset_after_ms=7000)
        self._restore_generate_button()

    def _create_tree_row(self, item):
        is_file = (item["type"] == "file")
        rel_path = item.get("rel_path")
        is_collapsed = item.get("collapsed", False)
        level = rel_path.count(os.sep) if rel_path else 0

        # 限制最大缩进层级
        MAX_INDENT_LEVEL = 6
        display_level = min(level, MAX_INDENT_LEVEL)
        indent_px = display_level * 32

        name_text = item.get("name", item.get("original_name", ""))
        if level > MAX_INDENT_LEVEL:
            name_text = f".../{name_text}"

        row_frame = tk.Frame(self.scroll_frame, bg=COLORS["bg_panel"])
        row_frame.pack(fill=tk.X, pady=1)

        spacer = None
        if indent_px > 0:
            spacer = tk.Frame(row_frame, bg=COLORS["bg_panel"], width=indent_px, height=34)
            spacer.pack(side=tk.LEFT, fill=tk.Y)

        # 文件夹折叠展开按钮（独立于选择逻辑）
        collapse_btn = None
        if not is_file:
            collapse_char = "▸" if is_collapsed else "▾"
            collapse_btn = tk.Label(row_frame, text=collapse_char, bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"], font=("Segoe UI", 10), width=2, anchor="center", cursor="hand2")
            collapse_btn.pack(side=tk.LEFT)
            collapse_btn.bind("<Button-1>", lambda e: self._toggle_folder_collapse(rel_path))

        # 图标
        icon_char = "📄" if is_file else "📁"
        if is_file and name_text.endswith(".py"):
            icon_char = "🐍"
        icon_color = COLORS["icon_file"] if is_file else COLORS["icon_folder"]
        if not is_file and is_collapsed:
            icon_color = COLORS["fg_secondary"]

        icon_lbl = tk.Label(row_frame, text=icon_char, bg=COLORS["bg_panel"], fg=icon_color, font=("Segoe UI Emoji", 11), width=2, anchor="center")
        icon_lbl.pack(side=tk.LEFT)

        # 选择状态（与折叠逻辑解耦）
        is_selected = self._get_visual_selected_state(rel_path) if rel_path else True
        curr_font = FONTS["tree_norm"] if is_selected else FONTS["tree_strike"]
        curr_fg = COLORS["fg_text"] if is_selected else COLORS["text_ignore"]
        if not is_file and is_selected:
            curr_fg = COLORS["folder_fg"]

        # 使用 TreeBuilder 已生成的显示名称（包含折叠提示）
        # item["name"] 已包含折叠时的 "(N 文件已折叠...)" 提示，无需重复处理

        name_lbl = tk.Label(row_frame, text=name_text, bg=COLORS["bg_panel"], fg=curr_fg, font=curr_font, anchor="w")
        name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

        if rel_path:
            self.path_to_label[rel_path] = {"label": name_lbl, "frame": row_frame, "icon": icon_lbl, "spacer": spacer, "collapse_btn": collapse_btn, "is_file": is_file, "collapsed": is_collapsed}

        # 点击名称：文件切换选择，文件夹批量选择（与折叠解耦）
        def on_name_click(event):
            if is_file:
                self.on_toggle_file(rel_path)
            else:
                self.on_toggle_folder(rel_path)

        name_lbl.bind("<Button-1>", on_name_click)
        icon_lbl.bind("<Button-1>", on_name_click)

        def on_enter(event):
            for widget in [row_frame, name_lbl, icon_lbl, spacer, collapse_btn]:
                if widget:
                    widget.config(bg=COLORS["bg_hover"])

        def on_leave(event):
            for widget in [row_frame, name_lbl, icon_lbl, spacer, collapse_btn]:
                if widget:
                    widget.config(bg=COLORS["bg_panel"])

        for widget in [row_frame, name_lbl, spacer]:
            if widget:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

    def _toggle_folder_collapse(self, rel_path):
        """切换文件夹折叠状态（独立功能）"""
        if rel_path in self.collapsed_folders:
            self.collapsed_folders.discard(rel_path)
        else:
            self.collapsed_folders.add(rel_path)
        self._rerender_tree()

    def _rerender_tree(self):
        """重新渲染目录树"""
        if not self.all_files_map:
            return
        saved_selection = dict(self.selection_state)
        self._clear_tree()
        self.path_to_label.clear()

        flat_files = [(rel, full) for rel, full in self.all_files_map.items()]
        visual_items, _ = TreeBuilder.build_visual_data(flat_files, self.collapsed_folders)

        for item in visual_items:
            if item["type"] == "file":
                self.selection_state[item["rel_path"]] = saved_selection.get(item["rel_path"], True)
            self._create_tree_row(item)

    def on_toggle_file(self, rel_path):
        new_state = not self.selection_state[rel_path]
        self.selection_state[rel_path] = new_state
        self._update_item_visual(rel_path, new_state)

    def on_toggle_folder(self, rel_path):
        affected_files = [p for p in self.all_files_map if p.startswith(rel_path + os.sep) or p == rel_path]
        if not affected_files:
            return
        any_selected = any(self.selection_state.get(p, False) for p in affected_files)
        new_state = not any_selected
        for path in affected_files:
            self.selection_state[path] = new_state
            self._update_item_visual(path, new_state)
        if rel_path in self.path_to_label:
            self._update_item_visual(rel_path, new_state)

    def _update_item_visual(self, rel_path, is_selected):
        widgets = self.path_to_label.get(rel_path)
        if not widgets:
            return
        lbl = widgets["label"]
        icon_lbl = widgets["icon"]
        is_file = widgets["is_file"]

        if is_selected:
            icon_color = COLORS["icon_file"] if is_file else COLORS["icon_folder"]
            icon_lbl.config(fg=icon_color)
            lbl.config(font=FONTS["tree_norm"], fg=COLORS["fg_text"] if is_file else COLORS["folder_fg"])
        else:
            icon_lbl.config(fg=COLORS["text_ignore"])
            lbl.config(font=FONTS["tree_strike"], fg=COLORS["text_ignore"])

    def _build_output_path(self, input_path, mode):
        suffix_map = {"normal": "_Codes.md", "gap": "_Gap.md", "skeleton": "_Skeleton.md"}
        norm_path = os.path.abspath(os.path.normpath(input_path))

        if os.path.isdir(norm_path):
            parent_dir = os.path.dirname(norm_path)
            base_name = os.path.basename(norm_path)
        else:
            parent_dir = os.path.dirname(norm_path)
            base_name = os.path.splitext(os.path.basename(norm_path))[0]

        return os.path.join(parent_dir, f"{base_name}{suffix_map.get(mode, '_Codes.md')}")

    def on_generate_click(self):
        if self.is_scanning:
            messagebox.showinfo("请稍候", "正在扫描项目文件，请稍后再生成。")
            return

        input_path = self.current_input_path or self.path_entry.get().strip()
        if not input_path:
            return

        root_path = self.current_root_path
        if not root_path:
            if os.path.isdir(input_path):
                root_path = input_path
            elif os.path.isfile(input_path):
                root_path = os.path.dirname(input_path)
            else:
                return

        selected_items = [(rel_path, self.all_files_map[rel_path]) for rel_path, selected in self.selection_state.items() if selected]
        if not selected_items:
            messagebox.showwarning("提示", "请至少选择一个文件！")
            return

        mode = self.mode_var.get()
        out_path = self._build_output_path(input_path, mode)

        self.btn_gen.config(state=tk.DISABLED, text="处理中...", bg=COLORS["bg_hover"])
        self._set_status("正在生成输出文件...")

        if self.progress_bar:
            self.progress_bar.pack(side=tk.LEFT, padx=10)
            self.progress_var.set(0)

        ignored_rels = [rel_path for rel_path, selected in self.selection_state.items() if not selected]
        reveal_source = self.last_path_source

        def progress_callback(current, total, filename):
            percent = int((current / total) * 100) if total else 0
            self.root.after(0, lambda: self.progress_var.set(percent))

        threading.Thread(
            target=self._generate_thread,
            args=(root_path, selected_items, out_path, mode, ignored_rels, progress_callback, reveal_source),
            daemon=True
        ).start()

    def _generate_thread(self, root_path, items, out_path, mode, ignored_rels, progress_callback=None, reveal_source="manual"):
        try:
            char_count = self.manager.pipeline_write(root_path, items, out_path, mode, None, ignored_rels, progress_callback)
            # 如果配置中启用了同时生成 TXT
            if self.cfg.save_txt:
                shutil.copy2(out_path, os.path.splitext(out_path)[0] + ".txt")
            token_count = int(char_count / 3.5)
            self.root.after(0, lambda: self._on_success(out_path, token_count, reveal_source))
        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, path, token_count, reveal_source):
        self._restore_generate_button()
        if self.progress_bar:
            self.progress_bar.pack_forget()

        messagebox.showinfo("生成成功", f"文件已保存至：\n{path}\n\n📊 预估 Token 总数: {token_count}")

        reveal_ok = True
        if reveal_source == "browse":
            reveal_ok = ExplorerService.reveal_file_in_new_window(path)
        elif reveal_source in ("hotkey", "arg"):
            reveal_ok = ExplorerService.highlight_file_in_existing_window(path)

        if reveal_source in ("hotkey", "arg") and not reveal_ok:
            self._set_status("文件已生成。", reset_after_ms=5000)
        elif reveal_source == "browse":
            self._set_status("文件已生成，已在资源管理器中高亮。", reset_after_ms=6000)
        else:
            self._set_status("文件已生成。", reset_after_ms=5000)

        self._on_close()

    def _on_error(self, msg):
        self._restore_generate_button()
        if self.progress_bar:
            self.progress_bar.pack_forget()
        self._set_status(f"生成失败：{msg}", reset_after_ms=7000)
        messagebox.showerror("错误", msg)

    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("设置")
        self.settings_window.geometry("1000x750")
        self.settings_window.configure(bg=COLORS["bg_main"])
        self.settings_window.transient(self.root)
        self.settings_window.grab_set()
        self.settings_window.protocol("WM_DELETE_WINDOW", self._close_settings)

        self.settings_window.update()
        set_win11_corners(ctypes.windll.user32.GetParent(self.settings_window.winfo_id()))

        # 加载配置数据
        self.temp_config_data = json.loads(read_config_text())
        self.settings_mode_var = tk.StringVar(value=self.temp_config_data.get("default_mode", "normal"))
        self.settings_timeout_var = tk.StringVar(value=str(self.temp_config_data.get("full_load_timeout_seconds", 5)))
        self.settings_max_files_var = tk.StringVar(value=str(self.temp_config_data.get("full_load_max_files", 2500)))
        self.settings_save_txt_var = tk.BooleanVar(value=self.temp_config_data.get("save_txt", False))
        self.settings_tab_var = tk.StringVar(value="general")

        # 底部按钮栏（先 pack，固定在底部）
        btn_bar = tk.Frame(self.settings_window, bg=COLORS["bg_panel"], height=50)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM)
        btn_bar.pack_propagate(False)

        btn_inner = tk.Frame(btn_bar, bg=COLORS["bg_panel"], padx=24, pady=12)
        btn_inner.pack(fill=tk.BOTH, expand=True)

        tk.Button(btn_inner, text="重新载入", command=self._reload_settings_from_file, bg=COLORS["bg_hover"], fg=COLORS["fg_text"], relief=tk.FLAT, activebackground=COLORS["bg_selected"], activeforeground=COLORS["fg_heading"], font=FONTS["ui"], cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_inner, text="保存配置", command=self._save_settings_config, bg=COLORS["accent"], fg=COLORS["fg_heading"], relief=tk.FLAT, activebackground=COLORS["accent_hov"], activeforeground=COLORS["fg_heading"], font=FONTS["ui_bold"], cursor="hand2").pack(side=tk.LEFT)
        tk.Button(btn_inner, text="关闭", command=self._close_settings, bg=COLORS["bg_hover"], fg=COLORS["fg_text"], relief=tk.FLAT, activebackground=COLORS["bg_selected"], activeforeground=COLORS["fg_heading"], font=FONTS["ui"], cursor="hand2").pack(side=tk.RIGHT)

        # 主容器（占据剩余空间）
        container = tk.Frame(self.settings_window, bg=COLORS["bg_main"])
        container.pack(fill=tk.BOTH, expand=True)

        # 左侧边栏 (~200px)
        sidebar = tk.Frame(container, bg=COLORS["bg_panel"], width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # 侧边栏标题
        tk.Label(sidebar, text="设置", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["h2"]).pack(anchor="w", padx=16, pady=(16, 12))

        # 侧边栏按钮列表
        self.settings_tab_btns = {}
        tab_items = [
            ("general", "常规设置"),
            ("scan", "扫描规则"),
            ("perf", "性能阈值"),
        ]
        for tab_id, tab_name in tab_items:
            btn_frame = tk.Frame(sidebar, bg=COLORS["bg_panel"], cursor="hand2")
            btn_frame.pack(fill=tk.X, pady=1)

            btn_label = tk.Label(btn_frame, text=tab_name, bg=COLORS["bg_panel"], fg=COLORS["fg_text"], font=FONTS["ui"], anchor="w", padx=16, pady=10)
            btn_label.pack(fill=tk.X)

            self.settings_tab_btns[tab_id] = {"frame": btn_frame, "label": btn_label}

            def on_tab_click(e, tid=tab_id):
                self._switch_settings_tab(tid)

            def on_tab_enter(e, tid=tab_id):
                if self.settings_tab_var.get() != tid:
                    self.settings_tab_btns[tid]["frame"].config(bg=COLORS["bg_hover"])
                    self.settings_tab_btns[tid]["label"].config(bg=COLORS["bg_hover"])

            def on_tab_leave(e, tid=tab_id):
                if self.settings_tab_var.get() != tid:
                    self.settings_tab_btns[tid]["frame"].config(bg=COLORS["bg_panel"])
                    self.settings_tab_btns[tid]["label"].config(bg=COLORS["bg_panel"])

            btn_frame.bind("<Button-1>", on_tab_click)
            btn_label.bind("<Button-1>", on_tab_click)
            btn_frame.bind("<Enter>", on_tab_enter)
            btn_frame.bind("<Leave>", on_tab_leave)
            btn_label.bind("<Enter>", on_tab_enter)
            btn_label.bind("<Leave>", on_tab_leave)

        # 右侧内容区域（使用简单 Frame，无需 Canvas 滚动）
        self.settings_content_frame = tk.Frame(container, bg=COLORS["bg_main"], padx=24, pady=20)
        self.settings_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 初始化内容
        self._switch_settings_tab("general")

        # 更新初始选中状态
        self._update_settings_tab_visual("general")

    def _switch_settings_tab(self, tab_id):
        """切换设置页面选项卡"""
        self.settings_tab_var.set(tab_id)
        self._update_settings_tab_visual(tab_id)

        # 清除内容区域
        for widget in self.settings_content_frame.winfo_children():
            widget.destroy()

        # 渲染对应内容
        if tab_id == "general":
            self._render_general_settings()
        elif tab_id == "scan":
            self._render_scan_settings()
        elif tab_id == "perf":
            self._render_perf_settings()

    def _update_settings_tab_visual(self, active_tab):
        """更新选项卡按钮的视觉状态"""
        for tab_id, widgets in self.settings_tab_btns.items():
            if tab_id == active_tab:
                widgets["frame"].config(bg=COLORS["bg_selected"])
                widgets["label"].config(bg=COLORS["bg_selected"], fg=COLORS["accent"])
            else:
                widgets["frame"].config(bg=COLORS["bg_panel"])
                widgets["label"].config(bg=COLORS["bg_panel"], fg=COLORS["fg_text"])

    
    def _render_general_settings(self):
        """渲染常规设置页面"""
        parent = self.settings_content_frame

        tk.Label(parent, text="常规设置", bg=COLORS["bg_main"], fg=COLORS["fg_heading"], font=FONTS["h2"]).pack(anchor="w")
        tk.Label(parent, text="配置默认行为与输出选项", bg=COLORS["bg_main"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(anchor="w", pady=(4, 16))

        # 默认输出模式
        mode_panel = RoundedFrame(parent, radius=8)
        mode_panel.pack(fill=tk.X, pady=(0, 12))
        mode_inner = mode_panel.inner_frame

        tk.Label(mode_inner, text="默认输出模式", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 4))
        mode_opts = tk.Frame(mode_inner, bg=COLORS["bg_panel"])
        mode_opts.pack(fill=tk.X, padx=12, pady=(4, 12))
        for mode_val, mode_label in [("normal", "普通"), ("gap", "简洁"), ("skeleton", "骨架")]:
            tk.Radiobutton(mode_opts, text=mode_label, variable=self.settings_mode_var, value=mode_val, bg=COLORS["bg_panel"], fg=COLORS["fg_text"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_panel"], activeforeground=COLORS["accent"], font=FONTS["ui"], cursor="hand2").pack(side=tk.LEFT, padx=8)

        # 输出选项
        output_panel = RoundedFrame(parent, radius=8)
        output_panel.pack(fill=tk.X)
        output_inner = output_panel.inner_frame

        tk.Label(output_inner, text="输出选项", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Checkbutton(output_inner, text="同时生成 .txt 文件", variable=self.settings_save_txt_var, bg=COLORS["bg_panel"], fg=COLORS["fg_text"], selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_panel"], activeforeground=COLORS["accent"], font=FONTS["ui"], cursor="hand2").pack(anchor="w", padx=12, pady=(4, 12))

    def _render_scan_settings(self):
        """渲染扫描规则页面"""
        parent = self.settings_content_frame

        tk.Label(parent, text="扫描规则", bg=COLORS["bg_main"], fg=COLORS["fg_heading"], font=FONTS["h2"]).pack(anchor="w")
        tk.Label(parent, text="定义扫描时允许的文件类型与忽略的目录", bg=COLORS["bg_main"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(anchor="w", pady=(4, 16))

        # 允许的后缀
        ext_panel = RoundedFrame(parent, radius=8)
        ext_panel.pack(fill=tk.X, pady=(0, 12))
        ext_inner = ext_panel.inner_frame

        tk.Label(ext_inner, text="允许的文件后缀", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Label(ext_inner, text="点击 ✕ 移除，在输入框输入并按 Enter 添加", bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"], font=("Microsoft YaHei UI", 9)).pack(anchor="w", padx=12, pady=(4, 4))

        self.ext_tag_cloud = TagCloudFrame(
            ext_inner,
            items=self.temp_config_data.get("allowed_extensions", []),
            on_remove_item=lambda x: None,
            on_add_item=lambda x: None,
            add_placeholder="添加后缀...",
            max_per_row=8,
            bg=COLORS["bg_panel"]
        )
        self.ext_tag_cloud.pack(fill=tk.X, padx=12, pady=(4, 12))

        # 忽略目录
        ignore_panel = RoundedFrame(parent, radius=8)
        ignore_panel.pack(fill=tk.X)
        ignore_inner = ignore_panel.inner_frame

        tk.Label(ignore_inner, text="忽略的目录", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Label(ignore_inner, text="扫描时跳过这些目录", bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"], font=("Microsoft YaHei UI", 9)).pack(anchor="w", padx=12, pady=(4, 4))

        self.ignore_tag_cloud = TagCloudFrame(
            ignore_inner,
            items=self.temp_config_data.get("ignore_dirs", []),
            on_remove_item=lambda x: None,
            on_add_item=lambda x: None,
            add_placeholder="添加目录...",
            max_per_row=8,
            bg=COLORS["bg_panel"]
        )
        self.ignore_tag_cloud.pack(fill=tk.X, padx=12, pady=(4, 12))

    def _render_perf_settings(self):
        """渲染性能阈值页面"""
        parent = self.settings_content_frame

        tk.Label(parent, text="性能阈值", bg=COLORS["bg_main"], fg=COLORS["fg_heading"], font=FONTS["h2"]).pack(anchor="w")
        tk.Label(parent, text="控制全量扫描的超时时间与最大文件数量限制", bg=COLORS["bg_main"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(anchor="w", pady=(4, 16))

        perf_panel = RoundedFrame(parent, radius=8)
        perf_panel.pack(fill=tk.X)
        perf_inner = perf_panel.inner_frame

        tk.Label(perf_inner, text="扫描限制", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 8))

        # 水平并列放置两个设置项
        opts_frame = tk.Frame(perf_inner, bg=COLORS["bg_panel"])
        opts_frame.pack(fill=tk.X, padx=12, pady=(4, 12))

        # 扫描超时
        timeout_frame = tk.Frame(opts_frame, bg=COLORS["bg_panel"])
        timeout_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(timeout_frame, text="扫描超时 (秒):", bg=COLORS["bg_panel"], fg=COLORS["fg_text"], font=FONTS["ui"]).pack(anchor="w")
        timeout_spin = tk.Spinbox(timeout_frame, from_=1, to=30, width=8, textvariable=self.settings_timeout_var, bg=COLORS["bg_input"], fg=COLORS["fg_text"], relief=tk.FLAT, font=FONTS["ui"])
        timeout_spin.pack(anchor="w", pady=(4, 0))

        # 最大文件数
        maxfiles_frame = tk.Frame(opts_frame, bg=COLORS["bg_panel"])
        maxfiles_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(24, 0))
        tk.Label(maxfiles_frame, text="最大文件数:", bg=COLORS["bg_panel"], fg=COLORS["fg_text"], font=FONTS["ui"]).pack(anchor="w")
        maxfiles_spin = tk.Spinbox(maxfiles_frame, from_=100, to=10000, increment=100, width=8, textvariable=self.settings_max_files_var, bg=COLORS["bg_input"], fg=COLORS["fg_text"], relief=tk.FLAT, font=FONTS["ui"])
        maxfiles_spin.pack(anchor="w", pady=(4, 0))

    def _collect_visual_data(self):
        """从可视化组件收集数据"""
        self.temp_config_data["default_mode"] = self.settings_mode_var.get()
        self.temp_config_data["save_txt"] = self.settings_save_txt_var.get()
        try:
            self.temp_config_data["full_load_timeout_seconds"] = int(self.settings_timeout_var.get())
        except ValueError:
            self.temp_config_data["full_load_timeout_seconds"] = 5
        try:
            self.temp_config_data["full_load_max_files"] = int(self.settings_max_files_var.get())
        except ValueError:
            self.temp_config_data["full_load_max_files"] = 2500

        if self.ext_tag_cloud:
            self.temp_config_data["allowed_extensions"] = self.ext_tag_cloud.get_items()
        if self.ignore_tag_cloud:
            self.temp_config_data["ignore_dirs"] = self.ignore_tag_cloud.get_items()

    def _reload_settings_from_file(self):
        """从文件重新加载配置"""
        self.temp_config_data = json.loads(read_config_text())
        self.settings_mode_var.set(self.temp_config_data.get("default_mode", "normal"))
        self.settings_timeout_var.set(str(self.temp_config_data.get("full_load_timeout_seconds", 5)))
        self.settings_max_files_var.set(str(self.temp_config_data.get("full_load_max_files", 2500)))
        self.settings_save_txt_var.set(self.temp_config_data.get("save_txt", False))

        # 重新渲染当前选项卡以更新 TagCloudFrame
        current_tab = self.settings_tab_var.get()
        self._switch_settings_tab(current_tab)

    def _close_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.grab_release()
            self.settings_window.destroy()
        self.settings_window = None
        self.ext_tag_cloud = None
        self.ignore_tag_cloud = None

    def _save_settings_config(self):
        self._collect_visual_data()

        try:
            save_config_text(json.dumps(self.temp_config_data, ensure_ascii=False, indent=2))
            self._reload_runtime_config(preserve_mode=True)
            self._reload_settings_from_file()
            self._set_status("config.json 已保存并重新加载。", reset_after_ms=5000)
            if self.current_input_path and os.path.exists(self.current_input_path):
                self.refresh_file_list()
            messagebox.showinfo("设置", "配置已保存。")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))