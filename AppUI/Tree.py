import os


class TreeBuilder:
    """
    负责将扁平的文件路径列表转换为 Unix Tree 风格的视觉列表
    支持自动折叠超过阈值的大文件夹
    """

    AUTO_COLLAPSE_THRESHOLD = 10  # 超过此数量自动折叠

    @staticmethod
    def build_visual_data(file_list, collapsed_folders=None):
        """
        入口函数
        collapsed_folders: 需要折叠的文件夹路径集合
        """
        if collapsed_folders is None:
            collapsed_folders = set()

        # 1. 构建树，同时标记叶子节点
        tree = {}
        path_map = {rel: full for rel, full in file_list}

        for rel_path, _ in file_list:
            parts = rel_path.split(os.sep)
            curr = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    curr[part] = "__FILE__"
                else:
                    curr = curr.setdefault(part, {})

        # 自动检测需要折叠的大文件夹
        auto_collapsed = TreeBuilder._find_large_folders(tree, "", TreeBuilder.AUTO_COLLAPSE_THRESHOLD)
        collapsed_folders = collapsed_folders.union(auto_collapsed)

        render_list = []
        TreeBuilder._recurse(tree, "", render_list, "", path_map, collapsed_folders, is_root=True)
        return render_list, collapsed_folders

    @staticmethod
    def _find_large_folders(tree, current_path, threshold):
        """递归查找超过阈值的文件夹"""
        large_folders = set()

        for key, val in tree.items():
            if val != "__FILE__":
                folder_path = os.path.join(current_path, key) if current_path else key
                # 计算该文件夹下的文件数量
                file_count = TreeBuilder._count_files_in_folder(val)
                if file_count > threshold:
                    large_folders.add(folder_path)
                # 继续递归检查子文件夹
                large_folders.update(TreeBuilder._find_large_folders(val, folder_path, threshold))

        return large_folders

    @staticmethod
    def _count_files_in_folder(tree_node):
        """计算文件夹下的文件数量"""
        count = 0
        for key, val in tree_node.items():
            if val == "__FILE__":
                count += 1
            else:
                count += TreeBuilder._count_files_in_folder(val)
        return count

    @staticmethod
    def _recurse(tree, prefix, result, current_rel_path, path_map, collapsed_folders, is_root=True, parent_collapsed=False):
        keys = sorted(tree.keys())

        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            val = tree[key]

            new_rel_path = os.path.join(current_rel_path, key) if current_rel_path else key

            if val == "__FILE__":
                item_type = 'file'
                icon = "📄 "
            else:
                item_type = 'folder'
                icon = "📁 "

            connector = "└── " if is_last else "├── "

            # 检查是否被折叠
            is_collapsed = new_rel_path in collapsed_folders and item_type == 'folder'
            # 如果父文件夹被折叠，则跳过渲染子项
            should_skip = parent_collapsed and not is_root

            if not should_skip:
                # 计算显示名称（折叠时显示提示）
                display_name = key
                if is_collapsed:
                    file_count = TreeBuilder._count_files_in_folder(val)
                    display_name = f"{key} ({file_count} 文件已折叠...)"

                item = {
                    'text': f"{prefix}{connector}{icon}{display_name}",
                    'indent_prefix': prefix,
                    'name': display_name,
                    'original_name': key,
                    'type': item_type,
                    'rel_path': new_rel_path,
                    'is_last': is_last,
                    'depth': len(prefix) // 4 if prefix else 0,
                    'collapsed': is_collapsed
                }

                if item_type == 'file':
                    item['full_path'] = path_map.get(new_rel_path)
                else:
                    item['text'] += "/"

                result.append(item)

            if item_type == 'folder' and not should_skip:
                # 如果文件夹被折叠，不递归渲染子项
                if not is_collapsed:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    TreeBuilder._recurse(val, next_prefix, result, new_rel_path, path_map, collapsed_folders, is_root=False, parent_collapsed=False)
                # 如果父文件夹被折叠，跳过所有子项
            elif should_skip:
                # 父文件夹被折叠时，跳过所有子项渲染
                pass