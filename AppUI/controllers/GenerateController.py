"""
生成控制器 - 处理文件生成逻辑
"""
import os
import shutil
import threading
from typing import Dict, Any, Optional, Callable, Tuple, List

from Core.Analyzer import ProjectManager
from AppUI.models.AppState import AppState
from AppUI.Theme import COLORS


class GenerateController:
    """
    生成控制器
    负责文件生成、进度回调、输出路径构建等
    """
    
    SUFFIX_MAP = {
        "normal": "_Codes.md",
        "gap": "_Gap.md",
        "skeleton": "_Skeleton.md"
    }
    
    def __init__(self,
                 manager: ProjectManager,
                 state: AppState,
                 config: Any,
                 on_success: Optional[Callable[[str, int, str], None]] = None,
                 on_error: Optional[Callable[[str], None]] = None,
                 on_progress: Optional[Callable[[int], None]] = None):
        self.manager = manager
        self.state = state
        self.config = config
        self.on_success = on_success
        self.on_error = on_error
        self.on_progress = on_progress
    
    def build_output_path(self, input_path: str, mode: str) -> str:
        """
        构建输出文件路径
        
        :param input_path: 输入路径
        :param mode: 输出模式
        :return: 输出文件路径
        """
        suffix = self.SUFFIX_MAP.get(mode, "_Codes.md")
        norm_path = os.path.abspath(os.path.normpath(input_path))
        
        if os.path.isdir(norm_path):
            parent_dir = os.path.dirname(norm_path)
            base_name = os.path.basename(norm_path)
        else:
            parent_dir = os.path.dirname(norm_path)
            base_name = os.path.splitext(os.path.basename(norm_path))[0]
        
        return os.path.join(parent_dir, f"{base_name}{suffix}")
    
    def generate(self,
                 root_path: str,
                 selected_items: List[Tuple[str, str]],
                 output_path: str,
                 mode: str,
                 ignored_rels: List[str],
                 reveal_source: str = "manual") -> None:
        """
        启动生成
        
        :param root_path: 根路径
        :param selected_items: 选中的文件列表 [(rel_path, full_path), ...]
        :param output_path: 输出路径
        :param mode: 输出模式
        :param ignored_rels: 忽略的文件列表
        :param reveal_source: 来源类型
        """
        if not selected_items:
            if self.on_error:
                self.on_error("请至少选择一个文件！")
            return
        
        thread = threading.Thread(
            target=self._generate_thread,
            args=(root_path, selected_items, output_path, mode, ignored_rels, reveal_source),
            daemon=True
        )
        thread.start()
    
    def _generate_thread(self,
                         root_path: str,
                         items: List[Tuple[str, str]],
                         out_path: str,
                         mode: str,
                         ignored_rels: List[str],
                         reveal_source: str) -> None:
        """生成线程"""
        try:
            def progress_callback(current: int, total: int, filename: str) -> None:
                percent = int((current / total) * 100) if total else 0
                if self.on_progress:
                    self.on_progress(percent)
            
            char_count = self.manager.pipeline_write(
                root_path, items, out_path, mode, 
                None, ignored_rels, progress_callback
            )
            
            if self.config.save_txt:
                shutil.copy2(out_path, os.path.splitext(out_path)[0] + ".txt")
            
            token_count = int(char_count / 3.5)
            
            if self.on_success:
                self.on_success(out_path, token_count, reveal_source)
                
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
    
    def get_selected_items(self) -> List[Tuple[str, str]]:
        """获取选中的文件项"""
        return self.state.get_selected_files()
    
    def get_ignored_items(self) -> List[str]:
        """获取忽略的文件路径列表"""
        return [
            rel_path for rel_path, selected in self.state.selection_state.items()
            if not selected
        ]
    
    def can_generate(self) -> bool:
        """检查是否可以生成"""
        return not self.state.is_scanning and len(self.state.all_files_map) > 0
    
    def get_current_mode(self) -> str:
        """获取当前输出模式"""
        return self.state.output_mode
    
    def set_mode(self, mode: str) -> None:
        """设置输出模式"""
        self.state.set_output_mode(mode)