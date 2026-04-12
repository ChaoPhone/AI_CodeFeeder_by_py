"""
Core 服务层 - 配置、扫描、生成等服务
"""
from .ConfigService import (
    Config,
    ConfigService,
    load_config,
    read_config_text,
    save_config_text,
    get_config_path,
    get_config_read_path,
    get_config_write_path,
    get_appdata_dir,
    validate_config_data,
)

__all__ = [
    "Config",
    "ConfigService",
    "load_config",
    "read_config_text",
    "save_config_text",
    "get_config_path",
    "get_config_read_path",
    "get_config_write_path",
    "get_appdata_dir",
    "validate_config_data",
]