import tkinter as tk
import math
from .Theme import COLORS, FONTS

class RoundedFrame(tk.Canvas):
    """带圆角的自定义分栏框组件"""
    def __init__(self, parent, bg=COLORS["bg_panel"], border_color=COLORS["border"], radius=COLORS["radius_panel"], padding=2, **kwargs):
        # 显式获取父容器背景色
        parent_bg = parent.cget("bg") if hasattr(parent, 'cget') else COLORS["bg_main"]
        # 设置初始高度为 60，防止 Canvas 为 0 高度时不可见
        super().__init__(parent, bg=parent_bg, highlightthickness=0, height=60, **kwargs)
        self.bg = bg
        self.border_color = border_color
        self.radius = radius
        self.padding = padding

        # 内部容器
        self.inner_frame = tk.Frame(self, bg=bg)

        # 防抖：缓存上次尺寸
        self._last_size = (0, 0)

        self.bind("<Configure>", self._draw_debounced)

        # 延迟监听 inner_frame 内容变化
        self.after(50, self._setup_inner_watch)

    def _setup_inner_watch(self):
        """延迟设置 inner_frame 监听"""
        self.inner_frame.bind("<Configure>", self._on_inner_change)
        # 初始绘制
        self._draw_actual()

    def _on_inner_change(self, event=None):
        """inner_frame 内容变化时更新高度"""
        self.update_idletasks()
        req_h = self.inner_frame.winfo_reqheight()
        # 设置 Canvas 高度
        target_h = max(req_h + self.radius + 8, 60)
        self.config(height=target_h)
        self._draw_actual()

    def _draw_debounced(self, event=None):
        """带防抖的重绘"""
        w, h = self.winfo_width(), self.winfo_height()
        if abs(w - self._last_size[0]) > 2 or abs(h - self._last_size[1]) > 2:
            self._last_size = (w, h)
            self._draw_actual()

    def _draw_actual(self):
        """实际重绘逻辑"""
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        r = self.radius

        if w < 10 or h < 10:
            return

        self.create_rounded_rect(0, 0, w, h, r, fill=self.bg, outline=self.border_color, width=1)

        inset = r // 2 if r > 6 else 4
        # 嵌入 inner_frame
        self.create_window(inset, inset, window=self.inner_frame, anchor="nw", width=w-inset*2)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        if r <= 0: return self.create_rectangle(x1, y1, x2, y2, **kwargs)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if r > w/2: r = w/2
        if r > h/2: r = h/2

        points = []
        for i in range(180, 271, 10):
            a = math.radians(i)
            points.extend([x1 + r + r * math.cos(a), y1 + r + r * math.sin(a)])
        for i in range(270, 361, 10):
            a = math.radians(i)
            points.extend([x2 - r + r * math.cos(a), y1 + r + r * math.sin(a)])
        for i in range(0, 91, 10):
            a = math.radians(i)
            points.extend([x2 - r + r * math.cos(a), y2 - r + r * math.sin(a)])
        for i in range(90, 181, 10):
            a = math.radians(i)
            points.extend([x1 + r + r * math.cos(a), y2 - r + r * math.sin(a)])

        return self.create_polygon(points, **kwargs)

