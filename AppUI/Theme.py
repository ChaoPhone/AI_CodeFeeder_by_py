import sys

# --- 统一字体配置 ---
UI_FONT_FAMILY = "Microsoft YaHei UI" if sys.platform == "win32" else "Helvetica"
BASE_FONT_SIZE = 11

FONTS = {
    "h1": (UI_FONT_FAMILY, 14, "bold"),
    "ui": (UI_FONT_FAMILY, 10),
    "ui_bold": (UI_FONT_FAMILY, 10, "bold"),
    "tree_norm": (UI_FONT_FAMILY, BASE_FONT_SIZE),
    "tree_strike": (UI_FONT_FAMILY, BASE_FONT_SIZE, "overstrike"),
}

# --- 现代配色方案 (参考 VS Code Dark Modern) ---
COLORS = {
    "bg_main": "#181818",
    "bg_panel": "#1F1F1F",
    "bg_input": "#2B2B2B",
    "bg_hover": "#2A2D2E",
    "bg_selected": "#37373D",
    "bg_active": "#005FB8",
    
    "fg_text": "#CCCCCC",
    "fg_heading": "#FFFFFF",
    "fg_secondary": "#858585",
    
    "accent": "#007ACC",
    "accent_hov": "#0098FF",
    
    "folder_fg": "#DCB67A",
    "file_fg": "#9CDCFE",
    "border": "#2B2B2B",
    "ignore": "#4D4D4D",
    
    "indent_guide": "#333333",
    "icon_file": "#87D7F2",
    "icon_folder": "#FFC66D",
    "text_ignore": "#666666",
    
    "radius_panel": 10,
    "radius_btn": 6,
}
