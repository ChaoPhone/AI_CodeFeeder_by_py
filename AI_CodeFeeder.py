import os
import tkinter as tk
from tkinter import filedialog
import subprocess

# --- 配置区域 ---

# 1. 包含的文件后缀
ALLOWED_EXTENSIONS = {
    # 修复了这里的逗号问题
    '.py', '.java', '.cpp', '.c', '.h', '.js', '.ts', '.html', '.m',
    '.css', '.sql', '.md', '.yaml', '.yml', '.xml',
    '.cs', '.shader', '.compute', '.cginc', '.txt'
}

# 2. 忽略的目录 (针对 STM32/CLion/Unity 深度优化)
IGNORE_DIRS = {
    # --- 通用开发垃圾 ---
    '.git', '.idea', '.vscode', '__pycache__',
    'venv', 'env', 'node_modules', '.DS_Store',

    # --- 编译生成的中间文件 (最占地方) ---
    'build', 'dist', 'bin', 'obj',
    'cmake-build-debug', 'cmake-build-release',
    'gradle', '.gradle',

    # --- Unity 缓存 (如果有 Unity 项目) ---
    'Library', 'Temp', 'Logs', 'UserSettings', 'Packages',

    # --- STM32/嵌入式 核心屏蔽区 (关键修改) ---
    'Drivers', 'Middlewares', 'CMSIS', 'MDK-ARM', 'EWARM',
    'cmake', 'DebugVals', 'Docs', 'Doc',
}

# 3. 忽略以这些前缀开头的文件 (专门针对 CubeMX 生成的杂文件)
IGNORE_PREFIXES = {
    'stm32f4xx_it', 'system_stm32f4xx', 'stm32f4xx_hal_conf',
    'stm32f4xx_hal_msp', 'sysmem', 'syscalls',
    'stm32f4xx_hal_timebase_tim.c', 'FreeRTOSConfig.h',
}

# 4. 忽略的文件
IGNORE_FILES = {
    os.path.basename(__file__),
    'project_context_for_notebooklm.md'
}


# --- 核心逻辑 ---

def is_text_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def get_sorted_file_list(start_path):
    """扫描并返回所有符合条件的文件路径列表"""
    file_list = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for f in files:
            if f in IGNORE_FILES: continue
            if f.endswith('_Codes.md'): continue
            if any(f.startswith(prefix) for prefix in IGNORE_PREFIXES): continue

            if is_text_file(f):
                rel_path = os.path.relpath(os.path.join(root, f), start_path)
                file_list.append(rel_path)
    return sorted(file_list)


def generate_tree(start_path, files_to_include):
    """生成目录树结构的字符串"""
    tree_str = "# Project Directory Structure\n\n```text\n"
    tree_str += f"{os.path.basename(start_path)}/\n"
    included_set = set(files_to_include)

    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        rel_path = os.path.relpath(root, start_path)
        level = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
        indent = ' ' * 4 * level
        subindent = ' ' * 4 * (level + 1)

        if rel_path != '.':
            tree_str += f"{indent}{os.path.basename(root)}/\n"

        for f in files:
            file_rel_path = os.path.relpath(os.path.join(root, f), start_path)
            if file_rel_path in included_set:
                tree_str += f"{subindent}{f}\n"

    tree_str += "```\n\n---\n\n"
    return tree_str


def show_file_in_explorer(path):
    """[Windows专用] 打开资源管理器并选中文件"""
    # 转换为绝对路径并规范化
    abs_path = os.path.abspath(path)
    abs_path = os.path.normpath(abs_path)

    print(f"📂 正在打开所在文件夹: {abs_path}")
    try:
        # 仅在 Windows 下执行
        if os.name == 'nt':
            subprocess.Popen(f'explorer /select,"{abs_path}"')
        else:
            # Mac/Linux 简单的回退处理 (仅打印路径)
            print("非 Windows 系统，请手动打开目录。")
    except Exception as e:
        print(f"⚠️ 无法自动打开文件夹: {e}")


def merge_files(start_path, output_path, target_files):
    """执行合并写入"""
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            outfile.write(generate_tree(start_path, target_files))
            print(f"\n正在写入 {len(target_files)} 个文件...")

            for rel_path in target_files:
                full_path = os.path.join(start_path, rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        outfile.write(f"## File: {rel_path}\n\n")
                        ext = os.path.splitext(rel_path)[1][1:] or 'text'
                        outfile.write(f"```{ext}\n{content}\n```\n\n---\n\n")
                except Exception as e:
                    print(f"读取错误: {rel_path} - {e}")

        print(f"\n✅ 成功！文件已生成: {output_path}")
        show_file_in_explorer(output_path)

    except Exception as e:
        print(f"\n❌ 写入失败: {e}")


def print_clean_config():
    exts = ", ".join(sorted([e for e in ALLOWED_EXTENSIONS]))
    dirs = ", ".join(sorted([d for d in IGNORE_DIRS]))
    print("-" * 50)
    print(f"包含后缀: {exts}")
    print(f"忽略目录: {dirs}")
    print("-" * 50)


if __name__ == "__main__":
    print("AI_CodeFeeder V1.0.7")
    print("Coded by ChaoPhone")
    print("-" * 50)

    # --- 初始化 Tkinter ---
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)  # 窗口置顶

    # 1. 选择目录
    print("等待用户选择目标主目录...")
    project_root = filedialog.askdirectory(title="请选择要分析的目标主目录")

    if not project_root:
        print("❌ 未选择目录，程序退出。")
        root.destroy()  # 显式销毁窗口
    else:
        print_clean_config()
        print("\n🔍 正在预扫描工程...")
        files_to_process = get_sorted_file_list(project_root)

        if not files_to_process:
            print("❌ 未找到符合条件的代码文件。")
            root.destroy()
        else:
            print(f"即将合并以下 {len(files_to_process)} 个文件:")
            for f in files_to_process:
                print(f" [📄] {f}")

            print(f"扫描目标: {project_root}")
            confirm = input("\n按回车键选择保存位置并生成 Markdown，输入 'n' 退出: ")

            if confirm.lower() != 'n':
                default_filename = f"{os.path.basename(project_root)}_Codes.md"

                output_path = filedialog.asksaveasfilename(
                    title="请选择输出文档的位置和名称",
                    initialdir=project_root,
                    initialfile=default_filename,
                    defaultextension=".md",
                    filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
                )

                if output_path:
                    merge_files(project_root, output_path, files_to_process)
                else:
                    print("操作已取消。")
            else:
                print("操作已取消。")

            root.destroy()  # 程序结束时清理资源