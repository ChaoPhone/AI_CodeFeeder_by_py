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
                # 过滤输出文件
                if f.endswith('_Codes.md') or f.endswith('_Gap.md') or f.endswith('_Skeleton.md'): continue

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

    def _generate_tree_text(self, start_path, selected_rel_paths):
        """
        生成 Unix 风格的 ASCII 目录树 (Tree Command Style)
        Example:
        Project/
        ├── Core/
        │   ├── Analyzer.py
        │   └── config.json
        └── main.py
        """
        # 1. 构建嵌套字典树结构
        tree_structure = {}
        for path in selected_rel_paths:
            parts = path.split(os.sep)
            current_level = tree_structure
            for part in parts:
                # setdefault 返回键对应的值，如果键不存在则设为 {}
                current_level = current_level.setdefault(part, {})

        # 2. 递归渲染
        lines = []
        root_name = os.path.basename(start_path) + "/"
        lines.append(root_name)

        self._render_tree(tree_structure, "", lines)

        return "# Project Directory Structure\n\n```text\n" + "\n".join(lines) + "\n```\n\n---\n\n"

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

    def pipeline_write(self, start_path, file_items, output_path, mode='normal', error_log=None):
        """
        核心流水线：写入格式严格对齐
        """
        selected_rels = [item[0] for item in file_items]

        with open(output_path, 'w', encoding='utf-8') as outfile:
            # 1. 写入目录树 (新版 ASCII 风格)
            outfile.write(self._generate_tree_text(start_path, selected_rels))

            # 2. 写入报错日志 (如果有)
            if error_log:
                outfile.write("\n# 🛑 Compilation Error Log\n")
                outfile.write("> Auto-detected from clipboard\n\n")
                outfile.write("```text\n")
                outfile.write(error_log)
                outfile.write("\n```\n\n---\n\n")

            # 3. 遍历并处理文件
            for rel_path, full_path in file_items:
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()

                    # === 清洗逻辑 ===
                    final_content = content
                    ext = os.path.splitext(rel_path)[1][1:] or 'text'

                    if mode in ['gap', 'skeleton']:
                        if is_junk_filename(rel_path): continue

                        final_content = remove_license_header(final_content)
                        aggressive = (mode == 'skeleton')
                        final_content = clean_content_deeply(final_content, aggressive_mode=aggressive)

                        if len(final_content.strip()) < 5: continue

                    # === 写入逻辑 ===
                    outfile.write(f"## File: {rel_path}\n\n")
                    outfile.write(f"```{ext}\n{final_content}\n```\n\n---\n\n")

                except Exception as e:
                    print(f"Skipping {rel_path}: {e}")