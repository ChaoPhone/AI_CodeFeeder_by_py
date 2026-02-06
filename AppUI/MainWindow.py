import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, font
import subprocess
import threading
import shutil  # 👈 记得导入 shutil
from Core.ConfigLoader import load_config
from Core.Analyzer import ProjectManager
from .Tree import TreeBuilder

# --- 配色方案 ---
COLORS = {
    "bg_main": "#1E1E1E",
    "bg_panel": "#252526",
    "fg_text": "#CCCCCC",
    "fg_active": "#FFFFFF",
    "fg_ignore": "#6E6E6E",
    "accent": "#007ACC",
    "accent_hov": "#0098FF",
    "item_hover": "#37373D",
    "folder_fg": "#C586C0",
    "tree_lines": "#585858"
}

FONTS = {
    "tree": ("Consolas", 12),
    "ui": ("Microsoft YaHei UI", 11),
    "ui_bold": ("Microsoft YaHei UI", 11, "bold"),
    "h1": ("Microsoft YaHei UI", 14, "bold")
}


class CodeFeederApp:
    def __init__(self, root, initial_dir=None):
        self.root = root
        self.cfg = load_config()
        self.manager = ProjectManager(self.cfg)

        self.root.title(f"AI CodeFeeder - {self.cfg.version_info[0]}")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS["bg_main"])

        self.target_dir = initial_dir
        self.all_files_map = {}
        self.selection_state = {}
        self.mode_var = tk.StringVar(value="normal")

        # ✨ 新增：保存 TXT 的状态变量
        self.save_txt_var = tk.BooleanVar(value=False)

        self.font_normal = font.Font(family="Consolas", size=12)
        self.font_strike = font.Font(family="Consolas", size=12, overstrike=1)

        self._setup_ui()

        if self.target_dir:
            self._update_path_display(self.target_dir)
            self.refresh_file_list()

    def _setup_ui(self):
        header = tk.Frame(self.root, bg=COLORS["bg_main"], pady=15, padx=20)
        header.pack(fill=tk.X)
        tk.Label(header, text="Project Path", bg=COLORS["bg_main"], fg=COLORS["fg_text"], font=FONTS["ui_bold"]).pack(
            side=tk.LEFT)

        self.path_entry = tk.Entry(header, bg=COLORS["bg_panel"], fg=COLORS["fg_active"],
                                   insertbackground="white", relief=tk.FLAT, font=FONTS["tree"])
        self.path_entry.pack(side=tk.LEFT, padx=15, fill=tk.X, expand=True, ipady=4)

        self._create_flat_btn(header, "📂 Browse", self.browse_dir).pack(side=tk.LEFT, padx=5)
        self._create_flat_btn(header, "🔄 Refresh", self.refresh_file_list).pack(side=tk.LEFT)

        tree_container = tk.Frame(self.root, bg=COLORS["bg_panel"], padx=2, pady=2)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        hint_bar = tk.Frame(tree_container, bg=COLORS["bg_panel"], pady=5)
        hint_bar.pack(fill=tk.X)
        tk.Label(hint_bar, text="Project Tree Structure", bg=COLORS["bg_panel"], fg=COLORS["accent"],
                 font=FONTS["ui_bold"]).pack(side=tk.LEFT, padx=10)
        tk.Label(hint_bar, text="(Click file to Toggle)", bg=COLORS["bg_panel"], fg="#666", font=FONTS["ui"]).pack(
            side=tk.RIGHT, padx=10)

        self.canvas = tk.Canvas(tree_container, bg=COLORS["bg_panel"], highlightthickness=0)
        scrollbar = tk.Scrollbar(tree_container, orient="vertical", command=self.canvas.yview, bg=COLORS["bg_panel"])
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS["bg_panel"])

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        footer = tk.Frame(self.root, bg=COLORS["bg_main"], pady=15, padx=20)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(footer, text="Mode:", bg=COLORS["bg_main"], fg=COLORS["fg_text"], font=FONTS["ui"]).pack(side=tk.LEFT,
                                                                                                          padx=(0, 10))
        self._create_mode_radio(footer, "Normal", "normal")
        self._create_mode_radio(footer, "Gap", "gap")
        self._create_mode_radio(footer, "Skeleton", "skeleton")

        self.btn_gen = tk.Button(footer, text="🚀 Generate Markdown", command=self.on_generate_click,
                                 bg=COLORS["accent"], fg="white", activebackground=COLORS["accent_hov"],
                                 font=("Microsoft YaHei UI", 11, "bold"), relief=tk.FLAT, padx=20, pady=5,
                                 cursor="hand2")
        self.btn_gen.pack(side=tk.RIGHT)

        # ✨ 新增：同时保存为 TXT 的选项
        chk_txt = tk.Checkbutton(footer, text="Also .txt", variable=self.save_txt_var,
                                 bg=COLORS["bg_main"], fg=COLORS["fg_text"],
                                 selectcolor=COLORS["bg_panel"], activebackground=COLORS["bg_main"],
                                 activeforeground=COLORS["accent"], font=FONTS["ui"], cursor="hand2")
        chk_txt.pack(side=tk.RIGHT, padx=10)

    def _create_flat_btn(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg=COLORS["item_hover"], fg=COLORS["fg_text"],
                         activebackground=COLORS["accent"], activeforeground="white", relief=tk.FLAT, font=FONTS["ui"],
                         padx=10, pady=2, cursor="hand2")

    def _create_mode_radio(self, parent, text, value):
        tk.Radiobutton(parent, text=text, variable=self.mode_var, value=value,
                       bg=COLORS["bg_main"], fg=COLORS["fg_text"], selectcolor=COLORS["bg_panel"],
                       activebackground=COLORS["bg_main"], activeforeground=COLORS["accent"], font=FONTS["ui"],
                       cursor="hand2").pack(side=tk.LEFT, padx=5)

    def _update_path_display(self, path):
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)

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
        if not path or not os.path.exists(path):
            return

        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.all_files_map.clear()
        self.selection_state.clear()

        flat_files = self.manager.scan_directory(path)
        if not flat_files:
            tk.Label(self.scroll_frame, text="No code files found.", bg=COLORS["bg_panel"], fg=COLORS["fg_ignore"],
                     font=FONTS["ui"]).pack(pady=20)
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

        row_frame = tk.Frame(self.scroll_frame, bg=COLORS["bg_panel"])
        row_frame.pack(fill=tk.X, expand=True)

        fg_color = COLORS["fg_text"] if is_file else COLORS["folder_fg"]
        if is_file: fg_color = COLORS["fg_active"]

        lbl = tk.Label(row_frame, text=text, bg=COLORS["bg_panel"], fg=fg_color,
                       font=self.font_normal, anchor="w", padx=10, pady=2)
        lbl.pack(fill=tk.X, anchor="w")

        if is_file:
            def on_enter(e):
                if self.selection_state[rel_path]:
                    row_frame.config(bg=COLORS["item_hover"])
                    lbl.config(bg=COLORS["item_hover"])

            def on_leave(e):
                row_frame.config(bg=COLORS["bg_panel"])
                lbl.config(bg=COLORS["bg_panel"])

            def on_click(e):
                curr = self.selection_state[rel_path]
                new_state = not curr
                self.selection_state[rel_path] = new_state

                if new_state:
                    lbl.config(font=self.font_normal, fg=COLORS["fg_active"])
                else:
                    lbl.config(font=self.font_strike, fg=COLORS["fg_ignore"])

            for w in (row_frame, lbl):
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
        else:
            pass

    def on_generate_click(self):
        path = self.path_entry.get()
        if not path: return

        selected_items = []
        for rel_path, is_selected in self.selection_state.items():
            if is_selected:
                full_path = self.all_files_map[rel_path]
                selected_items.append((rel_path, full_path))

        if not selected_items:
            messagebox.showwarning("Warning", "Select at least one file!")
            return

        mode = self.mode_var.get()
        suffix_map = {"normal": "_Codes.md", "gap": "_Gap.md", "skeleton": "_Skeleton.md"}
        base_name = os.path.basename(path) or "Project"
        default_name = f"{base_name}{suffix_map.get(mode, '_Codes.md')}"

        parent_dir = os.path.dirname(path)
        save_dir = parent_dir if os.access(parent_dir, os.W_OK) else path
        output_path = os.path.join(save_dir, default_name)

        self.btn_gen.config(state=tk.DISABLED, text="Processing...", bg=COLORS["item_hover"])

        error_log = None
        try:
            clip = self.root.clipboard_get()
            if clip and clip.startswith("=" * 10):
                error_log = clip
        except:
            pass

        # ✨ 获取复选框状态
        need_txt = self.save_txt_var.get()

        threading.Thread(target=self._generate_thread,
                         args=(path, selected_items, output_path, mode, error_log, need_txt)).start()

    def _generate_thread(self, root_path, items, out_path, mode, err_log, need_txt):
        try:
            self.manager.pipeline_write(root_path, items, out_path, mode, err_log)

            # ✨ 生成副本逻辑
            if need_txt:
                txt_path = os.path.splitext(out_path)[0] + ".txt"
                shutil.copy2(out_path, txt_path)

            self.root.after(0, lambda: self._on_success(out_path))
        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, path):
        self.btn_gen.config(state=tk.NORMAL, text="🚀 Generate Markdown", bg=COLORS["accent"])
        messagebox.showinfo("Success", f"Saved to:\n{path}")
        if os.name == 'nt':
            subprocess.Popen(f'explorer /select,"{path}"')

    def _on_error(self, msg):
        self.btn_gen.config(state=tk.NORMAL, text="🚀 Generate Markdown", bg=COLORS["accent"])
        messagebox.showerror("Error", msg)