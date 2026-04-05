"""
配置加载器 - 支持 exe 和源码两种模式
"""
import json
import os
import sys


def get_config_path():
    """获取 config.json 路径，兼容 exe 和源码模式"""
    if getattr(sys, 'frozen', False):
        # exe 模式：从 _MEIPASS 读取
        base_dir = sys._MEIPASS
    else:
        # 源码模式：从项目根目录读取
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'Core', 'config.json')


class Config:
    def __init__(self, json_path):
        self.json_path = json_path

        # 默认配置（兜底）
        self.allowed_exts = {'.py', '.c', '.h', '.cpp', '.txt', '.md'}
        self.ignore_dirs = {'.git', '__pycache__', 'node_modules', 'build'}
        self.ignore_files = set()
        self.ignore_prefixes = ('.',)
        self.version_info = ["Unknown Version"]
        self.default_mode = "normal"
        self.full_load_timeout_seconds = 5
        self.full_load_max_files = 2500

        if os.path.exists(json_path):
            self._load(json_path)

    def _load(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            data = validate_config_data(data)

            self.allowed_exts = set(data.get('allowed_extensions', []))
            self.ignore_dirs = set(data.get('ignore_dirs', []))
            self.ignore_files = set(data.get('ignore_files', []))
            self.ignore_prefixes = tuple(data.get('ignore_prefixes', []))
            self.version_info = data.get('version', ["Unknown Version"])
            self.default_mode = data.get('default_mode', "normal")
            self.full_load_timeout_seconds = data.get('full_load_timeout_seconds', 5)
            self.full_load_max_files = data.get('full_load_max_files', 2500)
        except Exception as e:
            print(f"Config load warning: {e}")


def validate_config_data(data):
    required_list_fields = [
        "allowed_extensions",
        "ignore_dirs",
        "ignore_files",
        "ignore_prefixes",
        "version",
    ]

    for field in required_list_fields:
        if field not in data:
            raise ValueError(f"config.json 缺少必要字段: {field}")
        if not isinstance(data[field], list):
            raise ValueError(f"config.json 字段类型错误: {field} 必须是数组")

    if "default_mode" in data and data["default_mode"] not in {"normal", "gap", "skeleton"}:
        raise ValueError("config.json 字段 default_mode 只能是 normal / gap / skeleton")

    for field in ("full_load_timeout_seconds", "full_load_max_files"):
        if field in data and not isinstance(data[field], int):
            raise ValueError(f"config.json 字段类型错误: {field} 必须是整数")

    return data


def read_config_text():
    """读取配置文件原始文本"""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return "{}"
    with open(config_path, 'r', encoding='utf-8') as f:
        return f.read()


def save_config_text(raw_text):
    """保存配置文件"""
    data = json.loads(raw_text)
    data = validate_config_data(data)
    normalized_text = json.dumps(data, ensure_ascii=False, indent=2)

    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(normalized_text + "\n")

    return data


def load_config():
    """加载配置对象"""
    return Config(get_config_path())