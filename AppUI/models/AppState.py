"""
应用状态模型 - 统一管理所有状态变量
"""
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field
import threading


@dataclass
class AppState:
    """
    应用全局状态模型
    使用 dataclass 简化状态管理，支持类型注解
    """
    
    is_topmost: bool = False
    target_dir: Optional[str] = None
    current_input_path: Optional[str] = None
    current_root_path: Optional[str] = None
    last_path_source: str = "manual"
    scan_request_id: int = 0
    is_scanning: bool = False
    whitelist_mode: bool = False
    
    all_files_map: Dict[str, Any] = field(default_factory=dict)
    selection_state: Dict[str, bool] = field(default_factory=dict)
    path_to_label: Dict[str, Any] = field(default_factory=dict)
    collapsed_folders: Set[str] = field(default_factory=set)
    user_expanded_folders: Set[str] = field(default_factory=set)
    
    scan_cancel_event: Optional[threading.Event] = None
    status_reset_job: Optional[int] = None
    
    output_mode: str = "normal"
    progress_value: int = 0
    
    tray_available: bool = False
    settings_window_open: bool = False
    
    def reset_scan_state(self) -> None:
        """重置扫描相关状态"""
        self.is_scanning = False
        self.scan_request_id += 1
        self.all_files_map.clear()
        self.selection_state.clear()
        self.path_to_label.clear()
        self.collapsed_folders.clear()
        self.user_expanded_folders.clear()
        if self.scan_cancel_event:
            self.scan_cancel_event.set()
        self.scan_cancel_event = None
    
    def create_cancel_event(self) -> threading.Event:
        """创建新的取消事件"""
        self.scan_cancel_event = threading.Event()
        return self.scan_cancel_event
    
    def cancel_scan(self) -> None:
        """取消当前扫描"""
        if self.scan_cancel_event:
            self.scan_cancel_event.set()
    
    def set_path(self, path: str, source: str = "manual") -> None:
        """设置目标路径"""
        self.target_dir = path
        self.current_input_path = path
        self.last_path_source = source
    
    def set_output_mode(self, mode: str) -> None:
        """设置输出模式"""
        if mode in {"normal", "gap", "skeleton"}:
            self.output_mode = mode
    
    def get_output_mode_display(self) -> str:
        """获取输出模式显示名称"""
        mode_map = {"normal": "普通", "gap": "简洁", "skeleton": "骨架"}
        return mode_map.get(self.output_mode, "普通")
    
    def toggle_topmost(self) -> bool:
        """切换置顶状态"""
        self.is_topmost = not self.is_topmost
        return self.is_topmost
    
    def toggle_whitelist_mode(self) -> bool:
        """切换白名单模式"""
        self.whitelist_mode = not self.whitelist_mode
        return self.whitelist_mode
    
    def get_selected_files(self) -> list:
        """获取选中的文件列表"""
        selected = []
        for rel_path, is_selected in self.selection_state.items():
            if is_selected and rel_path in self.all_files_map:
                selected.append((rel_path, self.all_files_map[rel_path]))
        return selected
    
    def select_all_files(self, selected: bool = True) -> None:
        """选择/取消选择所有文件"""
        for rel_path in self.selection_state:
            self.selection_state[rel_path] = selected
    
    def toggle_file_selection(self, rel_path: str) -> bool:
        """切换单个文件选择状态"""
        if rel_path in self.selection_state:
            self.selection_state[rel_path] = not self.selection_state[rel_path]
            return self.selection_state[rel_path]
        return False
    
    def toggle_folder_selection(self, folder_prefix: str) -> bool:
        """切换文件夹下所有文件选择状态"""
        current_state = None
        for rel_path in self.selection_state:
            if rel_path.startswith(folder_prefix):
                if current_state is None:
                    current_state = self.selection_state[rel_path]
                self.selection_state[rel_path] = not current_state
        
        return not current_state if current_state is not None else True
    
    def collapse_folder(self, folder_path: str) -> None:
        """折叠文件夹"""
        self.collapsed_folders.add(folder_path)
    
    def expand_folder(self, folder_path: str) -> None:
        """展开文件夹（标记为用户手动展开）"""
        self.collapsed_folders.discard(folder_path)
        self.user_expanded_folders.add(folder_path)
    
    def is_folder_collapsed(self, folder_path: str) -> bool:
        """检查文件夹是否折叠"""
        return folder_path in self.collapsed_folders