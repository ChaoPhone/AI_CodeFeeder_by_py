import tkinter as tk
import math
from .Theme import COLORS, FONTS

class RoundedFrame(tk.Canvas):
    """带圆角的自定义分栏框组件"""
    def __init__(self, parent, bg=COLORS["bg_panel"], border_color=COLORS["border"], radius=COLORS["radius_panel"], padding=2, **kwargs):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.bg = bg
        self.border_color = border_color
        self.radius = radius
        self.padding = padding
        self.inner_frame = tk.Frame(self, bg=bg)
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        r = self.radius

        self.create_rounded_rect(0, 0, w, h, r, fill=self.bg, outline=self.border_color, width=1)

        inset = r // 2 if r > 6 else 4
        self.create_window(w//2, h//2, window=self.inner_frame, width=w-inset*2, height=h-inset*2)

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
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, cursor="hand2", **kwargs)
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
    """标签云容器 - 动态管理多个 TagButton"""
    def __init__(self, parent, items, on_remove_item, on_add_item, add_placeholder="添加...", **kwargs):
        super().__init__(parent, bg=parent["bg"], **kwargs)
        self.items = list(items)
        self.on_remove_item = on_remove_item
        self.on_add_item = on_add_item
        self.add_placeholder = add_placeholder
        self.tag_widgets = []
        self.add_entry = None
        self._draw()

    def _draw(self):
        # 清除旧组件
        for widget in self.tag_widgets:
            widget.destroy()
        self.tag_widgets.clear()

        # 渲染标签
        for item in self.items:
            tag = TagButton(self, item, lambda x: self._handle_remove(x))
            tag.pack(side=tk.LEFT, padx=3, pady=3)
            self.tag_widgets.append(tag)

        # 添加输入框
        self.add_entry = tk.Entry(
            self, width=8, bg=COLORS["bg_input"], fg=COLORS["fg_secondary"],
            insertbackground=COLORS["fg_text"], relief=tk.FLAT,
            font=("Microsoft YaHei UI", 9)
        )
        self.add_entry.insert(0, self.add_placeholder)
        self.add_entry.pack(side=tk.LEFT, padx=3, pady=3)
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
