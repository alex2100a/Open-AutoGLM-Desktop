"""日志配置文件。

集中管理日志相关的配置选项。
"""

import os
from typing import Dict, Any


class LoggingConfig:
    """日志配置类"""

    # 默认日志级别
    DEFAULT_LEVEL = "INFO"

    # 默认日志格式
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 简化格式（用于开发环境）
    SIMPLE_FORMAT = "%(levelname)s - %(name)s - %(message)s"

    # 详细格式（用于生产环境）
    VERBOSE_FORMAT = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(filename)s:%(lineno)d - %(funcName)s - %(message)s"
    )

    # 默认日志目录
    DEFAULT_LOG_DIR = "logs"

    # 默认日志文件名
    DEFAULT_LOG_FILE = "phone_agent.log"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取当前日志配置。

        从环境变量读取配置，如果未设置则使用默认值。

        Returns:
            包含日志配置的字典
        """
        return {
            "level": os.getenv("PHONE_AGENT_LOG_LEVEL", cls.DEFAULT_LEVEL),
            "log_file": os.getenv("PHONE_AGENT_LOG_FILE"),
            "log_dir": os.getenv("PHONE_AGENT_LOG_DIR", cls.DEFAULT_LOG_DIR),
            "format": cls._get_format(),
        }

    @classmethod
    def _get_format(cls) -> str:
        """根据环境获取日志格式"""
        format_type = os.getenv("PHONE_AGENT_LOG_FORMAT", "default")

        if format_type == "simple":
            return cls.SIMPLE_FORMAT
        elif format_type == "verbose":
            return cls.VERBOSE_FORMAT
        else:
            return cls.DEFAULT_FORMAT


# 预定义的配置方案

# 开发环境配置
DEV_CONFIG = {
    "level": "DEBUG",
    "format_string": LoggingConfig.SIMPLE_FORMAT,
    "use_colors": True,
}

# 生产环境配置
PROD_CONFIG = {
    "level": "INFO",
    "log_file": "phone_agent.log",
    "log_dir": "logs",
    "format_string": LoggingConfig.VERBOSE_FORMAT,
    "use_colors": False,
}

# 测试环境配置
TEST_CONFIG = {
    "level": "WARNING",
    "format_string": LoggingConfig.SIMPLE_FORMAT,
    "use_colors": False,
}
