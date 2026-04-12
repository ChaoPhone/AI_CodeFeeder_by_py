"""
扫描控制器 - 处理文件扫描逻辑
"""
import os
import threading
from typing import Dict, Any, Optional, Callable, Tuple, List

from Core.Analyzer import ProjectManager, ScanCancelledError
from AppUI.models.AppState import AppState
from AppUI.Tree import TreeBuilder
from AppUI.Theme import COLORS, FONTS


class ScanController:
    """
    扫描控制器
    负责目录扫描、文件列表管理、取消机制等
    """
    
    def __init__(self, 
                 manager: ProjectManager,
                 state: AppState,
                 on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
                 on_error: Optional[Callable[[str], None]] = None,
                 on_progress: Optional[Callable[[str], None]] = None):
        self.manager = manager
        self.state = state
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_progress = on_progress
        self._scan_id = 0
    
    def update_manager(self, manager: ProjectManager) -> None:
        """更新 manager 引用（配置更新后调用）"""
        self.manager = manager
    
    def scan_path(self, path: str, source: str = "manual") -> threading.Event:
        """
        启动扫描
        
        :param path: 要扫描的路径
        :param source: 路径来源
        :return: 取消事件对象
        """
        norm_path = os.path.abspath(os.path.normpath(path))
        
        if not os.path.exists(norm_path):
            if self.on_error:
                self.on_error("路径不存在，请重新选择。")
            return threading.Event()
        
        self.state.set_path(norm_path, source)
        self.state.reset_scan_state()
        
        self._scan_id += 1
        current_scan_id = self._scan_id
        
        cancel_event = self.state.create_cancel_event()
        self.state.is_scanning = True
        
        if self.on_progress:
            self.on_progress(f"正在扫描，最多等待 {self.manager.cfg.full_load_timeout_seconds} 秒...")
        
        thread = threading.Thread(
            target=self._scan_thread,
            args=(norm_path, current_scan_id, cancel_event),
            daemon=True
        )
        thread.start()
        
        return cancel_event
    
    def cancel_scan(self) -> None:
        """取消当前扫描"""
        self.state.cancel_scan()
    
    def _scan_thread(self, path: str, scan_id: int, cancel_event: threading.Event) -> None:
        """扫描线程"""
        try:
            result = self.manager.scan_directory(path, cancel_event)
            if self.on_complete:
                self.on_complete(result)
        except ScanCancelledError:
            if self.on_error:
                self.on_error("扫描已取消。")
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
    
    def process_scan_result(self, result: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, str], Dict[str, bool]]:
        """
        处理扫描结果
        
        :param result: 扫描结果
        :return: (visual_items, all_files_map, selection_state)
        """
        if result.get("cancelled"):
            return [], {}, {}
        
        flat_files = result["files"]
        if not flat_files:
            return [], {}, {}
        
        all_files_map = {}
        selection_state = {}
        
        default_selected = not self.state.whitelist_mode
        visual_items, auto_collapsed = TreeBuilder.build_visual_data(
            flat_files, 
            self.state.collapsed_folders,
            self.state.user_expanded_folders
        )
        
        self.state.collapsed_folders = auto_collapsed
        
        for item in visual_items:
            if item["type"] == "file":
                all_files_map[item["rel_path"]] = item["full_path"]
                selection_state[item["rel_path"]] = default_selected
        
        self.state.all_files_map = all_files_map
        self.state.selection_state = selection_state
        
        return visual_items, all_files_map, selection_state
    
    def get_scan_summary(self, result: Dict[str, Any]) -> str:
        """
        获取扫描摘要信息
        
        :param result: 扫描结果
        :return: 摘要文本
        """
        if result.get("cancelled"):
            return "扫描已取消。"
        
        flat_files = result["files"]
        if not flat_files:
            return "扫描完成，但没有找到可加载文件。"
        
        collapsed_count = len(self.state.collapsed_folders)
        collapse_hint = f"，{collapsed_count} 个大文件夹已自动折叠" if collapsed_count > 0 else ""
        scan_mode_text = "全量加载" if result["used_full_load"] else "扩展名过滤加载"
        
        return f"扫描完成，耗时 {result['elapsed']:.2f}s，共 {len(flat_files)} 个文件，{scan_mode_text}{collapse_hint}。"
    
    def toggle_file_selection(self, rel_path: str) -> bool:
        """切换文件选择状态"""
        return self.state.toggle_file_selection(rel_path)
    
    def toggle_folder_selection(self, rel_path: str) -> bool:
        """切换文件夹选择状态"""
        return self.state.toggle_folder_selection(rel_path)
    
    def toggle_whitelist_mode(self) -> bool:
        """切换白名单模式"""
        new_mode = self.state.toggle_whitelist_mode()
        default_selected = not new_mode
        for rel_path in self.state.selection_state:
            self.state.selection_state[rel_path] = default_selected
        return new_mode
    
    def toggle_folder_collapse(self, rel_path: str) -> None:
        """切换文件夹折叠状态"""
        if rel_path in self.state.collapsed_folders:
            self.state.expand_folder(rel_path)
        else:
            self.state.collapse_folder(rel_path)
    
    def get_selected_files(self) -> List[Tuple[str, str]]:
        """获取选中的文件列表"""
        return self.state.get_selected_files()
    
    def get_visual_selected_state(self, rel_path: str, is_file: bool) -> bool:
        """获取视觉选中状态"""
        if is_file:
            return self.state.selection_state.get(rel_path, True)
        
        affected_files = [
            path for path in self.state.all_files_map 
            if path.startswith(rel_path + os.sep)
        ]
        if not affected_files:
            return True
        
        return any(self.state.selection_state.get(path, True) for path in affected_files)