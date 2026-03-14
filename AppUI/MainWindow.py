import os
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import shutil
import subprocess
import ctypes

from Core.ConfigLoader import load_config
from Core.Analyzer import ProjectManager
from .Tree import TreeBuilder
from .Theme import COLORS, FONTS
from .Components import RoundedFrame, RoundedButton
from .Views import MainView
from .SystemServices import (
    set_win11_corners, 
    SystemHotkeyService, 
    SystemTrayService, 
    StartupService, 
    ExplorerService
)

# --- Windows 高 DPI 感知 ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class CodeFeederApp:
    def __init__(self, root, initial_dir=None):
        self.root = root
        self.cfg = load_config()
        self.manager = ProjectManager(self.cfg)

        self.root.title(f"AI CodeFeeder - {self.cfg.version_info[0]}")
        self.root.geometry("1400x1000")
        self.root.configure(bg=COLORS["bg_main"])
        
        # 状态变量
        self.is_topmost = False
        self.target_dir = initial_dir
        self.all_files_map = {}
        self.selection_state = {}
        self.path_to_label = {}
        self.mode_var = tk.StringVar(value="normal")
        self.save_txt_var = tk.BooleanVar(value=False)
        self.whitelist_mode = False  # 白名单模式：默认全部不选中
        self.progress_var = tk.IntVar(value=0)  # 进度条变量

        # 初始化系统服务
        self.hotkey_service = SystemHotkeyService(self._on_hotkey_triggered)
        self.tray_service = SystemTrayService(
            on_show=self._show_window,
            on_quit=self._quit_app,
            get_startup_status=StartupService.is_startup_enabled,
            toggle_startup=self._toggle_startup
        )

        # 设置 Win11 视觉效果
        self.root.update()
        set_win11_corners(ctypes.windll.user32.GetParent(self.root.winfo_id()))

        # 构建 UI
        self.view = MainView(self.root, self)
        
        # 快捷引用 view 中的组件
        self.path_entry = self.view.path_entry
        self.canvas = self.view.canvas
        self.scroll_frame = self.view.scroll_frame
        self.btn_gen = self.view.btn_gen
        self.top_btn_canvas = self.view.top_btn_canvas
        
        # 启动服务
        self.hotkey_service.start()
        self.tray_service.start()

        # 事件绑定
        self.root.bind("<Return>", lambda e: self.on_generate_click())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        if self.target_dir:
            self._update_path_display(self.target_dir)
            self.refresh_file_list()

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.root.attributes("-topmost", self.is_topmost)
        self.top_btn_canvas.config(fg=COLORS["accent"] if self.is_topmost else COLORS["fg_text"])

    def toggle_whitelist_mode(self):
        """白名单模式：点击后所有文件默认不选中，用户手动勾选"""
        self.whitelist_mode = not self.whitelist_mode
        # 更新按钮状态
        if hasattr(self, 'whitelist_btn'):
            if self.whitelist_mode:
                self.whitelist_btn.config(bg=COLORS["accent"], text="✓ 白名单")
            else:
                self.whitelist_btn.config(bg=COLORS["bg_hover"], text="白名单")
        
        # 根据模式设置初始选中状态
        new_default = not self.whitelist_mode  # 白名单模式=False，普通=True
        for rel_path in self.selection_state:
            self.selection_state[rel_path] = new_default
        # 刷新UI
        self._refresh_tree_visual()

    def _refresh_tree_visual(self):
        """刷新树的视觉状态"""
        for rel_path, widgets in self.path_to_label.items():
            is_selected = self.selection_state.get(rel_path, False)
            self._update_item_visual(rel_path, is_selected)

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
            self.target_dir = path
            self._update_path_display(path)
            self.refresh_file_list()
        else:
            messagebox.showinfo("快捷键触发", "已识别快捷键 Ctrl+`\n\n请确保当前已打开 Windows 资源管理器窗口，或选中了某个文件夹。")

    def _toggle_startup(self, icon, item):
        current_state = StartupService.is_startup_enabled()
        new_state = not current_state
        if StartupService.toggle_startup(new_state):
            # 托盘菜单会自动通过 checked 逻辑更新状态
            pass

    def _show_window(self):
        self.root.after(0, self.root.deiconify)

    def _on_close(self):
        self.root.withdraw()

    def _quit_app(self):
        self.tray_service.stop()
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

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.target_dir = d
            self._update_path_display(d)
            self.refresh_file_list()

    def refresh_file_list(self):
        path = self.path_entry.get()
        if not path or not os.path.exists(path): return

        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.all_files_map.clear()
        self.selection_state.clear()
        self.path_to_label.clear()

        flat_files = self.manager.scan_directory(path)
        if not flat_files:
            tk.Label(self.scroll_frame, text="未找到相关代码文件。", bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"],
                     font=FONTS["ui"]).pack(pady=40)
            return

        visual_items = TreeBuilder.build_visual_data(flat_files)
        for item in visual_items:
            if item['type'] == 'file':
                self.all_files_map[item['rel_path']] = item['full_path']
                self.selection_state[item['rel_path']] = True
            self._create_tree_row(item)

    def _create_tree_row(self, item):
        text = item['text']
        is_file = (item['type'] == 'file')
        rel_path = item.get('rel_path')

        level = rel_path.count(os.sep) if rel_path else 0
        indent_px = level * 48

        row_frame = tk.Frame(self.scroll_frame, bg=COLORS["bg_panel"])
        row_frame.pack(fill=tk.X, pady=1)

        spacer = None
        if indent_px > 0:
            spacer = tk.Frame(row_frame, bg=COLORS["bg_panel"], width=indent_px, height=34)
            spacer.pack(side=tk.LEFT, fill=tk.Y)

        icon_char = "📄" if is_file else "📁"
        if is_file and text.endswith(".py"): icon_char = "🐍"
        icon_color = COLORS["icon_file"] if is_file else COLORS["icon_folder"]
        
        icon_lbl = tk.Label(row_frame, text=icon_char, bg=COLORS["bg_panel"], fg=icon_color, 
                            font=("Segoe UI Emoji", 12), width=3, anchor="center")
        icon_lbl.pack(side=tk.LEFT)

        is_selected = self.selection_state.get(rel_path, True)
        curr_font = FONTS["tree_norm"] if is_selected else FONTS["tree_strike"]
        curr_fg = COLORS["fg_text"] if is_selected else COLORS["text_ignore"]
        
        if not is_file and not is_selected:
            curr_fg = COLORS["text_ignore"]
        elif not is_file:
            curr_fg = COLORS["folder_fg"]

        name_lbl = tk.Label(row_frame, text=item['name'], bg=COLORS["bg_panel"], fg=curr_fg, 
                            font=curr_font, anchor="w")
        name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)

        if rel_path:
            self.path_to_label[rel_path] = {
                "label": name_lbl, "frame": row_frame, "icon": icon_lbl,
                "spacer": spacer, "is_file": is_file
            }

        def toggle(e):
            if is_file: self.on_toggle_file(rel_path)
            else: self.on_toggle_folder(rel_path)

        def on_enter(e):
            for w in [row_frame, name_lbl, icon_lbl, spacer]:
                if w: w.config(bg=COLORS["bg_hover"])

        def on_leave(e):
            for w in [row_frame, name_lbl, icon_lbl, spacer]:
                if w: w.config(bg=COLORS["bg_panel"])

        for w in [row_frame, name_lbl, icon_lbl, spacer]:
            if w:
                w.bind("<Button-1>", toggle)
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)

    def on_toggle_file(self, rel_path):
        new_state = not self.selection_state[rel_path]
        self.selection_state[rel_path] = new_state
        self._update_item_visual(rel_path, new_state)

    def on_toggle_folder(self, rel_path):
        affected_files = [p for p in self.all_files_map.keys() if p.startswith(rel_path + os.sep) or p == rel_path]
        if not affected_files: return
        any_selected = any(self.selection_state.get(p, False) for p in affected_files)
        new_state = not any_selected
        for p in affected_files:
            self.selection_state[p] = new_state
            self._update_item_visual(p, new_state)
        if rel_path in self.path_to_label:
             self._update_item_visual(rel_path, new_state)

    def _update_item_visual(self, rel_path, is_selected):
        widgets = self.path_to_label.get(rel_path)
        if not widgets: return
        lbl = widgets["label"]
        icon_lbl = widgets["icon"]
        is_file = widgets["is_file"]
        
        if is_selected:
            # 恢复正常状态
            icon_char = icon_lbl.cget("text")
            icon_color = COLORS["icon_file"] if is_file else COLORS["icon_folder"]
            icon_lbl.config(fg=icon_color)
            lbl.config(font=FONTS["tree_norm"], fg=COLORS["fg_text"] if is_file else COLORS["folder_fg"])
        else:
            # 显眼的“已忽略”状态：图标变灰、文字删除线并变淡
            icon_lbl.config(fg=COLORS["text_ignore"])
            lbl.config(font=FONTS["tree_strike"], fg=COLORS["text_ignore"])

    def on_generate_click(self):
        path = self.path_entry.get()
        if not path: return
        selected_items = [(r, self.all_files_map[r]) for r, s in self.selection_state.items() if s]
        if not selected_items:
            messagebox.showwarning("提示", "请至少选择一个文件！")
            return

        mode = self.mode_var.get()
        suffix_map = {"normal": "_Codes.md", "gap": "_Gap.md", "skeleton": "_Skeleton.md"}
        
        # 将生成路径修改为项目根目录的同级文件夹
        parent_dir = os.path.dirname(os.path.normpath(path))
        out_path = os.path.join(parent_dir, f"{os.path.basename(path)}{suffix_map.get(mode, '_Codes.md')}")

        self.btn_gen.config(state=tk.DISABLED, text="处理中...", bg=COLORS["bg_hover"])
        
        # 显示进度条
        if self.progress_bar:
            self.progress_bar.pack(side=tk.LEFT, padx=10)
            self.progress_var.set(0)
        
        ignored_rels = [r for r, s in self.selection_state.items() if not s]
        
        # 创建进度回调函数
        def progress_callback(current, total, filename):
            percent = int((current / total) * 100)
            self.root.after(0, lambda: self.progress_var.set(percent))
        
        threading.Thread(target=self._generate_thread,
                         args=(path, selected_items, out_path, mode, self.save_txt_var.get(), ignored_rels, progress_callback)).start()

    def _generate_thread(self, root_path, items, out_path, mode, need_txt, ignored_rels, progress_callback=None):
        try:
            char_count = self.manager.pipeline_write(root_path, items, out_path, mode, None, ignored_rels, progress_callback)
            if need_txt: shutil.copy2(out_path, os.path.splitext(out_path)[0] + ".txt")
            token_count = int(char_count / 3.5)
            self.root.after(0, lambda: self._on_success(out_path, token_count))
        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, path, token_count):
        self.btn_gen.config(state=tk.NORMAL, text="🚀 生成 Markdown", bg=COLORS["accent"])
        # 隐藏进度条
        if self.progress_bar:
            self.progress_bar.pack_forget()
        messagebox.showinfo("生成成功", f"文件已保存至：\n{path}\n\n📊 预估 Token 总数: {token_count}")
        # 生成后不自动打开目录（用户已知文件位置）
        # 删除原有 explorer 逻辑，避免重复打开目录
        # 生成结束后程序留在后台保持静默
        self._on_close()

    def _on_error(self, msg):
        self.btn_gen.config(state=tk.NORMAL, text="🚀 生成 Markdown", bg=COLORS["accent"])
        # 隐藏进度条
        if self.progress_bar:
            self.progress_bar.pack_forget()
        messagebox.showerror("错误", msg)
