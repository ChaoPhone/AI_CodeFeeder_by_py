"""
树视图组件 - 处理目录树的显示与交互
"""
import os
import tkinter as tk
from typing import Dict, Any, Optional, Callable

from AppUI.Theme import COLORS, FONTS
from AppUI.Tree import TreeBuilder


class TreeView:
    """
    目录树视图组件
    负责树的渲染、折叠、选择状态显示
    """
    
    def __init__(self, scroll_frame: tk.Frame, on_toggle_file: Callable, on_toggle_folder: Callable, on_toggle_collapse: Callable):
        self.scroll_frame = scroll_frame
        self.on_toggle_file = on_toggle_file
        self.on_toggle_folder = on_toggle_folder
        self.on_toggle_collapse = on_toggle_collapse
        
        self.path_to_label: Dict[str, Dict[str, Any]] = {}
    
    def clear(self) -> None:
        """清空树视图"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.path_to_label.clear()
    
    def show_message(self, message: str) -> None:
        """显示消息"""
        self.clear()
        tk.Label(
            self.scroll_frame,
            text=message,
            bg=COLORS["bg_panel"],
            fg=COLORS["fg_secondary"],
            font=FONTS["ui"]
        ).pack(pady=40)
    
    def show_loading(self, message: str) -> None:
        """显示加载占位符"""
        self.clear()
        tk.Label(
            self.scroll_frame,
            text=message,
            bg=COLORS["bg_panel"],
            fg=COLORS["fg_secondary"],
            font=FONTS["ui"]
        ).pack(anchor="w", padx=30, pady=(24, 12))
        
        for width in (0.88, 0.74, 0.93, 0.68, 0.82):
            bar = tk.Frame(self.scroll_frame, bg=COLORS["bg_hover"], height=18)
            bar.pack(fill=tk.X, padx=30, pady=8)
            bar.pack_propagate(False)
            tk.Frame(bar, bg=COLORS["bg_selected"], width=int(920 * width), height=18).pack(anchor="w")
    
    def render_tree(self, flat_files: list, collapsed_folders: set, selection_state: dict, all_files_map: dict, whitelist_mode: bool) -> set:
        """
        渲染目录树
        
        :param flat_files: 扁平文件列表 [(rel_path, full_path), ...]
        :param collapsed_folders: 已折叠的文件夹集合
        :param selection_state: 选择状态字典
        :param all_files_map: 文件映射字典
        :param whitelist_mode: 白名单模式
        :return: 自动折叠的文件夹集合
        """
        self.clear()
        
        visual_items, auto_collapsed = TreeBuilder.build_visual_data(flat_files, collapsed_folders)
        
        for item in visual_items:
            if item["type"] == "file":
                all_files_map[item["rel_path"]] = item["full_path"]
                selection_state[item["rel_path"]] = not whitelist_mode
            self._create_row(item, selection_state)
        
        return auto_collapsed
    
    def _create_row(self, item: dict, selection_state: dict) -> None:
        """创建树行"""
        is_file = (item["type"] == "file")
        rel_path = item.get("rel_path")
        is_collapsed = item.get("collapsed", False)
        level = rel_path.count(os.sep) if rel_path else 0
        
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
        
        collapse_btn = None
        if not is_file:
            collapse_char = "▸" if is_collapsed else "▾"
            collapse_btn = tk.Label(
                row_frame,
                text=collapse_char,
                bg=COLORS["bg_panel"],
                fg=COLORS["fg_secondary"],
                font=("Segoe UI", 10),
                width=2,
                anchor="center",
                cursor="hand2"
            )
            collapse_btn.pack(side=tk.LEFT)
            collapse_btn.bind("<Button-1>", lambda e: self.on_toggle_collapse(rel_path))
        
        icon_char = "📄" if is_file else "📁"
        if is_file and name_text.endswith(".py"):
            icon_char = "🐍"
        icon_color = COLORS["icon_file"] if is_file else COLORS["icon_folder"]
        if not is_file and is_collapsed:
            icon_color = COLORS["fg_secondary"]
        
        icon_lbl = tk.Label(
            row_frame,
            text=icon_char,
            bg=COLORS["bg_panel"],
            fg=icon_color,
            font=("Segoe UI Emoji", 11),
            width=2,
            anchor="center"
        )
        icon_lbl.pack(side=tk.LEFT)
        
        is_selected = self._get_visual_selected_state(rel_path, is_file, selection_state) if rel_path else True
        curr_font = FONTS["tree_norm"] if is_selected else FONTS["tree_strike"]
        curr_fg = COLORS["fg_text"] if is_selected else COLORS["text_ignore"]
        if not is_file and is_selected:
            curr_fg = COLORS["folder_fg"]
        
        name_lbl = tk.Label(
            row_frame,
            text=name_text,
            bg=COLORS["bg_panel"],
            fg=curr_fg,
            font=curr_font,
            anchor="w"
        )
        name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)
        
        if rel_path:
            self.path_to_label[rel_path] = {
                "label": name_lbl,
                "frame": row_frame,
                "icon": icon_lbl,
                "spacer": spacer,
                "collapse_btn": collapse_btn,
                "is_file": is_file,
                "collapsed": is_collapsed
            }
        
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
    
    def _get_visual_selected_state(self, rel_path: str, is_file: bool, selection_state: dict) -> bool:
        """获取视觉选中状态"""
        if is_file:
            return selection_state.get(rel_path, True)
        
        affected_files = [
            path for path in self.path_to_label
            if path.startswith(rel_path + os.sep) and self.path_to_label[path]["is_file"]
        ]
        if not affected_files:
            return True
        
        return any(selection_state.get(path, True) for path in affected_files)
    
    def update_item_visual(self, rel_path: str, is_selected: bool) -> None:
        """更新单个项目的视觉状态"""
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
    
    def refresh_visual(self, selection_state: dict) -> None:
        """刷新所有项目的视觉状态"""
        for rel_path in self.path_to_label:
            widgets = self.path_to_label[rel_path]
            is_selected = self._get_visual_selected_state(rel_path, widgets["is_file"], selection_state)
            self.update_item_visual(rel_path, is_selected)