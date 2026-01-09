"""统一的日志记录工具。

提供结构化、可配置的日志记录功能，替代项目中的print语句。

使用示例：
    from phone_agent.utils import get_logger

    logger = get_logger(__name__)
    logger.info("任务开始")
    logger.debug("调试信息: %s", data)
    logger.warning("警告: 配置缺失")
    logger.error("错误: %s", error_msg)
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


# ANSI颜色代码
class Colors:
    """控制台颜色代码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 亮色
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（仅用于控制台）"""

    # 日志级别对应的颜色
    LEVEL_COLORS = {
        logging.DEBUG: Colors.BRIGHT_BLACK,
        logging.INFO: Colors.BRIGHT_CYAN,
        logging.WARNING: Colors.BRIGHT_YELLOW,
        logging.ERROR: Colors.BRIGHT_RED,
        logging.CRITICAL: Colors.BOLD + Colors.BRIGHT_RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，添加颜色"""
        # 保存原始levelname
        original_levelname = record.levelname

        # 添加颜色
        color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
        record.levelname = f"{color}{record.levelname}{Colors.RESET}"

        # 模块名添加颜色
        record.name = f"{Colors.BRIGHT_BLUE}{record.name}{Colors.RESET}"

        # 格式化
        result = super().format(record)

        # 恢复原始levelname
        record.levelname = original_levelname

        return result


def _should_use_colors() -> bool:
    """判断是否应该使用颜色输出"""
    # 检查环境变量
    no_color = os.getenv("NO_COLOR")
    if no_color:
        return False

    force_color = os.getenv("FORCE_COLOR")
    if force_color:
        return True

    # 检查是否是TTY
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    format_string: Optional[str] = None,
    use_colors: Optional[bool] = None,
) -> None:
    """配置全局日志系统。

    Args:
        level: 日志级别，可选值: DEBUG, INFO, WARNING, ERROR, CRITICAL
               默认从环境变量 PHONE_AGENT_LOG_LEVEL 读取，未设置则为 INFO
        log_file: 日志文件名，如果指定则同时输出到文件
                 默认从环境变量 PHONE_AGENT_LOG_FILE 读取
        log_dir: 日志文件目录，默认为 logs/
                默认从环境变量 PHONE_AGENT_LOG_DIR 读取
        format_string: 自定义日志格式
        use_colors: 是否使用彩色输出，默认自动检测

    环境变量：
        PHONE_AGENT_LOG_LEVEL: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        PHONE_AGENT_LOG_FILE: 日志文件名
        PHONE_AGENT_LOG_DIR: 日志目录
        NO_COLOR: 设置为任意值禁用颜色
        FORCE_COLOR: 设置为任意值强制启用颜色
    """
    # 获取日志级别
    if level is None:
        level = os.getenv("PHONE_AGENT_LOG_LEVEL", "INFO").upper()

    # 验证日志级别
    numeric_level = getattr(logging, level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"无效的日志级别: {level}")

    # 获取根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 清除现有的handlers
    root_logger.handlers.clear()

    # 默认格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # 判断是否使用颜色
    if use_colors is None:
        use_colors = _should_use_colors()

    if use_colors:
        console_formatter = ColoredFormatter(format_string)
    else:
        console_formatter = logging.Formatter(format_string)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件handler（如果指定）
    if log_file is None:
        log_file = os.getenv("PHONE_AGENT_LOG_FILE")

    if log_file:
        if log_dir is None:
            log_dir = os.getenv("PHONE_AGENT_LOG_DIR", "logs")

        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # 完整的日志文件路径
        full_log_path = log_path / log_file

        file_handler = logging.FileHandler(
            full_log_path, mode="a", encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)

        # 文件输出不使用颜色
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)

        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的logger。

    Args:
        name: logger名称，通常使用 __name__

    Returns:
        配置好的logger实例

    使用示例：
        logger = get_logger(__name__)
        logger.info("这是一条信息")
        logger.debug("调试信息: %s", data)
        logger.error("错误: %s", error)
    """
    return logging.getLogger(name)


# 默认初始化（如果还没有配置）
if not logging.getLogger().handlers:
    setup_logging()
