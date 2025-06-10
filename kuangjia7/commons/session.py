# session.py
import os
import datetime
import logging
import requests
from typing import Dict, Any, Optional
from pathlib import Path
import logging.handlers
from kuangjia7.commons.jsonpath_utils import JsonPathUtils

# 自动创建日志目录
log_dir = "./Logs"
os.makedirs(log_dir, exist_ok=True)

# 优化日志路径和轮转
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "requests.log"

# 按天轮转日志，保留7天
file_handler = logging.handlers.TimedRotatingFileHandler(
    log_file, when="D", backupCount=7, encoding="utf-8"
)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger = logging.getLogger("requests.session")
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


class JunhaoSession(requests.Session):
    """
    request二次封装：
    1. 支持BaseURL环境切换
    2. 自动记录请求响应日志
    3. 维护全局变量上下文
    """

    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        self.g_vars: Dict[str, Any] = {}  # 存储全局变量
        self.last_response = None  # 存储最后一次响应
        super().__init__()

    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        """预处理请求URL，添加BaseURL"""
        if url and not url.startswith(("http://", "https://")):
            url = self.base_url + url
        return super().request(method, url, *args, **kwargs)

    def send(self, request: requests.PreparedRequest, *args, **kwargs) -> requests.Response:
        """发送请求并记录完整日志"""
        # 记录请求日志（优化日志格式）
        req_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.info(f"{req_time}发送请求>>>>>>>       接口地址={request.method} {request.url}")
        logger.info(f"发送请求>>>>>>>                 请求头={request.headers}")
        logger.info(f"发送请求>>>>>>>                 请求体={request.body.decode('utf-8') if request.body else '无'}")

        # 发送请求
        response = super().send(request, **kwargs)
        self.last_response = response  # 保存响应

        # 记录响应日志
        resp_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.info(f"{resp_time}接收响应<<<<<<<       状态码={response.status_code}")
        logger.info(f"接收响应<<<<<<<                  响应头={response.headers}")
        logger.info(f"接收响应<<<<<<<                  响应体={response.content[:500]}...")  # 截断长响应体

        return response

    def extract_jsonpath(
            self,
            expr: str,
            response: requests.Response = None,
            default: Any = None,
            multi_match: bool = False
    ) -> Any:
        """
        使用工具类提取 JSONPath 值

        Args:
            expr: JSONPath 表达式
            response: 响应对象（默认使用最后一次响应）
            default: 未匹配默认值
            multi_match: 是否返回所有匹配结果

        Returns:
            提取结果
        """
        response = response or self.last_response
        if not response:
            return default

        try:
            data = response.json()
            return JsonPathUtils.extract(
                data=data,
                expr=expr,
                default=default,
                multi_match=multi_match
            )
        except (ValueError, TypeError):
            return default
