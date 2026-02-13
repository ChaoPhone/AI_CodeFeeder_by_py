import re


def hollow_out_function_bodies(content):
    """
    【骨架模式核心】保留结构，掏空实现
    基于大括号计数 ({ count })
    """
    output = []
    i = 0
    length = len(content)
    brace_depth = 0
    in_string = False
    in_char = False

    while i < length:
        char = content[i]

        # 1. 简单的字符串跳过逻辑
        if char == '"' and (i == 0 or content[i - 1] != '\\'):
            in_string = not in_string
            output.append(char)
            i += 1
            continue
        if char == "'" and (i == 0 or content[i - 1] != '\\'):
            in_char = not in_char
            output.append(char)
            i += 1
            continue

        if in_string or in_char:
            output.append(char)
            i += 1
            continue

        # 2. 大括号逻辑
        if char == '{':
            if brace_depth == 0:
                output.append('{')
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
            if brace_depth == 0:
                output.append('}')
        else:
            if brace_depth == 0:
                output.append(char)
            elif brace_depth == 1 and output and output[-1] == '{':
                output.append(' /* ... */ ')  # 简化占位符

        i += 1

    return "".join(output)


def remove_license_header(content):
    """移除常见的顶部版权注释"""
    match = re.match(r'^\s*/\*[\s\S]*?\*/', content)
    if match:
        header = match.group(0)
        # 简单判定：包含 license/copyright 等关键词
        if any(k in header.lower() for k in ['copyright', 'license', 'author', 'file']):
            return content[len(header):].lstrip()
    return content


def clean_content_deeply(content, ext, aggressive_mode=False):
    """
    深度清洗流水线
    :param ext: 文件扩展名 (如 '.py', '.cpp')
    :param aggressive_mode: True=骨架模式, False=Gap模式(仅去注释)
    """
    ext = ext.lower()

    # 1. 根据后缀决定清洗逻辑
    if ext == '.py':
        # 移除 Python import
        content = re.sub(r'^\s*(import|from)\s+.*$', '', content, flags=re.MULTILINE)
        # 移除 Python 单行注释
        content = re.sub(r'#.*', '', content)
        # 移除 Python 多行注释 (''' 或 """) - 简单处理，不考虑字符串内的情况
        content = re.sub(r'\'\'\'[\s\S]*?\'\'\'', '', content)
        content = re.sub(r'\"\"\"[\s\S]*?\"\"\"', '', content)
        
    elif ext in ['.c', '.cpp', '.h', '.hpp']:
        # 移除 C/C++ 引用
        content = re.sub(r'^\s*#\s*(include|pragma|import).*$', '', content, flags=re.MULTILINE)
        # 移除 C/C++ 单行注释
        content = re.sub(r'(?<!:)\/\/.*', '', content)
        # 移除 C/C++ 块注释
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)

    # 2. 骨架模式 (仅对支持大括号的语言有效，当前逻辑基于大括号)
    if aggressive_mode and ext in ['.c', '.cpp', '.h', '.hpp']:
        content = hollow_out_function_bodies(content)

    # 3. 格式整理 (去多余空行)
    content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def is_junk_filename(filename, extra_patterns=None):
    """文件名级过滤"""
    # 基础垃圾文件名正则
    base_pattern = r'(stm32.*?xx|system_|main\.h|stm32f4xx_hal_conf|FreeRTOSConfig)'
    if re.search(base_pattern, filename, re.IGNORECASE):
        return True
    return False