import requests
import logging
import json
from enum import Enum
from lingkuan_youhua2.commons.enums import Environment  # 从公共模块导入
from lingkuan_youhua2.commons.jsonpath_utils import JsonPathUtils

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EnvironmentSession(requests.Session):
    """支持多环境切换的会话管理，自动处理URL和请求头"""

    def __init__(self, environment: Environment, base_url: str):
        self.environment = environment
        self.base_url = base_url.rstrip('/')
        self.jsonpath_utils = JsonPathUtils()
        super().__init__()
        # 设置环境标识到日志
        self.logger = logging.LoggerAdapter(logger, {"env": environment.value})
        self.logger.info(f"初始化环境会话: {environment.value}")

    def build_url(self, path: str) -> str:
        """根据环境和路径构建完整URL"""
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(self, method, url, *args, **kwargs):
        """重写请求方法，添加环境日志和通用处理"""
        full_url = self.build_url(url)
        self.logger.info(f"请求URL: {full_url}, 方法: {method}")

        # 处理JSON请求
        if "json" in kwargs:
            kwargs.setdefault("headers", {})
            kwargs["headers"].setdefault("Content-Type", "application/json; charset=utf-8")
            kwargs["data"] = json.dumps(kwargs.pop("json"), ensure_ascii=False).encode("utf-8")

        response = super().request(method, full_url, *args, **kwargs)
        self.logger.info(f"响应状态码: {response.status_code}")

        # 记录响应内容
        if response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                self.logger.debug(f"响应内容: {response.json()}")
            except:
                self.logger.debug(f"响应内容: {response.text}")
        else:
            self.logger.debug(f"响应内容: {response.text[:200]}...")

        # 为响应添加JSONPath提取方法
        response.extract_jsonpath = lambda expr: self.jsonpath_utils.extract(response.json(), expr)

        return response
