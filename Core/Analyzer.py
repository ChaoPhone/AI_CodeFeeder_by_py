import os
import time
from .CodeCleaner import clean_content_deeply, remove_license_header, is_junk_filename


class ScanTimeoutError(Exception):
    pass


class ProjectManager:
    def __init__(self, config):
        self.cfg = config

    def scan_directory(self, start_path):
        """
        扫描目录或单文件，并根据扫描复杂度决定是否启用扩展名过滤。
        返回格式:
        {
            "root_path": "...",
            "files": [(rel_path, full_path), ...],
            "used_full_load": bool,
            "elapsed": float,
            "requested_path": "...",
        }
        """
        requested_path = os.path.abspath(os.path.normpath(start_path))
        root_path = requested_path if os.path.isdir(requested_path) else os.path.dirname(requested_path)
        scan_started_at = time.time()

        try:
            file_list = self._scan_path(
                requested_path,
                root_path,
                allow_all_extensions=True,
                started_at=scan_started_at,
                timeout_seconds=self.cfg.full_load_timeout_seconds,
                max_files=self.cfg.full_load_max_files,
            )
            used_full_load = True
        except ScanTimeoutError:
            file_list = self._scan_path(
                requested_path,
                root_path,
                allow_all_extensions=False,
            )
            used_full_load = False

        return {
            "root_path": root_path,
            "requested_path": requested_path,
            "files": sorted(file_list, key=lambda x: x[0]),
            "used_full_load": used_full_load,
            "elapsed": time.time() - scan_started_at,
        }

    def _scan_path(self, target_path, root_path, allow_all_extensions, started_at=None, timeout_seconds=None, max_files=None):
        file_list = []

        if os.path.isfile(target_path):
            self._collect_file(target_path, root_path, file_list, allow_all_extensions)
            return file_list

        self._scan_dir_recursive(
            target_path,
            root_path,
            file_list,
            allow_all_extensions,
            started_at=started_at,
            timeout_seconds=timeout_seconds,
            max_files=max_files,
        )
        return file_list

    def _scan_dir_recursive(self, current_path, root_path, collector, allow_all_extensions, started_at=None, timeout_seconds=None, max_files=None):
        self._check_scan_limits(started_at, timeout_seconds, len(collector), max_files)

        try:
            with os.scandir(current_path) as entries:
                sub_dirs = []
                for entry in entries:
                    self._check_scan_limits(started_at, timeout_seconds, len(collector), max_files)

                    if entry.is_dir(follow_symlinks=False):
                        if entry.name in self.cfg.ignore_dirs:
                            continue
                        sub_dirs.append(entry.path)
                        continue

                    if entry.is_file(follow_symlinks=False):
                        self._collect_file(entry.path, root_path, collector, allow_all_extensions)
        except PermissionError:
            return

        for sub_dir in sub_dirs:
            self._scan_dir_recursive(
                sub_dir,
                root_path,
                collector,
                allow_all_extensions,
                started_at=started_at,
                timeout_seconds=timeout_seconds,
                max_files=max_files,
            )

    def _collect_file(self, full_path, root_path, collector, allow_all_extensions):
        filename = os.path.basename(full_path)

        if filename in self.cfg.ignore_files:
            return

        if any(filename.startswith(prefix) for prefix in self.cfg.ignore_prefixes):
            return

        ext = os.path.splitext(filename)[1].lower()
        if not allow_all_extensions and ext not in self.cfg.allowed_exts:
            return

        rel_path = os.path.relpath(full_path, root_path)
        collector.append((rel_path, full_path))

    def _check_scan_limits(self, started_at, timeout_seconds, current_file_count, max_files):
        if started_at is not None and timeout_seconds is not None:
            if time.time() - started_at > timeout_seconds:
                raise ScanTimeoutError("full scan timed out")

        if max_files and current_file_count > max_files:
            raise ScanTimeoutError("full scan exceeded file limit")

    def _generate_tree_text(self, start_path, selected_rel_paths, title="# Project Directory Structure"):
        """
        生成 Unix 风格的 ASCII 目录树 (Tree Command Style)
        """
        # 1. 构建嵌套字典树结构
        tree_structure = {}
        for path in selected_rel_paths:
            parts = path.split(os.sep)
            current_level = tree_structure
            for part in parts:
                current_level = current_level.setdefault(part, {})

        # 2. 递归渲染
        lines = []
        root_name = os.path.basename(start_path) + "/"
        lines.append(root_name)

        self._render_tree(tree_structure, "", lines)

        return f"{title}\n\n```text\n" + "\n".join(lines) + "\n```\n\n---\n\n"

    def _render_tree(self, tree, prefix, lines):
        """递归渲染辅助函数"""
        # 排序：让文件夹和文件混排，或者文件夹在前。这里使用默认字母排序。
        keys = sorted(tree.keys())

        for i, key in enumerate(keys):
            is_last_item = (i == len(keys) - 1)
            subtree = tree[key]

            # 确定连接符
            connector = "└── " if is_last_item else "├── "

            # 判断是文件夹还是文件
            # 在我们的构建逻辑中，如果 subtree 是非空字典，它通常是文件夹（但也可能是文件被误判，取决于路径结构）
            # 更好的判断方式：如果 key 在原文件列表中是叶子节点，它就是文件。
            # 但简单来说：如果 subtree 有内容，它不仅是文件还是父级目录。
            # 视觉上，我们给看起来像文件夹的（有子节点）或者我们逻辑中的非叶子节点加 /

            display_name = key
            if subtree:
                display_name += "/"

            lines.append(f"{prefix}{connector}{display_name}")

            if subtree:
                # 计算下一级的前缀
                extension = "    " if is_last_item else "│   "
                self._render_tree(subtree, prefix + extension, lines)

    def pipeline_write(self, start_path, file_items, output_path, mode='normal', error_log=None, ignored_rels=None, progress_callback=None):
        """
        核心流水线：写入格式严格对齐
        支持进度回调 (progress_callback(current, total, filename))
        返回生成的总字符数，用于估算 Token
        """
        selected_rels = [item[0] for item in file_items]
        total_content = ""

        # 1. 生成目录树
        tree_text = self._generate_tree_text(start_path, selected_rels)
        total_content += tree_text

        # 1.5 生成忽略目录树
        if ignored_rels:
            ignored_tree_text = self._generate_tree_text(start_path, ignored_rels, title="# Ignored Files & Directories")
            total_content += ignored_tree_text

        # 2. 生成报错日志
        if error_log:
            err_text = f"\n# 🛑 Compilation Error Log\n> Auto-detected from clipboard\n\n```text\n{error_log}\n```\n\n---\n\n"
            total_content += err_text

        # 3. 遍历并处理文件内容（带进度回调）
        total_files = len(file_items)
        for idx, (rel_path, full_path) in enumerate(file_items):
            try:
                # 流式读取大文件（分块读取）
                content = self._read_file_streaming(full_path)

                # === 清洗逻辑 ===
                final_content = content
                file_ext = os.path.splitext(rel_path)[1].lower()
                ext_for_md = file_ext[1:] or 'text'

                if mode in ['gap', 'skeleton']:
                    if is_junk_filename(rel_path): continue
                    final_content = remove_license_header(final_content)
                    aggressive = (mode == 'skeleton')
                    final_content = clean_content_deeply(final_content, file_ext, aggressive_mode=aggressive)
                    if len(final_content.strip()) < 5: continue

                # === 累加逻辑 ===
                file_section = f"## File: {rel_path}\n\n```{ext_for_md}\n{final_content}\n```\n\n---\n\n"
                total_content += file_section

                # 报告进度
                if progress_callback:
                    progress_callback(idx + 1, total_files, rel_path)

            except Exception as e:
                print(f"Skipping {rel_path}: {e}")

        # 4. 一次性写入文件
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(total_content)
        
        return len(total_content)

    def _read_file_streaming(self, file_path, chunk_size=8192):
        """
        流式读取文件，避免大文件一次性加载到内存
        对于小文件直接读取，对于大文件分块读取
        """
        file_size = os.path.getsize(file_path)
        # 小于5MB的文件直接读取
        if file_size < 5 * 1024 * 1024:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        # 大文件流式读取
        chunks = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
        return ''.join(chunks)
