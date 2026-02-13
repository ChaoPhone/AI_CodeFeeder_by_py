import os


class TreeBuilder:
    """
    负责将扁平的文件路径列表转换为 Unix Tree 风格的视觉列表
    """

    @staticmethod
    def build_visual_data(file_list):
        """
        入口函数
        """
        # 1. 构建树，同时标记叶子节点
        # 结构: { "Folder": { "File": "__FILE__" } }
        tree = {}
        path_map = {rel: full for rel, full in file_list}

        for rel_path, _ in file_list:
            parts = rel_path.split(os.sep)
            curr = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # 叶子节点 (文件)
                    curr[part] = "__FILE__"
                else:
                    # 文件夹
                    curr = curr.setdefault(part, {})

        render_list = []
        TreeBuilder._recurse(tree, "", render_list, "", path_map)
        return render_list

    @staticmethod
    def _recurse(tree, prefix, result, current_rel_path, path_map, is_root=True):
        keys = sorted(tree.keys())

        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            val = tree[key]

            # 构建相对路径（用于查找）
            new_rel_path = os.path.join(current_rel_path, key) if current_rel_path else key

            # 计算视觉层级和图标
            if val == "__FILE__":
                item_type = 'file'
                icon = "📄 "
            else:
                item_type = 'folder'
                icon = "📁 "

            # 缩进线逻辑：
            # prefix 包含了父层级的缩进信息
            # connector 是当前项的连接符
            connector = "└── " if is_last else "├── "
            
            # VS Code 风格：我们不需要复杂的 ASCII 前缀，只需要计算深度和是否为最后一个
            # 但为了保持兼容性，我们先保留文本生成，但在 UI 渲染时可以使用 indent_level
            
            item = {
                'text': f"{prefix}{connector}{icon}{key}",
                'indent_prefix': prefix,
                'name': key,
                'type': item_type,
                'rel_path': new_rel_path,
                'is_last': is_last,
                'depth': len(prefix) // 4 if prefix else 0
            }

            if item_type == 'file':
                item['full_path'] = path_map.get(new_rel_path)
            else:
                item['text'] += "/"

            result.append(item)

            if item_type == 'folder':
                # 递归下一层
                next_prefix = prefix + ("    " if is_last else "│   ")
                TreeBuilder._recurse(val, next_prefix, result, new_rel_path, path_map, is_root=False)