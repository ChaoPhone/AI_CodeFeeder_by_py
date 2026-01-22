import os
import re
import sys


# ==========================================
# 🧠 智能核心：代码骨架化 (Skeletonizer)
# ==========================================
def hollow_out_function_bodies(content):
    """
    【黑科技】掏空函数体
    原理：基于大括号层级计数 ({ count })。
    保留：全局变量、宏定义、函数声明、结构体定义。
    删除：函数内部的具体实现逻辑，替换为 ' /* ... */ '。
    """
    output = []
    i = 0
    length = len(content)
    brace_depth = 0
    in_string = False
    in_char = False

    # 简单的状态机扫描
    while i < length:
        char = content[i]

        # 1. 处理字符串/字符防止误判大括号
        if char == '"' and content[i - 1] != '\\':
            in_string = not in_string
            output.append(char)
            i += 1
            continue
        if char == "'" and content[i - 1] != '\\':
            in_char = not in_char
            output.append(char)
            i += 1
            continue

        if in_string or in_char:
            output.append(char)
            i += 1
            continue

        # 2. 核心：大括号计数
        if char == '{':
            if brace_depth == 0:
                # 刚进入第一层（通常是函数开始，或者结构体开始）
                output.append('{')
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
            if brace_depth == 0:
                # 回到第0层（函数结束）
                output.append('}')
        else:
            # 只有在第0层（全局区域）的内容才保留
            # 第1层及以上（函数体内部）全部丢弃
            if brace_depth == 0:
                output.append(char)
            elif brace_depth == 1 and output[-1] == '{':
                # 刚进入函数体，留个标记告诉AI这里有东西
                output.append(' /* Code Omitted */ ')

        i += 1

    return "".join(output)


# ==========================================
# 🛠️ 常规清洗工具箱
# ==========================================

def remove_license_header(content):
    """移除头部版权声明"""
    match = re.match(r'^\s*/\*[\s\S]*?\*/', content)
    if match:
        header = match.group(0)
        if any(k in header.lower() for k in ['copyright', 'license', 'author', 'file']):
            return content[len(header):].lstrip()
    return content


def clean_content_deeply(content, aggressive_mode=False):
    """
    深度清洗
    :param aggressive_mode: 是否开启【骨架模式】
    """
    # 1. 基础正则清洗
    # 去除 #include / #pragma
    content = re.sub(r'^\s*#\s*(include|pragma|import).*$', '', content, flags=re.MULTILINE)
    # 去除单行注释
    content = re.sub(r'(?<!:)\/\/.*', '', content)
    # 去除块注释
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    # 去除断言
    content = re.sub(r'\s*assert_param\s*\(.*?\);', '', content, flags=re.DOTALL)

    # 2. 【高阶】如果开启骨架模式，执行掏空逻辑
    if aggressive_mode:
        content = hollow_out_function_bodies(content)

    # 3. 最后的格式整理
    # 删除空行
    content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def is_junk_filename(filename):
    # 可以在这里增加更多你不想看的文件
    pattern = r'(stm32.*?xx|system_|main\.h|stm32f4xx_hal_conf|FreeRTOSConfig)'
    if re.search(pattern, filename, re.IGNORECASE):
        return True
    return False


# ==========================================
# 🚀 主流程
# ==========================================
def run_gap_process(md_path):
    print("=" * 50)
    print("✂️  FeederGap启动！")
    print("🦴  是否开启【骨架模式】(极大压缩)? ")
    print("    Tip: 骨架模式会保留函数接口，删除函数体实现。")
    print("-" * 50)

    # --- 交互：是否开启骨架模式 ---
    mode_input = input("(y/n): ")

    aggressive = (mode_input.lower() == 'y')

    if not os.path.exists(md_path):
        print("❌ 找不到目标 MD 文件")
        return

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            full_text = f.read()
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return

    separator = "## File: "
    parts = full_text.split(separator)
    header = parts[0]
    body_parts = parts[1:]

    cleaned_parts = []
    removed_count = 0
    chars_before = len(full_text)

    # 用于统计“Token败家子”
    file_stats = []

    print(f"🔍 正在处理 {len(body_parts)} 个文件块...")

    for part in body_parts:
        newline_idx = part.find('\n')
        if newline_idx == -1: continue

        fname = part[:newline_idx].strip()
        code_content = part[newline_idx:]

        # 过滤
        if is_junk_filename(fname):
            removed_count += 1
            continue

        # 清洗
        code_content = remove_license_header(code_content)
        new_code = clean_content_deeply(code_content, aggressive_mode=aggressive)

        # 只有剩下的内容还有意义才保留
        if len(new_code.strip()) < 5:
            removed_count += 1
            continue

        cleaned_parts.append(fname + "\n" + new_code)

        # 记录统计信息
        file_stats.append((fname, len(new_code)))

    # --- 组装 ---
    new_full_text = header + separator + "\n" + ("\n" + separator).join(cleaned_parts)
    chars_after = len(new_full_text)
    ratio = (1 - chars_after / chars_before) * 100

    # --- 保存 ---
    dir_name = os.path.dirname(md_path)
    base_name = os.path.basename(md_path)
    # 根据模式给文件名加不同的后缀
    suffix = "_Skeleton.md" if aggressive else "_Gap.md"
    new_name = os.path.splitext(base_name)[0] + suffix
    new_path = os.path.join(dir_name, new_name)

    try:
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(new_full_text)

        print("\n" + "=" * 50)
        print(f"✅ 处理完成！")
        print(f"📉 移除文件: {removed_count} 个")
        print(f"📉 字符压缩: {chars_before} -> {chars_after} (瘦身 {ratio:.1f}%)")
        print("\n💾 输出文件: " + new_path)
        print("=" * 50)

        if os.name == 'nt':
            import subprocess
            subprocess.Popen(f'explorer /select,"{os.path.abspath(new_path)}"')

    except Exception as e:
        print(f"❌ 写入失败: {e}")