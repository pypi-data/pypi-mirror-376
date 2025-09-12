import logging
import sys
from contextvars import ContextVar
from pathlib import Path

# 1. Context Variables 保持不变
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default="anonymous")

# 2. 日志目录保持不变
LOG_DIR = Path("../..") / "logs"


# 3. ContextFilter 保持不变
class ContextFilter(logging.Filter):
    """将 request_id 和 user_id 注入到每一条日志记录中。"""
    def filter(self, record):
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        return True


# --- (关键新增 1) 自定义一个过滤器，用于分离不同级别的日志 ---
class LevelFilter(logging.Filter):
    """
    这个过滤器只允许低于指定级别的日志通过。
    例如，LevelFilter(logging.WARNING) 将只允许 INFO 和 DEBUG 级别的日志。
    """
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


# --- (关键修改 2) 简化 Logger 配置 ---
# 我们只需要定义特殊的 logger，常规的应用日志将由 root logger 处理
LOGGERS_TO_SETUP = [
    {"name": "api_traffic", "level": logging.INFO, "filename": "api_traffic.log"},
]


# 5. 重构设置日志的主函数
def setup_logging():
    """
    配置应用的日志系统，实现控制台和多文件输出，并按级别分离。
    """
    LOG_DIR.mkdir(exist_ok=True)

    log_format = (
        "%(asctime)s - [User:%(user_id)s] [%(request_id)s] - "
        "%(levelname)s - %(name)s - %(message)s"
    )
    formatter = logging.Formatter(log_format)
    context_filter = ContextFilter()

    # --- (关键修改 3) 配置 root logger 来处理所有常规日志 ---
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 设置最低级别，交由 handler 过滤
    # 清除已有 handler，防止重复日志
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # --- 创建并配置 Handlers ---

    # 1. 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)
    console_handler.setLevel(logging.DEBUG)  # 开发时显示所有日志

    # 2. info.log 文件 Handler (只记录 INFO 和 DEBUG)
    info_file_handler = logging.FileHandler(LOG_DIR / "info.log", encoding='utf-8')
    info_file_handler.setFormatter(formatter)
    info_file_handler.addFilter(context_filter)
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.addFilter(LevelFilter(logging.WARNING))  # 添加过滤器，只允许低于 WARNING 的日志

    # 3. error.log 文件 Handler (只记录 WARNING 及以上)
    error_file_handler = logging.FileHandler(LOG_DIR / "error.log", encoding='utf-8')
    error_file_handler.setFormatter(formatter)
    error_file_handler.addFilter(context_filter)
    error_file_handler.setLevel(logging.WARNING)  # 只处理 WARNING, ERROR, CRITICAL

    # 将 Handlers 添加到 root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(info_file_handler)
    root_logger.addHandler(error_file_handler)

    # --- (关键修改 4) 单独配置专用的 logger ---
    for config in LOGGERS_TO_SETUP:
        logger = logging.getLogger(config["name"])
        logger.setLevel(config["level"])
        logger.propagate = False  # 阻止向 root logger 传播，避免重复

        if logger.hasHandlers():
            logger.handlers.clear()

        # 专用 logger 也输出到控制台
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(LOG_DIR / config["filename"], encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        logger.addHandler(file_handler)