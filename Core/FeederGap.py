# FeederGap.py
# 专门用于对 AI_CodeFeeder 生成的 Markdown 进行“瘦身”
# 功能：去除头文件引用、块注释、压缩空行、过滤杂项文件

import os
import re
import sys


def clean_code_content(content):
    """
    对代码内容进行清洗的核心逻辑
    """
    # 1. 去除 /**/ 样式的块注释 (非贪婪匹配，跨行模式)
    # 这里的 pattern 匹配 /* 开始，到 */ 结束的内容
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)

    # 2. 去除头文件引用 (#include ...)
    # 匹配以 # 开头，中间可能有空格，紧接 include，直到行尾
    content = re.sub(r'^\s*#\s*include.*$', '', content, flags=re.MULTILINE)

    # 3. 压缩连续空行
    # 将连续2个及以上的换行符替换为2个换行符（保留段落感，但去除大段空白）
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content


def is_junk_filename(filename):
    """
    使用正则表达式判断文件名是否包含 stm32, system_ 等杂项
    """
    # 这里定义过滤规则，忽略大小写
    pattern = r'(stm32|system_|main\.h|stm32f4xx)'
    return bool(re.search(pattern, filename, re.IGNORECASE))


def run_gap_process(md_path):
    print("-" * 50)
    print("✂️ 正在启动 FeederGap 精简程序...")

    if not os.path.exists(md_path):
        print(f"❌ 错误：找不到文件 {md_path}")
        return

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            full_content = f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    # --- 核心处理流程 ---

    # 1. 拆分文档
    # 使用 "## File: " 作为分隔符拆分
    # parts[0] 是目录树和报错信息（保留）
    # parts[1:] 是各个具体的代码文件块
    separator = "## File: "
    parts = full_content.split(separator)

    header_section = parts[0]
    file_sections = parts[1:]

    cleaned_sections = []
    removed_count = 0

    print(f"🔍 正在分析 {len(file_sections)} 个文件块...")

    for section in file_sections:
        # 提取第一行作为文件名（直到换行符）
        newline_index = section.find('\n')
        if newline_index == -1:
            continue

        file_path = section[:newline_index].strip()
        code_body = section[newline_index:]

        # 2. 过滤文件名 (STM32/System杂项)
        if is_junk_filename(file_path):
            print(f"   🗑️ 剔除杂项文件: {file_path}")
            removed_count += 1
            continue

        # 3. 清洗代码内容
        cleaned_body = clean_code_content(code_body)

        # 重新组装
        cleaned_sections.append(file_path + cleaned_body)

    # --- 生成新文件 ---
    new_content = header_section + separator + separator.join(cleaned_sections)

    # 计算压缩率
    original_len = len(full_content)
    new_len = len(new_content)
    ratio = (1 - new_len / original_len) * 100

    # 构造输出文件名 (xxx_Codes.md -> xxx_Codes_Gap.md)
    dir_name = os.path.dirname(md_path)
    base_name = os.path.basename(md_path)
    name_without_ext = os.path.splitext(base_name)[0]
    new_output_path = os.path.join(dir_name, f"{name_without_ext}_Gap.md")

    try:
        with open(new_output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print("-" * 50)
        print(f"✅ 精简完成！")
        print(f"📉 剔除文件数: {removed_count}")
        print(f"📉 体积压缩: {original_len} -> {new_len} chars (节省 {ratio:.1f}%)")
        print(f"💾 新文件已生成: {new_output_path}")

        # 自动打开新文件位置
        if os.name == 'nt':
            import subprocess
            subprocess.Popen(f'explorer /select,"{os.path.abspath(new_output_path)}"')

    except Exception as e:
        print(f"❌ 写入新文件失败: {e}")


if __name__ == "__main__":
    # 测试用
    pass