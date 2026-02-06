import json
import os


class Config:
    def __init__(self, json_path):
        # 默认配置 (兜底)
        self.allowed_exts = {'.py', '.c', '.h', '.cpp', '.txt', '.md'}
        self.ignore_dirs = {'.git', '__pycache__', 'node_modules', 'build'}
        self.ignore_files = set()
        self.ignore_prefixes = ('.',)
        self.version_info = ["Unknown Version"]

        # 加载
        if os.path.exists(json_path):
            self._load(json_path)

    def _load(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.allowed_exts = set(data.get('allowed_extensions', []))
            self.ignore_dirs = set(data.get('ignore_dirs', []))
            self.ignore_files = set(data.get('ignore_files', []))
            self.ignore_prefixes = tuple(data.get('ignore_prefixes', []))
            self.version_info = data.get('version', [])
        except Exception as e:
            print(f"⚠️ Config load warning: {e}")


# 方便外部调用
def load_config():
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(current_dir, 'Core', 'config.json')
    return Config(config_path)