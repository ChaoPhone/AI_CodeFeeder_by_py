import os
import tkinter as tk
from tkinter import filedialog

# --- 配置区域 ---

# 1. 包含的文件后缀 (已添加 .cs 和 Unity 相关)
ALLOWED_EXTENSIONS = {
    '.py', '.java', '.cpp', '.c', '.h', '.js', '.ts', '.html','.m'
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
    'cmake-build-debug', 'cmake-build-release',  # CLion 特有
    'gradle', '.gradle',

    # --- Unity 缓存 (如果有 Unity 项目) ---
    'Library', 'Temp', 'Logs', 'UserSettings', 'Packages',

    # --- STM32/嵌入式 核心屏蔽区 (关键修改) ---
    'Drivers',  # 屏蔽几万行的 HAL 库文件
    'Middlewares',  # 屏蔽 FreeRTOS 等第三方源码
    'CMSIS',  # 屏蔽 ARM 核心接口文件
    'MDK-ARM',  # 屏蔽 Keil 工程文件
    'EWARM',  # 屏蔽 IAR 工程文件
    'cmake',  # 屏蔽 CubeMX 生成的 CMake 脚本
    'DebugVals',  # 屏蔽调试临时数据文件夹

    # --- 其他特定无需分析的目录 ---
    'Docs', 'Doc',  # 文档目录通常不需要代码分析
}

# 3. [新增] 忽略以这些前缀开头的文件 (专门针对 CubeMX 生成的杂文件)
IGNORE_PREFIXES = {
    'stm32f4xx_it',  # 忽略中断文件 (.c/.h)
    'system_stm32f4xx',  # 忽略系统时钟初始化
    'stm32f4xx_hal_conf',  # 忽略 HAL 库配置
    'stm32f4xx_hal_msp',  # 忽略 MSP 硬件初始化 (视情况而定，一般不改)
    'sysmem',  # 内存管理存根
    'syscalls',  # 系统调用存根
    'stm32f4xx_hal_timebase_tim.c',
    'FreeRTOSConfig.h',
}

# 4. 忽略的文件 (脚本自身 + 潜在的旧输出文件)
# 注意：由于输出文件名现在是动态的，这里主要保留脚本自身的过滤
IGNORE_FILES = {
    os.path.basename(__file__),
    'project_context_for_notebooklm.md'  # 保留旧版默认名以防万一
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
            # 1. 检查完全匹配的黑名单
            if f in IGNORE_FILES: continue

            # 额外检查：如果文件名包含 '_Codes.md' 且在根目录，可能也是上次生成的，建议忽略
            if f.endswith('_Codes.md'): continue

            # 2. 检查前缀黑名单
            if any(f.startswith(prefix) for prefix in IGNORE_PREFIXES):
                continue

            if is_text_file(f):
                # 保存相对路径
                rel_path = os.path.relpath(os.path.join(root, f), start_path)
                file_list.append(rel_path)
    return sorted(file_list)


def generate_tree(start_path, files_to_include):
    """生成目录树结构的字符串 (仅包含被选中的文件)"""
    tree_str = "# Project Directory Structure\n\n```text\n"
    tree_str += f"{os.path.basename(start_path)}/\n"

    # 将文件列表转换为集合以便快速查找
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
            # 只有在最终列表里的文件才显示在树中，保持树与内容一致
            if file_rel_path in included_set:
                tree_str += f"{subindent}{f}\n"

    tree_str += "```\n\n---\n\n"
    return tree_str


def merge_files(start_path, output_path, target_files):
    """执行合并写入"""
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            # 1. 写入目录树
            outfile.write(generate_tree(start_path, target_files))

            # 2. 写入文件内容
            print(f"\n正在写入 {len(target_files)} 个文件...")
            for rel_path in target_files:
                full_path = os.path.join(start_path, rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()

                        outfile.write(f"## File: {rel_path}\n\n")

                        ext = os.path.splitext(rel_path)[1][1:]
                        if ext == '': ext = 'text'

                        outfile.write(f"```{ext}\n")
                        outfile.write(content)
                        outfile.write("\n```\n\n")
                        outfile.write("---\n\n")
                except Exception as e:
                    print(f"读取错误: {rel_path} - {e}")

        print(f"\n✅ 成功！文件已生成: {output_path}")
    except Exception as e:
        print(f"\n❌ 写入失败: {e}")


def print_clean_config():
    """打印清爽的配置信息"""
    exts = ", ".join(sorted([e for e in ALLOWED_EXTENSIONS]))
    dirs = ", ".join(sorted([d for d in IGNORE_DIRS]))

    print("-" * 50)
    print(f"包含后缀 (.): {exts}")
    print(f"忽略目录 (/): {dirs}")
    print("-" * 50)


if __name__ == "__main__":
    # --- 版本信息 ---
    print("AI_CodeFeeder V1.0.5")
    print("Coded by ChaoPhone")
    print("-" * 50)

    # --- 初始化 Tkinter ---
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 【新增优化】强制让弹窗置顶，避免被编辑器挡住
    root.attributes('-topmost', True)

    # 1. 选择目录
    print("等待用户选择目标主目录...")
    project_root = filedialog.askdirectory(title="请选择要分析的目标主目录")

    if not project_root:
        print("❌ 未选择目录，程序退出。")
    else:
        # 2. 打印配置
        print_clean_config()


        # 3. 预扫描
        print("\n🔍 正在预扫描工程...")
        files_to_process = get_sorted_file_list(project_root)

        if not files_to_process:
            print("❌ 未找到符合条件的代码文件，请检查配置。")
        else:
            print(f"即将合并以下 {len(files_to_process)} 个文件:")
            for f in files_to_process:
                print(f" [📄] {f}")

            # 4. 确认并选择输出位置
            print(f"扫描目标: {project_root}")
            confirm = input("\n按回车键选择保存位置并生成 Markdown，输入 'n' 退出: ")

            if confirm.lower() != 'n':
                # 默认文件名: 目录名_Codes.md
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
                    print("操作已取消（未选择保存路径）。")
            else:
                print("操作已取消。")