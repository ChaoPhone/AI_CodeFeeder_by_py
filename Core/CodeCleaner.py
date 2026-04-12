"""
代码清洗器 - 支持多种语言的注释移除和骨架模式
"""
import re


def hollow_out_function_bodies(content):
    """
    【骨架模式核心】保留结构，掏空实现
    基于大括号计数 ({ count })
    使用正则预处理移除字符串字面量，避免转义判断复杂度
    """
    def replace_string(match):
        return ' ' * len(match.group(0))

    content = re.sub(r'"(?:[^"\\]|\\.)*"', replace_string, content)
    content = re.sub(r"'(?:[^'\\]|\\.)*'", replace_string, content)

    output = []
    brace_depth = 0

    for char in content:
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
                output.append(' /* ... */ ')

    return "".join(output)


def hollow_out_python_bodies(content):
    """
    【Python骨架模式】保留结构，掏空实现
    基于缩进计数，保留函数/类定义，掏空实现
    """
    lines = content.split('\n')
    output_lines = []
    
    in_block = False
    block_indent = 0
    block_type = None
    
    for line in lines:
        stripped = line.strip()
        current_indent = len(line) - len(line.lstrip())
        
        if not stripped:
            output_lines.append('')
            continue
        
        if stripped.startswith(('def ', 'class ', 'async def ')):
            in_block = True
            block_indent = current_indent
            block_type = 'def' if 'def' in stripped else 'class'
            output_lines.append(line)
            continue
        
        if in_block:
            if current_indent > block_indent:
                if stripped and not stripped.startswith(('"""', "'''", '#')):
                    if output_lines and output_lines[-1].strip() and not output_lines[-1].strip().endswith('...'):
                        output_lines.append('    ' * ((current_indent // 4) or 1) + '...')
                continue
            elif current_indent <= block_indent and stripped:
                in_block = False
                block_indent = 0
                block_type = None
        
        output_lines.append(line)
    
    return '\n'.join(output_lines)


def remove_license_header(content):
    """移除常见的顶部版权注释"""
    match = re.match(r'^\s*/\*[\s\S]*?\*/', content)
    if match:
        header = match.group(0)
        if any(k in header.lower() for k in ['copyright', 'license', 'author', 'file']):
            return content[len(header):].lstrip()
    return content


def remove_python_docstring(content):
    """移除 Python 文档字符串"""
    content = re.sub(r'\'\'\'[\s\S]*?\'\'\'', '', content)
    content = re.sub(r'\"\"\"[\s\S]*?\"\"\"', '', content)
    return content


def clean_content_deeply(content, ext, aggressive_mode=False):
    """
    深度清洗流水线
    :param ext: 文件扩展名 (如 '.py', '.cpp')
    :param aggressive_mode: True=骨架模式, False=Gap模式(仅去注释)
    """
    ext = ext.lower()

    if ext == '.py':
        content = re.sub(r'^\s*(import|from)\s+.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'#.*', '', content)
        content = remove_python_docstring(content)
        
        if aggressive_mode:
            content = hollow_out_python_bodies(content)
        
    elif ext in ['.c', '.cpp', '.h', '.hpp']:
        content = re.sub(r'^\s*#\s*(include|pragma|import).*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'(?<!:)\/\/.*', '', content)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        if aggressive_mode:
            content = hollow_out_function_bodies(content)
    
    elif ext in ['.js', '.ts', '.jsx', '.tsx']:
        content = re.sub(r'(?<!:)\/\/.*', '', content)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        if aggressive_mode:
            content = hollow_out_function_bodies(content)
    
    elif ext in ['.java', '.kt']:
        content = re.sub(r'(?<!:)\/\/.*', '', content)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        if aggressive_mode:
            content = hollow_out_function_bodies(content)

    content = re.sub(r'^[ \t]+$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def is_junk_filename(filename, extra_patterns=None):
    """文件名级过滤"""
    base_pattern = r'(stm32.*?xx|system_|main\.h|stm32f4xx_hal_conf|FreeRTOSConfig|__init__|setup\.py|test_|_test\.py)'
    if re.search(base_pattern, filename, re.IGNORECASE):
        return True
    return False