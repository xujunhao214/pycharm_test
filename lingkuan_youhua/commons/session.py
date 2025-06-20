# session.py
import os
import datetime
import requests
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
import logging.handlers
from lingkuan_youhua.commons.jsonpath_utils import JsonPathUtils

# 自动创建日志目录
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
    4. 优化请求和响应的编码处理
    """

    def __init__(self, base_url: str = ""):
        # self.base_url = base_url
        self.base_url = base_url.rstrip('/')  # 移除base_url末尾的斜杠
        self.g_vars: Dict[str, Any] = {}  # 存储全局变量
        self.last_response = None  # 存储最后一次响应
        self.named_urls = {}  # 存储命名URL
        super().__init__()

    def register_url(self, name: str, url: str):
        """注册命名URL（支持完整URL或基础路径）"""
        self.named_urls[name] = url.rstrip('/')  # 确保URL末尾无斜杠

    def build_url(self, url: str) -> str:
        """构建完整URL，处理命名URL和普通路径"""
        # 检查是否为命名URL（格式："命名URL/路径" 或 "命名URL"）
        for name, base in self.named_urls.items():
            if url.startswith(f"{name}/"):
                # 提取路径部分（如 "vps_api/subcontrol" → "subcontrol"）
                path = url[len(name) + 1:].lstrip('/')
                return f"{base}/{path}" if path else base

        # 检查是否为完整URL
        if url.startswith(("http://", "https://")):
            return url

        # 普通路径（使用base_url）
        return f"{self.base_url}/{url.lstrip('/')}" if self.base_url else url

    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        """预处理请求URL，支持命名URL"""
        full_url = self.build_url(url)

        # 记录请求日志（便于调试）
        logger.info(f"请求URL: {full_url}")

        # 处理JSON参数...（其他逻辑不变）
        if 'json' in kwargs and 'files' not in kwargs:
            headers = kwargs.get('headers', {})
            headers.setdefault('Content-Type', 'application/json; charset=utf-8')
            kwargs['headers'] = headers
            json_data = kwargs.pop('json')
            kwargs['data'] = json.dumps(json_data, ensure_ascii=False).encode('utf-8')

        return super().request(method, full_url, *args, **kwargs)

    def send_request_and_assert_success(session, method, url, data=None, params=None, files=None):
        """
        发送请求并断言响应消息为 "success"
        :param api: API会话对象
        :param method: 请求方法，如 "post", "delete"
        :param url: 请求URL
        :param data: 请求数据
        :param files: 上传的文件
        """
        if method == "post":
            session.post(url, json=data, files=files)
        if method == "get":
            session.get(url, params=params)
        if method == "put":
            session.put(url, json=data)
        elif method == "delete":
            session.delete(url, json=data)
        else:
            raise ValueError(f"不支持的请求方法: {method}")

        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)

    def query_db_and_check_result(db, sql, expected_empty=False):
        """
        查询数据库并检查结果
        :param db: 数据库连接对象
        :param sql: SQL查询语句
        :param expected_empty: 是否期望查询结果为空
        """
        with db.cursor() as cursor:
            try:
                cursor.execute(sql)
                result = cursor.fetchone()
                if expected_empty:
                    assert result is None, f"查询结果不为空，数据：{result}"
                    logging.info("删除成功：数据库中已无该记录")
                else:
                    assert result is not None, "查询结果为空，无法进行对比"
                    logging.info(f"查询成功，数据：{result}")
            except Exception as e:
                logging.error(f"查询数据库时发生错误：{str(e)}")
                raise

    def send(self, request: requests.PreparedRequest, *args, **kwargs) -> requests.Response:
        """
        发送请求并记录完整日志，改进编码处理
        """
        # 记录请求日志
        req_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.info(f"{req_time}发送请求>>>>>>>       接口地址={request.method} {request.url}")
        logger.info(f"{req_time}发送请求>>>>>>>       请求头={request.headers}")

        # 安全地处理请求体编码
        try:
            request_body = request.body.decode('utf-8') if request.body else '无'
        except UnicodeDecodeError:
            request_body = f"二进制数据 ({len(request.body)} bytes)" if request.body else '无'
        logger.info(f"{req_time}发送请求>>>>>>>       请求体={request_body}")

        # 发送请求
        response = super().send(request, **kwargs)
        self.last_response = response  # 保存响应

        # 记录响应日志
        resp_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.info(f"{resp_time}接收响应<<<<<<<       状态码={response.status_code}")
        logger.info(f"{resp_time}接收响应<<<<<<<       响应头={response.headers}")

        # 安全地处理响应体编码
        try:
            response_body = response.content.decode('utf-8')[:5000] if response.content else '无'
        except UnicodeDecodeError:
            response_body = f"二进制数据 ({len(response.content)} bytes)" if response.content else '无'
        logger.info(f"{resp_time}接收响应<<<<<<<       响应体={response_body}")

        return response

    def extract_jsonpath(
            self,
            expr: str,
            response: requests.Response = None,
            default: Any = None,
            multi_match: bool = False
    ) -> Any:
        """
        使用工具类提取 JSONPath 值，增强错误处理
        """
        response = response or self.last_response
        if not response:
            logger.warning("错误: 没有可用的响应数据")
            return default

        try:
            data = response.json()
        except ValueError as e:
            logger.warning(f"错误: 无法解析响应为JSON: {str(e)}")
            logger.warning(f"响应内容: {response.text[:500]}...")  # 显示部分响应内容用于调试
            return default

        try:
            return JsonPathUtils.extract(
                data=data,
                expr=expr,
                default=default,
                multi_match=multi_match
            )
        except Exception as e:
            logger.warning(f"错误: JSONPath提取失败: {str(e)}")
            logger.warning(f"JSONPath表达式: {expr}")
            logger.warning(f"响应数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return default

    def debug_response_encoding(self, response: requests.Response = None) -> None:
        """
        调试响应编码，帮助诊断中文显示问题
        """
        response = response or self.last_response
        if not response:
            logger.info("没有可用的响应数据")
            return

        logger.info(f"响应声明的编码: {response.encoding}")
        logger.info(f"自动检测的编码: {response.apparent_encoding}")

        try:
            json_data = response.json()
            logger.info(f"响应JSON解析成功:{json_data}")
        except ValueError:
            logger.warning(f"响应无法解析为JSON:{json_data}")

        # 显示响应内容的前500个字符（安全处理编码）
        try:
            content_sample = response.content.decode('utf-8')[:500]
            logger.info(f"响应内容样本: {content_sample}")
        except UnicodeDecodeError:
            logger.warning("响应内容无法以UTF-8解码")