class RoundedButton(tk.Canvas):
    """带圆角的自定义按钮组件 (VS Code 风格)"""
    def __init__(self, parent, text, command,
                 bg=COLORS["bg_input"], fg=COLORS["fg_text"],
                 hover_bg=COLORS["bg_hover"], active_bg=COLORS["bg_active"],
                 radius=COLORS["radius_btn"], font=FONTS["ui"],
                 width=None, height=None, padding_x=16, padding_y=6, **kwargs):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, cursor="hand2", **kwargs)
        self.text = text
        self.command = command
        self.base_bg = bg
        self.curr_bg = bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.fg = fg
        self.radius = radius
        self.font = font
        self.state = tk.NORMAL

        temp_label = tk.Label(text=text, font=font)
        self.req_w = (width or temp_label.winfo_reqwidth() + padding_x * 2)
        self.req_h = (height or temp_label.winfo_reqheight() + padding_y * 2)
        self.config(width=self.req_w, height=self.req_h)

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click_down)
        self.bind("<ButtonRelease-1>", self._on_click_up)

    def config(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs.pop("text")
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            self.configure(cursor="arrow" if self.state == tk.DISABLED else "hand2")
        if "bg" in kwargs:
            self.base_bg = kwargs.pop("bg")
            self.curr_bg = self.base_bg
        if "fg" in kwargs:
            self.fg = kwargs.pop("fg")

        if kwargs:
            super().configure(**kwargs)
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()

        draw_fg = self.fg
        if self.state == tk.DISABLED:
            draw_fg = COLORS["fg_secondary"]

        self.create_rounded_rect(0, 0, w, h, self.radius, fill=self.curr_bg, outline=COLORS["border"])
        self.create_text(w//2, h//2, text=self.text, fill=draw_fg, font=self.font)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        if r <= 0: return self.create_rectangle(x1, y1, x2, y2, **kwargs)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if r > w/2: r = w/2
        if r > h/2: r = h/2
        points = []
        for i in range(180, 271, 10):
            a = math.radians(i); points.extend([x1 + r + r * math.cos(a), y1 + r + r * math.sin(a)])
        for i in range(270, 361, 10):
            a = math.radians(i); points.extend([x2 - r + r * math.cos(a), y1 + r + r * math.sin(a)])
        for i in range(0, 91, 10):
            a = math.radians(i); points.extend([x2 - r + r * math.cos(a), y2 - r + r * math.sin(a)])
        for i in range(90, 181, 10):
            a = math.radians(i); points.extend([x1 + r + r * math.cos(a), y2 - r + r * math.sin(a)])
        return self.create_polygon(points, **kwargs)

    def _on_enter(self, e):
        if self.state == tk.DISABLED: return
        self.curr_bg = self.hover_bg
        self._draw()

    def _on_leave(self, e):
        if self.state == tk.DISABLED: return
        self.curr_bg = self.base_bg
        self._draw()

    def _on_click_down(self, e):
        if self.state == tk.DISABLED: return
        self.curr_bg = self.active_bg
        self._draw()

    def _on_click_up(self, e):
        if self.state == tk.DISABLED: return
        self.curr_bg = self.hover_bg
        self._draw()
        if self.command: self.command()


class TagButton(tk.Canvas):
    """标签按钮组件 - 用于标签云显示，带删除功能"""
    def __init__(self, parent, text, on_remove,
                 bg=COLORS["bg_input"], fg=COLORS["fg_text"],
                 hover_bg="#3A3D41", remove_bg="#5A2D2D",
                 radius=4, font=("Microsoft YaHei UI", 9), **kwargs):
        # 显式获取父容器背景色
        parent_bg = parent.cget("bg") if hasattr(parent, 'cget') else COLORS["bg_panel"]
        super().__init__(parent, bg=parent_bg, highlightthickness=0, cursor="hand2", **kwargs)
        self.text = text
        self.on_remove = on_remove
        self.base_bg = bg
        self.curr_bg = bg
        self.hover_bg = hover_bg
        self.remove_bg = remove_bg
        self.fg = fg
        self.radius = radius
        self.font = font

        temp_label = tk.Label(text=f"{text} ✕", font=font)
        self.req_w = temp_label.winfo_reqwidth() + 14
        self.req_h = temp_label.winfo_reqheight() + 6
        self.config(width=self.req_w, height=self.req_h)

        self.bind("<Configure>", self._draw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        self.create_rounded_rect(0, 0, w, h, self.radius, fill=self.curr_bg, outline=COLORS["border"])
        self.create_text(w//2, h//2, text=f"{self.text} ✕", fill=self.fg, font=self.font)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        if r <= 0: return self.create_rectangle(x1, y1, x2, y2, **kwargs)
        w, h = abs(x2 - x1), abs(y2 - y1)
        if r > w/2: r = w/2
        if r > h/2: r = h/2
        points = []
        for i in range(180, 271, 10):
            a = math.radians(i); points.extend([x1 + r + r * math.cos(a), y1 + r + r * math.sin(a)])
        for i in range(270, 361, 10):
            a = math.radians(i); points.extend([x2 - r + r * math.cos(a), y1 + r + r * math.sin(a)])
        for i in range(0, 91, 10):
            a = math.radians(i); points.extend([x2 - r + r * math.cos(a), y2 - r + r * math.sin(a)])
        for i in range(90, 181, 10):
            a = math.radians(i); points.extend([x1 + r + r * math.cos(a), y2 - r + r * math.sin(a)])
        return self.create_polygon(points, **kwargs)

    def _on_enter(self, e):
        self.curr_bg = self.remove_bg
        self._draw()

    def _on_leave(self, e):
        self.curr_bg = self.base_bg
        self._draw()

    def _on_click(self, e):
        if self.on_remove:
            self.on_remove(self.text)


class TagCloudFrame(tk.Frame):
    """标签云容器 - 动态管理多个 TagButton，支持自动换行"""
    def __init__(self, parent, items, on_remove_item, on_add_item, add_placeholder="添加...", max_per_row=5, bg=None, **kwargs):
        # 显式获取或使用默认背景色
        frame_bg = bg if bg is not None else (parent.cget("bg") if hasattr(parent, 'cget') else COLORS["bg_panel"])
        super().__init__(parent, bg=frame_bg, **kwargs)
        self.items = list(items)
        self.on_remove_item = on_remove_item
        self.on_add_item = on_add_item
        self.add_placeholder = add_placeholder
        self.max_per_row = max_per_row  # 每行最大标签数
        self.tag_widgets = []
        self.row_frames = []
        self.add_entry = None
        self._draw()

    def _draw(self):
        # 清除旧组件
        for widget in self.tag_widgets:
            widget.destroy()
        for row in self.row_frames:
            row.destroy()
        self.tag_widgets.clear()
        self.row_frames.clear()

        frame_bg = self.cget("bg")

        # 按行分组渲染标签
        current_row = None
        for idx, item in enumerate(self.items):
            # 每 max_per_row 个标签换一行
            if idx % self.max_per_row == 0:
                current_row = tk.Frame(self, bg=frame_bg)
                current_row.pack(fill=tk.X, pady=2)
                self.row_frames.append(current_row)

            tag = TagButton(current_row, item, lambda x: self._handle_remove(x))
            tag.pack(side=tk.LEFT, padx=3, pady=2)
            self.tag_widgets.append(tag)

        # 添加输入框单独一行
        add_row = tk.Frame(self, bg=frame_bg)
        add_row.pack(fill=tk.X, pady=(6, 2))
        self.row_frames.append(add_row)

        self.add_entry = tk.Entry(
            add_row, width=12, bg=COLORS["bg_input"], fg=COLORS["fg_secondary"],
            insertbackground=COLORS["fg_text"], relief=tk.FLAT,
            font=("Microsoft YaHei UI", 9)
        )
        self.add_entry.insert(0, self.add_placeholder)
        self.add_entry.pack(side=tk.LEFT, padx=3, pady=2)
        self.add_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.add_entry.bind("<FocusOut>", self._on_entry_focus_out)
        self.add_entry.bind("<Return>", self._on_entry_submit)
        self.tag_widgets.append(self.add_entry)

    def _handle_remove(self, item):
        if item in self.items:
            self.items.remove(item)
            if self.on_remove_item:
                self.on_remove_item(item)
            self._draw()

    def _on_entry_focus_in(self, e):
        if self.add_entry.get() == self.add_placeholder:
            self.add_entry.delete(0, tk.END)
            self.add_entry.config(fg=COLORS["fg_text"])

    def _on_entry_focus_out(self, e):
        if not self.add_entry.get():
            self.add_entry.insert(0, self.add_placeholder)
            self.add_entry.config(fg=COLORS["fg_secondary"])

    def _on_entry_submit(self, e):
        new_item = self.add_entry.get().strip()
        if new_item and new_item not in self.items:
            self.items.append(new_item)
            if self.on_add_item:
                self.on_add_item(new_item)
            self.add_entry.delete(0, tk.END)
            self._draw()

    def get_items(self):
        return list(self.items)

    def set_items(self, items):
        self.items = list(items)
        self._draw()
