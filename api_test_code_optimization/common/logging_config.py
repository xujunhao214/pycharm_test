import logging
import os
from datetime import datetime


def setup_logger(name, log_file=None, level=logging.INFO):
    """设置日志记录器"""
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 如果logger已经有处理器，直接返回
    if logger.handlers:
        return logger

    # 创建控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # 创建格式化器并添加到处理器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    # 将处理器添加到logger
    logger.addHandler(ch)

    # 如果指定了日志文件，创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        # 创建文件处理器
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def get_logger(module_name):
    """获取配置好的日志记录器"""
    # 从配置文件读取日志级别和日志文件路径
    # 这里简化处理，实际应从config.yaml读取
    log_level = logging.INFO
    log_dir = "Logs"
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{current_date}.log")

    return setup_logger(module_name, log_file, log_level)
