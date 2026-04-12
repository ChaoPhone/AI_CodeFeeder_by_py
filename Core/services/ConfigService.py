"""
配置服务 - 处理配置加载、保存、验证
"""
import json
import os
import sys


def get_appdata_dir():
    """获取应用数据目录（exe模式使用C盘AppData）"""
    if getattr(sys, 'frozen', False):
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        cache_dir = os.path.join(appdata, 'AICodeFeeder')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    else:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_config_read_path():
    """获取 config.json 读取路径（exe模式从内置资源读取默认配置）"""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
        return os.path.join(base_dir, 'Core', 'config.json')
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, 'Core', 'config.json')


def get_config_write_path():
    """获取 config.json 写入路径"""
    if getattr(sys, 'frozen', False):
        return os.path.join(get_appdata_dir(), 'config.json')
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, 'Core', 'config.json')


def get_config_path():
    """获取 config.json 路径（兼容旧接口）"""
    write_path = get_config_write_path()
    if os.path.exists(write_path):
        return write_path
    return get_config_read_path()


def validate_config_data(data):
    """验证配置数据"""
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


class Config:
    """配置对象"""
    
    def __init__(self, json_path):
        self.json_path = json_path
        
        self.allowed_exts = {'.py', '.c', '.h', '.cpp', '.txt', '.md'}
        self.ignore_dirs = {'.git', '__pycache__', 'node_modules', 'build'}
        self.ignore_files = set()
        self.ignore_prefixes = ('.',)
        self.version_info = ["Unknown Version"]
        self.default_mode = "normal"
        self.full_load_timeout_seconds = 5
        self.full_load_max_files = 2500
        self.save_txt = False

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
            self.save_txt = data.get('save_txt', False)
        except Exception as e:
            print(f"Config load warning: {e}")


class ConfigService:
    """配置服务类"""
    
    @staticmethod
    def load() -> Config:
        """加载配置对象"""
        return Config(get_config_path())
    
    @staticmethod
    def read_text() -> str:
        """读取配置文件原始文本"""
        write_path = get_config_write_path()
        if os.path.exists(write_path):
            with open(write_path, 'r', encoding='utf-8') as f:
                return f.read()

        read_path = get_config_read_path()
        if not os.path.exists(read_path):
            return "{}"
        with open(read_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def save_text(raw_text: str) -> dict:
        """保存配置文件"""
        data = json.loads(raw_text)
        data = validate_config_data(data)
        normalized_text = json.dumps(data, ensure_ascii=False, indent=2)

        config_path = get_config_write_path()
        config_dir = os.path.dirname(config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(normalized_text + "\n")

        return data
    
    @staticmethod
    def get_path() -> str:
        """获取配置路径"""
        return get_config_path()
    
    @staticmethod
    def get_read_path() -> str:
        """获取读取路径"""
        return get_config_read_path()
    
    @staticmethod
    def get_write_path() -> str:
        """获取写入路径"""
        return get_config_write_path()
    
    @staticmethod
    def get_appdata_dir() -> str:
        """获取应用数据目录"""
        return get_appdata_dir()


def load_config():
    """加载配置对象（兼容旧接口）"""
    return Config(get_config_path())


def read_config_text():
    """读取配置文件原始文本（兼容旧接口）"""
    return ConfigService.read_text()


def save_config_text(raw_text):
    """保存配置文件（兼容旧接口）"""
    return ConfigService.save_text(raw_text)