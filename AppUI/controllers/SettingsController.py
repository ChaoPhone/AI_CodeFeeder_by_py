"""
设置控制器 - 处理配置设置逻辑
"""
import json
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, Optional, Callable

from Core.ConfigLoader import load_config, read_config_text, save_config_text
from AppUI.models.AppState import AppState
from AppUI.Theme import COLORS, FONTS
from AppUI.Components import RoundedFrame, TagCloudFrame


class SettingsController:
    """
    设置控制器
    负责配置加载、保存、UI 渲染等
    """
    
    def __init__(self,
                 state: AppState,
                 on_config_changed: Optional[Callable[[], None]] = None,
                 on_status_update: Optional[Callable[[str, Optional[int]], None]] = None):
        self.state = state
        self.on_config_changed = on_config_changed
        self.on_status_update = on_status_update
        
        self.settings_window: Optional[tk.Toplevel] = None
        self.temp_config_data: Dict[str, Any] = {}
        
        self.settings_mode_var: Optional[tk.StringVar] = None
        self.settings_timeout_var: Optional[tk.StringVar] = None
        self.settings_max_files_var: Optional[tk.StringVar] = None
        self.settings_save_txt_var: Optional[tk.BooleanVar] = None
        
        self.ext_tag_cloud: Optional[TagCloudFrame] = None
        self.ignore_tag_cloud: Optional[TagCloudFrame] = None
        
        self.settings_canvas: Optional[tk.Canvas] = None
        self.settings_content_frame: Optional[tk.Frame] = None
        self.settings_canvas_window: Optional[int] = None
    
    def load_config_data(self) -> Dict[str, Any]:
        """加载配置数据"""
        try:
            self.temp_config_data = json.loads(read_config_text())
        except Exception:
            self.temp_config_data = {}
        return self.temp_config_data
    
    def save_config(self) -> bool:
        """
        保存配置
        
        :return: 是否成功
        """
        self._collect_visual_data()
        
        try:
            save_config_text(json.dumps(self.temp_config_data, ensure_ascii=False, indent=2))
            
            if self.on_config_changed:
                self.on_config_changed()
            
            self.state.set_output_mode(self.temp_config_data.get("default_mode", "normal"))
            
            if self.on_status_update:
                self.on_status_update("config.json 已保存并重新加载。", 5000)
            
            return True
            
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return False
    
    def _collect_visual_data(self) -> None:
        """从可视化组件收集数据"""
        if self.settings_mode_var:
            self.temp_config_data["default_mode"] = self.settings_mode_var.get()
        
        if self.settings_save_txt_var:
            self.temp_config_data["save_txt"] = self.settings_save_txt_var.get()
        
        try:
            if self.settings_timeout_var:
                self.temp_config_data["full_load_timeout_seconds"] = int(self.settings_timeout_var.get())
        except ValueError:
            self.temp_config_data["full_load_timeout_seconds"] = 5
        
        try:
            if self.settings_max_files_var:
                self.temp_config_data["full_load_max_files"] = int(self.settings_max_files_var.get())
        except ValueError:
            self.temp_config_data["full_load_max_files"] = 2500
        
        if self.ext_tag_cloud:
            self.temp_config_data["allowed_extensions"] = self.ext_tag_cloud.get_items()
        
        if self.ignore_tag_cloud:
            self.temp_config_data["ignore_dirs"] = self.ignore_tag_cloud.get_items()
    
    def reload_from_file(self) -> None:
        """从文件重新加载配置"""
        self.temp_config_data = json.loads(read_config_text())
        
        if self.settings_mode_var:
            self.settings_mode_var.set(self.temp_config_data.get("default_mode", "normal"))
        
        if self.settings_timeout_var:
            self.settings_timeout_var.set(str(self.temp_config_data.get("full_load_timeout_seconds", 5)))
        
        if self.settings_max_files_var:
            self.settings_max_files_var.set(str(self.temp_config_data.get("full_load_max_files", 2500)))
        
        if self.settings_save_txt_var:
            self.settings_save_txt_var.set(self.temp_config_data.get("save_txt", False))
    
    def create_vars(self, parent: tk.Toplevel) -> None:
        """创建设置变量"""
        self.settings_mode_var = tk.StringVar(value=self.temp_config_data.get("default_mode", "gap"))
        self.settings_timeout_var = tk.StringVar(value=str(self.temp_config_data.get("full_load_timeout_seconds", 5)))
        self.settings_max_files_var = tk.StringVar(value=str(self.temp_config_data.get("full_load_max_files", 2500)))
        self.settings_save_txt_var = tk.BooleanVar(value=self.temp_config_data.get("save_txt", False))
    
    def render_settings_content(self, parent: tk.Frame) -> None:
        """渲染设置内容"""
        self._render_general_section(parent)
        self._render_scan_section(parent)
        self._render_perf_section(parent)
    
    def _render_general_section(self, parent: tk.Frame) -> None:
        """渲染常规设置"""
        tk.Label(parent, text="常规设置", bg=COLORS["bg_main"], fg=COLORS["fg_heading"], font=FONTS["h2"]).pack(anchor="w", pady=(0, 4))
        tk.Label(parent, text="配置默认行为与输出选项", bg=COLORS["bg_main"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(anchor="w", pady=(0, 12))
        
        mode_panel = RoundedFrame(parent, radius=8)
        mode_panel.pack(fill=tk.X, pady=(0, 12))
        mode_inner = mode_panel.inner_frame
        
        tk.Label(mode_inner, text="默认输出模式", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 4))
        mode_opts = tk.Frame(mode_inner, bg=COLORS["bg_panel"])
        mode_opts.pack(fill=tk.X, padx=12, pady=(4, 12))
        
        for mode_val, mode_label in [("normal", "普通"), ("gap", "简洁"), ("skeleton", "骨架")]:
            tk.Radiobutton(
                mode_opts, text=mode_label, variable=self.settings_mode_var, 
                value=mode_val, bg=COLORS["bg_panel"], fg=COLORS["fg_text"],
                selectcolor=COLORS["bg_input"], activebackground=COLORS["bg_panel"],
                activeforeground=COLORS["accent"], font=FONTS["ui"], cursor="hand2"
            ).pack(side=tk.LEFT, padx=8)
        
        output_panel = RoundedFrame(parent, radius=8)
        output_panel.pack(fill=tk.X, pady=(0, 20))
        output_inner = output_panel.inner_frame
        
        tk.Label(output_inner, text="输出选项", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Checkbutton(
            output_inner, text="同时生成 .txt 文件", variable=self.settings_save_txt_var,
            bg=COLORS["bg_panel"], fg=COLORS["fg_text"], selectcolor=COLORS["bg_input"],
            activebackground=COLORS["bg_panel"], activeforeground=COLORS["accent"],
            font=FONTS["ui"], cursor="hand2"
        ).pack(anchor="w", padx=12, pady=(4, 12))
    
    def _render_scan_section(self, parent: tk.Frame) -> None:
        """渲染扫描规则"""
        tk.Label(parent, text="扫描规则", bg=COLORS["bg_main"], fg=COLORS["fg_heading"], font=FONTS["h2"]).pack(anchor="w", pady=(20, 4))
        tk.Label(parent, text="定义扫描时允许的文件类型与忽略的目录", bg=COLORS["bg_main"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(anchor="w", pady=(0, 12))
        
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
        
        ignore_panel = RoundedFrame(parent, radius=8)
        ignore_panel.pack(fill=tk.X, pady=(0, 20))
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
    
    def _render_perf_section(self, parent: tk.Frame) -> None:
        """渲染性能阈值"""
        tk.Label(parent, text="性能阈值", bg=COLORS["bg_main"], fg=COLORS["fg_heading"], font=FONTS["h2"]).pack(anchor="w", pady=(20, 4))
        tk.Label(parent, text="控制全量扫描的超时时间与最大文件数量限制", bg=COLORS["bg_main"], fg=COLORS["fg_secondary"], font=FONTS["ui"]).pack(anchor="w", pady=(0, 12))
        
        perf_panel = RoundedFrame(parent, radius=8)
        perf_panel.pack(fill=tk.X)
        perf_inner = perf_panel.inner_frame
        
        tk.Label(perf_inner, text="扫描限制", bg=COLORS["bg_panel"], fg=COLORS["fg_heading"], font=FONTS["ui_bold"]).pack(anchor="w", padx=12, pady=(12, 8))
        
        opts_frame = tk.Frame(perf_inner, bg=COLORS["bg_panel"])
        opts_frame.pack(fill=tk.X, padx=12, pady=(4, 12))
        
        timeout_frame = tk.Frame(opts_frame, bg=COLORS["bg_panel"])
        timeout_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(timeout_frame, text="扫描超时 (秒):", bg=COLORS["bg_panel"], fg=COLORS["fg_text"], font=FONTS["ui"]).pack(anchor="w")
        tk.Spinbox(
            timeout_frame, from_=1, to=30, width=8,
            textvariable=self.settings_timeout_var,
            bg=COLORS["bg_input"], fg=COLORS["fg_text"],
            relief=tk.FLAT, font=FONTS["ui"]
        ).pack(anchor="w", pady=(4, 0))
        
        maxfiles_frame = tk.Frame(opts_frame, bg=COLORS["bg_panel"])
        maxfiles_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(24, 0))
        tk.Label(maxfiles_frame, text="最大文件数:", bg=COLORS["bg_panel"], fg=COLORS["fg_text"], font=FONTS["ui"]).pack(anchor="w")
        tk.Spinbox(
            maxfiles_frame, from_=100, to=10000, increment=100, width=8,
            textvariable=self.settings_max_files_var,
            bg=COLORS["bg_input"], fg=COLORS["fg_text"],
            relief=tk.FLAT, font=FONTS["ui"]
        ).pack(anchor="w", pady=(4, 0))
    
    def close(self) -> None:
        """关闭设置窗口"""
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.grab_release()
            self.settings_window.destroy()
        self.settings_window = None
        self.ext_tag_cloud = None
        self.ignore_tag_cloud = None
    
    def is_open(self) -> bool:
        """检查设置窗口是否打开"""
        return self.settings_window is not None and self.settings_window.winfo_exists()