#在远方的时候，又想你到泪流
#这矫情的语法结构，经历过的人会懂

import os
import sys
import json
import tkinter as tk
from tkinter import filedialog
import subprocess
import time

# --- 配置区域 (已修改为读取 config.json) ---

# 1. 确定配置文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'Core','config.json')

# 2. 读取配置
if not os.path.exists(config_path):
    print(f"❌ 错误：找不到配置文件 config.json")
    print(f"请访问https://github.com/ChaoPhone/AI_CodeFeeder_by_py下载，并确保配置文件位于: {current_dir}")
    input("按回车键退出...")
    sys.exit(1)

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
except Exception as e:
    print(f"❌ 配置文件格式错误: {e}")
    sys.exit(1)

# 3. 映射变量 (注意类型转换)
# Set 用于快速查找 (O(1))
ALLOWED_EXTENSIONS = set(config_data.get('allowed_extensions', []))
IGNORE_DIRS = set(config_data.get('ignore_dirs', []))
IGNORE_FILES = set(config_data.get('ignore_files', []))

# Tuple 用于 startswith 方法
IGNORE_PREFIXES = tuple(config_data.get('ignore_prefixes', []))

# 4. 强制忽略脚本自身 (防止递归读取)
IGNORE_FILES.add(os.path.basename(__file__))

#5 获取最新版本号
VERSION_LATEST = "\n".join(config_data.get('version', ["Unknown Version"]))


# --- 核心逻辑  ---

def is_text_file(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def get_clipboard_content(root):
    """安全获取剪贴板内容"""
    try:
        # 尝试获取剪贴板的文本内容
        return root.clipboard_get()
    except:
        # 如果剪贴板为空、非文本或无法访问，返回空字符串，防止报错
        return ""

def get_sorted_file_list(start_path):
    """扫描并返回所有符合条件的文件路径列表"""
    file_list = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for f in files:
            # 1. 检查完全匹配的黑名单
            if f in IGNORE_FILES: continue
            if f.endswith('_Codes.md'): continue

            # 2. 检查前缀黑名单
            if any(f.startswith(prefix) for prefix in IGNORE_PREFIXES): continue

            if is_text_file(f):
                rel_path = os.path.relpath(os.path.join(root, f), start_path)
                file_list.append(rel_path)
    return sorted(file_list)


def generate_tree(start_path, files_to_include):
    """生成目录树结构的字符串"""
    tree_str = "# 文件目录树 Project Directory Structure\n\n```text\n"
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
    abs_path = os.path.abspath(path)
    abs_path = os.path.normpath(abs_path)

    print(f"📂 正在打开所在文件夹: {abs_path}")
    try:
        if os.name == 'nt':
            subprocess.Popen(f'explorer /select,"{abs_path}"')
        else:
            print("非 Windows 系统，请手动打开目录。")
    except Exception as e:
        print(f"⚠️ 无法自动打开文件夹: {e}")


def merge_files(start_path, output_path, target_files, error_log=None):
    """执行合并写入"""
    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:

            # 1. 先写目录树 (保持不变)
            outfile.write(generate_tree(start_path, target_files))

            # 2. 【修改位置】报错信息移到这里 (目录树下方)
            if error_log:
                outfile.write("\n# 🛑 报错信息 Compilation Error Log\n")
                outfile.write("> Auto-detected from clipboard\n\n")
                outfile.write("```text\n")
                outfile.write(error_log)
                outfile.write("\n```\n\n---\n\n")

            # 3. 再写代码内容 (保持不变)
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




if __name__ == "__main__":
    print("=" * 50)
    print(VERSION_LATEST)
    print("=" * 50)

    # --- 初始化 Tkinter ---
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    # 1. 选择目录
    print("请在资源管理器中选择目标主目录ヾ(≧▽≦*)o")
    print("支持自动添加报错信息喔！快去复制吧~")
    project_root = filedialog.askdirectory(title="请选择要分析的目标主目录(～￣▽￣)～")

    if not project_root:
        print("❌ 未选择目录，程序退出。")
        root.destroy()
    else:

        files_to_process = get_sorted_file_list(project_root)

        if not files_to_process:
            print("❌ 未找到符合条件的代码文件。")
            root.destroy()
        else:
            print(f"即将合并以下 {len(files_to_process)} 个文件:")
            for f in files_to_process:
                print(f" [📄] {f}")
            print("-" * 50)

            print(f"扫描目标: {project_root}")
            # --- 自动检测剪贴板 ---
            clipboard_text = get_clipboard_content(root)
            error_content = None

            # 检测是否以 20 个等号开头
            if clipboard_text and clipboard_text.startswith("=" * 20):
                print("📋 检测到剪贴板包含编译报错信息 (以 '====' 开头)，已自动提取。")
                error_content = clipboard_text
            else:
                print("📋 剪贴板内容不符合报错格式，已跳过。")

            # --- 【修改点 2】倒计时自动生成 ---
            print("\n⏳ 2秒后自动生成文档...")
            time.sleep(1)
            print("\n⏳ 1秒后自动生成文档...")
            time.sleep(1)
            print("\n✅ 文档已经生成...")
            time.sleep(1)


            default_filename = f"{os.path.basename(project_root)}_Codes.md"
            output_path = filedialog.asksaveasfilename(
                title="请选择输出文档的位置和名称",
                initialdir=project_root,
                initialfile=default_filename,
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
            )

            merge_files(project_root, output_path, files_to_process, error_content)

            # --- 【新增】FeederGap 衔接逻辑 ---
            if os.path.exists(output_path):
                # 简单估算 Token (1 token ≈ 4 chars)
                with open(output_path, 'r', encoding='utf-8') as f:
                    content_len = len(f.read())

                est_tokens = content_len // 4

                print("\n" + "=" * 50)
                print(f"📊 当前文档预估 Token 数: {est_tokens}")

                # 给出评价
                if est_tokens > 50000:
                    print("⚠️ (文件较大，建议精简)")
                else:
                    print("✅ (大小适中)")

                print("=" * 50)

                # 询问是否启动 FeederGap
                gap_choice = input("✂️ 是否启用 FeederGap 对文件做减法 (去除头文件/注释/杂项)? (y/n): ")

                if gap_choice.lower() == 'y':
                    try:
                        from Core import FeederGap

                        FeederGap.run_gap_process(output_path)
                    except ImportError:
                        print("❌ 错误：未找到 FeederGap.py，请确保它在同一目录下。")
                    except Exception as e:
                        print(f"❌ 运行出错: {e}")
                else:
                    print("已保持原样。")



            root.destroy()