import tkinter as tk
from tkinter import ttk
from .Theme import COLORS, FONTS, UI_FONT_FAMILY
from .Components import RoundedFrame, RoundedButton

class MainView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        # 引用关键组件以便控制器访问
        self.path_entry = None
        self.canvas = None
        self.scroll_frame = None
        self.btn_gen = None
        self.top_btn_canvas = None
        self.progress_bar = None  # 进度条引用
        self.mode_var = controller.mode_var
        self.save_txt_var = controller.save_txt_var
        
        self._setup_ui()
        
        # 将进度条引用传递给controller
        self.controller.progress_bar = self.progress_bar

    def _setup_ui(self):
        # --- 顶部工具栏 ---
        toolbar = tk.Frame(self.root, bg=COLORS["bg_main"], padx=20, pady=15)
        toolbar.pack(fill=tk.X)

        # 右侧按钮组
        btn_group = tk.Frame(toolbar, bg=COLORS["bg_main"])
        btn_group.pack(side=tk.RIGHT, padx=(10, 0))

        RoundedButton(btn_group, "浏览", self.controller.browse_dir, width=70).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_group, "刷新", self.controller.refresh_file_list, width=70).pack(side=tk.LEFT, padx=5)
        self.controller.whitelist_btn = RoundedButton(btn_group, "白名单", self.controller.toggle_whitelist_mode, width=80, bg=COLORS["bg_hover"])
        self.controller.whitelist_btn.pack(side=tk.LEFT, padx=5)
        self.top_btn_canvas = RoundedButton(btn_group, "📌", self.controller.toggle_topmost, width=40)
        self.top_btn_canvas.pack(side=tk.LEFT, padx=5)

        # 左侧路径框
        path_rounded = RoundedFrame(toolbar, bg=COLORS["bg_panel"], radius=8, padding=0)
        path_rounded.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        path_container = path_rounded.inner_frame
        path_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(path_container, text="📂", bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"], 
                 font=("Segoe UI Emoji", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.path_entry = tk.Entry(path_container, bg=COLORS["bg_panel"], fg=COLORS["fg_text"], 
                                   insertbackground="white", relief=tk.FLAT, 
                                   font=(UI_FONT_FAMILY, 11))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.path_entry.insert(0, "输入或选择项目路径...")
        self.path_entry.bind("<FocusIn>", self.controller._on_path_focus_in)
        self.path_entry.bind("<FocusOut>", self.controller._on_path_focus_out)

        # --- 主体内容区 ---
        content_area = tk.Frame(self.root, bg=COLORS["bg_main"], padx=30)
        content_area.pack(fill=tk.BOTH, expand=True)

        tree_rounded = RoundedFrame(content_area, radius=COLORS["radius_panel"])
        tree_rounded.pack(fill=tk.BOTH, expand=True)
        tree_container = tree_rounded.inner_frame

        tree_header = tk.Frame(tree_container, bg=COLORS["bg_panel"], pady=12, padx=15)
        tree_header.pack(fill=tk.X)
        tk.Label(tree_header, text="项目目录树", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["h1"]).pack(side=tk.LEFT)
        tk.Label(tree_header, text="(点击文件夹批量忽略/点击文件单个忽略)", bg=COLORS["bg_panel"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(tree_container, bg=COLORS["bg_panel"], highlightthickness=0)
        scrollbar = tk.Scrollbar(tree_container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS["bg_panel"])

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw", width=self.canvas.winfo_width())
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(1, width=e.width))
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self.controller._on_mousewheel)

        # --- 底部控制栏 ---
        footer = tk.Frame(self.root, bg=COLORS["bg_main"], padx=25, pady=25)
        footer.pack(fill=tk.X)

        mode_frame = tk.Frame(footer, bg=COLORS["bg_main"])
        mode_frame.pack(side=tk.LEFT)
        tk.Label(mode_frame, text="模式:", bg=COLORS["bg_main"], fg=COLORS["fg_text"], font=FONTS["ui_bold"]).pack(side=tk.LEFT, padx=(0, 15))
        self._create_modern_radio(mode_frame, "普通", "normal")
        self._create_modern_radio(mode_frame, "去注释", "gap")
        self._create_modern_radio(mode_frame, "骨架", "skeleton")

        action_group = tk.Frame(footer, bg=COLORS["bg_main"])
        action_group.pack(side=tk.RIGHT)

        # 进度条（默认隐藏）
        self.progress_bar = tk.ttk.Progressbar(action_group, variable=self.controller.progress_var, 
                                               maximum=100, mode='determinate', length=150)
        # 默认隐藏进度条
        self.progress_bar.pack_forget()

        self.btn_gen = RoundedButton(action_group, "🚀 生成 Markdown", self.controller.on_generate_click,
                                    bg=COLORS["accent"], hover_bg=COLORS["accent_hov"],
                                    radius=COLORS["radius_btn"],
                                    font=FONTS["h1"], padding_x=50, padding_y=12)
        self.btn_gen.pack(side=tk.LEFT, padx=10)

        tk.Checkbutton(action_group, text="同步生成txt", variable=self.save_txt_var,
                       bg=COLORS["bg_main"], fg=COLORS["fg_text"],
                       selectcolor=COLORS["bg_panel"], activebackground=COLORS["bg_main"],
                       activeforeground=COLORS["accent"], font=FONTS["ui"], cursor="hand2").pack(side=tk.LEFT, padx=15)

    def _create_modern_radio(self, parent, text, value):
        tk.Radiobutton(parent, text=text, variable=self.mode_var, value=value,
                       bg=COLORS["bg_main"], fg=COLORS["fg_text"], selectcolor=COLORS["bg_panel"],
                       activebackground=COLORS["bg_main"], activeforeground=COLORS["accent"], 
                       font=FONTS["ui"], cursor="hand2").pack(side=tk.LEFT, padx=5)
