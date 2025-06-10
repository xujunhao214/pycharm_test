# Common/log_handler.py
import logging
import os
from datetime import datetime
from typing import Optional, Union


class LogHandler:
    """
    增强版日志处理类，支持灵活配置日志级别、路径和格式，封装常用日志方法。
    """

    def __init__(
            self,
            log_name: str = "api_test",
            log_level: Union[str, int] = logging.INFO,
            log_dir: Optional[str] = None,
            use_console: bool = True,
            use_file: bool = True,
            file_suffix: str = ".log"
    ):
        """
        初始化日志处理器
        """
        self.log_name = log_name
        self.log_level = log_level
        self.log_dir = log_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../Logs"
        )
        self.use_console = use_console
        self.use_file = use_file
        self.file_suffix = file_suffix

        # 初始化日志器
        self.logger = logging.getLogger(self.log_name)
        self.logger.setLevel(self.log_level)

        # 清除已有处理器（避免重复日志）
        self._clear_handlers()

        # 创建日志目录
        self._create_log_dir()

        # 添加处理器
        if self.use_console:
            self._add_console_handler()
        if self.use_file:
            self._add_file_handler()

    def _clear_handlers(self) -> None:
        """清除日志器中已有的处理器"""
        if self.logger.handlers:
            for handler in self.logger.handlers:
                handler.close()
                self.logger.removeHandler(handler)

    def _create_log_dir(self) -> None:
        """创建日志目录（如果不存在）"""
        os.makedirs(self.log_dir, exist_ok=True)

    def _add_console_handler(self) -> None:
        """添加控制台处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)

    def _add_file_handler(self) -> None:
        """添加文件处理器（按天分割日志）"""
        file_name = f"{datetime.now().strftime('%Y%m%d')}{self.file_suffix}"
        file_path = os.path.join(self.log_dir, file_name)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(file_handler)

    @staticmethod
    def _get_formatter() -> logging.Formatter:
        """获取统一的日志格式"""
        return logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # --------------------------- 日志方法封装 ---------------------------
    def debug(self, msg: str, *args, **kwargs) -> None:
        """记录DEBUG级别日志"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """记录INFO级别日志"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """记录WARNING级别日志"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """记录ERROR级别日志"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """记录CRITICAL级别日志"""
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str = "发生异常", *args, **kwargs) -> None:
        """记录异常日志（自动包含堆栈信息）"""
        self.logger.exception(msg, *args, exc_info=True, **kwargs)
