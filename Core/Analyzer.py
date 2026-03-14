import os
from .CodeCleaner import clean_content_deeply, remove_license_header, is_junk_filename


class ProjectManager:
    def __init__(self, config):
        self.cfg = config

    def scan_directory(self, start_path):
        """
        扫描目录，返回所有符合条件的文件列表
        返回格式: [(rel_path, full_path), ...]
        """
        file_list = []
        ignore_files_dynamic = self.cfg.ignore_files.copy()

        for root, dirs, files in os.walk(start_path):
            # 1. 过滤文件夹 (原地修改 dirs 以阻止递归)
            dirs[:] = [d for d in dirs if d not in self.cfg.ignore_dirs]

            for f in files:
                if f in ignore_files_dynamic: continue

                # 前缀过滤
                if any(f.startswith(prefix) for prefix in self.cfg.ignore_prefixes): continue

                # 扩展名过滤
                ext = os.path.splitext(f)[1].lower()
                if ext in self.cfg.allowed_exts:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, start_path)
                    file_list.append((rel_path, full_path))

        # 按相对路径排序
        return sorted(file_list, key=lambda x: x[0])

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