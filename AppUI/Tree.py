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
    def _recurse(tree, prefix, result, current_rel_path, path_map):
        keys = sorted(tree.keys())

        for i, key in enumerate(keys):
            is_last = (i == len(keys) - 1)
            val = tree[key]

            # 构建相对路径（用于查找）
            # 注意：如果是根层级，current_rel_path 为空
            new_rel_path = os.path.join(current_rel_path, key) if current_rel_path else key

            # 视觉前缀
            connector = "└── " if is_last else "├── "

            item = {
                'text': f"{prefix}{connector}{key}",
                'indent_prefix': prefix,  # 保留前缀信息备用
                'name': key
            }

            if val == "__FILE__":
                # 是文件
                item['type'] = 'file'
                item['rel_path'] = new_rel_path
                item['full_path'] = path_map.get(new_rel_path)
                result.append(item)
            else:
                # 是文件夹
                item['type'] = 'folder'
                item['text'] += "/"  # 文件夹加斜杠
                item['rel_path'] = None  # 文件夹不可选（或者视作不可选）
                result.append(item)

                # 递归下一层
                next_prefix = prefix + ("    " if is_last else "│   ")
                TreeBuilder._recurse(val, next_prefix, result, new_rel_path, path_map)