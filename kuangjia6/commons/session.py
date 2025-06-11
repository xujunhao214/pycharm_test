# session.py
import os
import datetime
import logging
import requests
from typing import Dict, Any, Optional
from pathlib import Path
import logging.handlers
from kuangjia6.commons.jsonpath_utils import JsonPathUtils
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError

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
        logger.info(f"{req_time}发送请求>>>>>>>       请求头={request.headers}")
        logger.info(f"{req_time}发送请求 >>>>>>>      请求体={request.body.decode('utf-8') if request.body else '无'}")

        try:
            # 发送请求并捕获异常
            response = super().send(request, **kwargs)
            response.raise_for_status()  # 主动抛出HTTP错误（如4xx/5xx）

        except ConnectionError:
            # 服务器连接失败（如IP错误、服务未启动）
            logger.error(f"{req_time} 连接异常 >>> 服务器不可达，请求URL：{request.url}")
            raise

        except Timeout:
            # 请求超时（网络延迟或服务器无响应）
            logger.error(f"{req_time} 超时异常 >>> 请求超时，URL：{request.url}")
            raise

        except HTTPError as e:
            # 服务器返回错误状态码（400/500等）
            logger.error(f"{req_time} HTTP错误 >>> 状态码={e.response.status_code}，URL：{request.url}")
            raise

        except RequestException as e:
            # 其他请求异常（如DNS解析失败）
            logger.error(f"{req_time} 未知请求异常 >>> {str(e)}，URL：{request.url}")
            raise

        # 记录响应日志
        resp_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.info(f"{resp_time}接收响应<<<<<<<       状态码={response.status_code}")
        logger.info(f"{resp_time}接收响应<<<<<<<       响应头={response.headers}")
        # 截断长响应体
        logger.info(f"{resp_time}接收响应<<<<<<<       响应体={response.content[:500].decode('utf-8', errors='replace')}...")

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
