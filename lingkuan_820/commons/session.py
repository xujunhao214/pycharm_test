import os
import datetime
import requests
import json
from lingkuan_820.VAR.VAR import *
from typing import Dict, Any, Optional
from pathlib import Path
import logging.handlers
from requests.exceptions import (
    RequestException, ConnectionError, Timeout,
    HTTPError, SSLError
)
from lingkuan_820.commons.jsonpath_utils import JsonPathUtils
from lingkuan_820.commons.enums import Environment
from lingkuan_820.conftest import *

# 自动创建日志目录
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "requests.log"

# 按天轮转日志，保留1天
file_handler = logging.handlers.TimedRotatingFileHandler(
    log_file, when="D", interval=1, backupCount=10, encoding="utf-8"
    # log_file, when="H", interval=1, backupCount=10, encoding="utf-8"
)

# 日志格式包含时间、级别、环境标识和消息
formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(env)s] - %(message)s")
file_handler.setFormatter(formatter)

# 配置基础logger（支持info级别）
logger = logging.getLogger("requests.session")
logger.propagate = False
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


class EnvironmentSession(requests.Session):
    """
    支持多环境切换的会话管理类（增强版）
    使用 ConnectionError 捕获包括 DNS 解析失败在内的所有连接异常
    """

    def __init__(self, environment: Environment, base_url: str, vps_url=None):
        self.environment = environment
        self.base_url = base_url.rstrip('/')  # 移除base_url末尾的斜杠
        self.jsonpath_utils = JsonPathUtils()
        self.g_vars: Dict[str, Any] = {}  # 存储全局变量
        self.last_response = None  # 存储最后一次响应
        self.named_urls = {}  # 存储命名URL
        self.vps_url = vps_url or ENV_CONFIG[environment].get("vps_url")
        self.current_url = base_url  # 默认使用base_url
        super().__init__()

        # 设置环境标识到日志适配器
        self.logger = logging.LoggerAdapter(logger, {"env": environment.value})
        self.logger.info(f"[{DATETIME_NOW}] 初始化环境会话: {environment.value} | Base URL: {self.base_url}")

    def use_base_url(self):
        """切换回默认base_url"""
        self.current_url = self.base_url
        self.logger.info(f"[{DATETIME_NOW}] 切换到Base URL: {self.current_url}")
        return self

    def use_vps_url(self):
        """切换到vps_url"""
        self.current_url = self.vps_url
        self.logger.info(f"[{DATETIME_NOW}] 切换到VPS URL: {self.current_url}")
        return self

    def register_url(self, name: str, url: str):
        """
        注册命名URL，支持后续通过名称快速调用
        """
        self.named_urls[name] = url.rstrip('/')  # 确保URL末尾无斜杠
        self.logger.info(f"[{DATETIME_NOW}] 注册命名URL: {name} -> {self.named_urls[name]}")

    def build_url(self, path: str) -> str:
        """
        构建完整URL，支持三种优先级：
        1. 完整URL（http://或https://开头）
        2. 命名URL（如"vps_api/subcontrol"）
        3. 基于current_url的相对路径
        """
        # 检查是否为完整URL
        if path.startswith(("http://", "https://")):
            self.logger.info(f"[{DATETIME_NOW}] 使用完整URL: {path}")
            return path

        # 检查是否为命名URL
        for name, base in self.named_urls.items():
            if path.startswith(f"{name}/"):
                sub_path = path[len(name) + 1:].lstrip('/')
                full_url = f"{base}/{sub_path}" if sub_path else base
                self.logger.info(f"[{DATETIME_NOW}] 使用命名URL: {name} -> {full_url}")
                return full_url

        # 普通相对路径
        full_url = f"{self.current_url}/{path.lstrip('/')}" if self.current_url else path
        self.logger.info(f"[{DATETIME_NOW}] 构建相对URL: {self.current_url} + {path} -> {full_url}")
        return full_url

    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        """
        重写请求方法，使用 ConnectionError 统一处理连接相关异常
        """
        # 构建完整URL
        full_url = self.build_url(url)
        request_id = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        request_start_time = datetime.datetime.now()

        # 记录请求开始日志
        self.logger.info(f"[{request_id}] {method.upper()} 请求开始: {full_url}")
        self.logger.info(f"[{request_id}] 请求参数: args={args}, kwargs_keys={list(kwargs.keys())}")

        # 处理JSON请求
        if "json" in kwargs and "files" not in kwargs:
            kwargs.setdefault("headers", {})
            kwargs["headers"].setdefault("Content-Type", "application/json; charset=utf-8")
            json_data = kwargs.pop("json")
            kwargs["data"] = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
            self.logger.info(f"[{request_id}] JSON请求体: {json_data}")

        # 发送请求并捕获异常
        try:
            response = super().request(method, full_url, *args, **kwargs)
            self.last_response = response
            request_end_time = datetime.datetime.now()

            # 记录响应日志
            duration = (request_end_time - request_start_time).total_seconds() * 1000
            self.logger.info(
                f"[{request_id}] 请求完成: {method.upper()} {full_url} | 状态码: {response.status_code} | 耗时: {duration:.2f}ms")
            self.logger.info(f"[{request_id}] 响应头: {response.headers}")

            # 记录响应内容
            try:
                if response.headers.get('Content-Type', '').startswith('application/json'):
                    resp_json = response.json()
                    self.logger.info(f"[{request_id}] 响应JSON: {resp_json}")
                else:
                    content = response.text[:5000] + ("..." if len(response.text) > 5000 else "")
                    self.logger.info(f"[{request_id}] 响应内容: {content}")
            except Exception as e:
                self.logger.warning(f"[{request_id}] 响应解析失败: {str(e)}")

            # 为响应添加JSONPath提取方法
            response.extract_jsonpath = lambda expr: self.jsonpath_utils.extract(
                response.json() if response.headers.get('Content-Type', '').startswith('application/json') else {},
                expr
            )

            return response

        except SSLError as e:
            error_msg = f"[{request_id}] SSL验证失败: {str(e)} | URL: {full_url}"
            self.logger.error(error_msg, exc_info=True)
            raise
        except ConnectionError as e:
            # 统一处理所有连接相关异常（包括DNS解析失败）
            error_msg = f"[{request_id}] 网络连接异常（可能包含DNS解析失败）: {str(e)} | URL: {full_url}"
            self.logger.error(error_msg, exc_info=True)
            raise
        except Timeout as e:
            error_msg = f"[{request_id}] 请求超时: {str(e)} | URL: {full_url}"
            self.logger.error(error_msg, exc_info=True)
            raise
        except RequestException as e:
            error_msg = f"[{request_id}] 请求异常: {str(e)} | URL: {full_url}"
            self.logger.error(error_msg, exc_info=True)
            raise

    def extract_jsonpath(
            self,
            expr: str,
            response: requests.Response = None,
            default: Any = None,
            multi_match: bool = False
    ) -> Any:
        """
        使用JSONPath提取响应数据（增强错误处理）
        """
        response = response or self.last_response
        if not response:
            self.logger.warning(f"[{DATETIME_NOW}] 无可用响应数据，无法执行JSONPath提取")
            return default

        try:
            data = response.json() if response.headers.get('Content-Type', '').startswith('application/json') else {}
            result = self.jsonpath_utils.extract(data, expr, multi_match=multi_match)
            self.logger.info(f"[{DATETIME_NOW}] JSONPath提取成功: {expr} -> {result}")
            return result if result is not None else default
        except Exception as e:
            self.logger.error(f"[{DATETIME_NOW}] JSONPath提取失败: {str(e)} | 表达式: {expr}")
            return default

    def info_response_encoding(self, response: requests.Response = None) -> None:
        """
        调试响应编码，帮助诊断中文显示问题
        """
        response = response or self.last_response
        if not response:
            self.logger.info(f"[{DATETIME_NOW}] 无可用响应数据")
            return

        self.logger.info(f"[{DATETIME_NOW}] 响应声明编码: {response.encoding}")
        self.logger.info(f"[{DATETIME_NOW}] 自动检测编码: {response.apparent_encoding}")

        try:
            self.logger.info(f"[{DATETIME_NOW}] JSON解析结果: {response.json()}")
        except ValueError:
            self.logger.warning(f"[{DATETIME_NOW}] 非JSON响应内容")

        try:
            content_sample = response.content.decode('utf-8', errors='replace')[:200]
            self.logger.info(f"[{DATETIME_NOW}] 响应内容样本: {content_sample}")
        except Exception as e:
            self.logger.warning(f"[{DATETIME_NOW}] 响应解码失败: {str(e)}")
