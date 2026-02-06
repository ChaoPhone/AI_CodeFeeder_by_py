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


def clean_content_deeply(content, aggressive_mode=False):
    """
    深度清洗流水线
    :param aggressive_mode: True=骨架模式, False=Gap模式(仅去注释)
    """
    # 1. 移除引用
    content = re.sub(r'^\s*#\s*(include|pragma|import).*$', '', content, flags=re.MULTILINE)

    # 2. 移除注释
    content = re.sub(r'(?<!:)\/\/.*', '', content)  # 单行
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)  # 块注释

    # 3. 骨架模式
    if aggressive_mode:
        content = hollow_out_function_bodies(content)

    # 4. 格式整理 (去多余空行)
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