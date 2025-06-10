import os
import datetime
import logging
import requests

# 自动创建日志目录
log_dir = "./Logs"
os.makedirs(log_dir, exist_ok=True)

# 配置日志 - 明确指定编码为UTF-8
file_handler = logging.FileHandler(f"{log_dir}/requests.log", mode="a", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger = logging.getLogger("requests.session")
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


class JunhaoSession(requests.Session):
    """
    徐俊豪的request二次封装：
    1.支持BaseURL（环境切换）
    2.支持日志记录
    """

    def __init__(self, base_url=""):
        self.base_url = base_url
        super().__init__()

    def request(
            self,
            method,
            url,
            *args,
            **kwargs
    ):
        # 如果接口地址是相对地址
        if not url.startswith("http"):
            # 自动添加base_url
            url = self.base_url + url

        return super().request(method, url, *args, **kwargs)

    # 日志
    def send(self, request: requests.PreparedRequest, *args, **kwargs):
        logger.info(f"发送请求>>>>>>>       接口地址={request.method} {request.url}")
        logger.info(f"发送请求>>>>>>>       请求头={request.headers}")
        logger.info(f"发送请求>>>>>>>       请求体={request.body}")

        response = super().send(request, **kwargs)
        logger.info(f"接收响应<<<<<<<       状态码={response.status_code}")
        logger.info(f"接收响应<<<<<<<       响应头={response.headers}")
        logger.info(f"接收响应<<<<<<<       响应体={response.content}")

        return response
# import os
# import datetime
# import logging
# import requests
# import json
# from copy import deepcopy
#
# # 自动创建日志目录
# log_dir = "./Logs"
# os.makedirs(log_dir, exist_ok=True)
#
# # 配置日志 - 明确指定编码为UTF-8
# file_handler = logging.FileHandler(f"{log_dir}/requests.log", mode="a", encoding="utf-8")
# formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# file_handler.setFormatter(formatter)
#
# logger = logging.getLogger("requests.session")
# logger.addHandler(file_handler)
# logger.setLevel(logging.INFO)
#
# # 敏感字段列表，用于脱敏处理
# SENSITIVE_FIELDS = {"password", "token", "access_token", "refresh_token", "Authorization"}
#
#
# class JunhaoSession(requests.Session):
#     """
#     增强版requests会话类，支持：
#     1. BaseURL自动拼接（方便环境切换）
#     2. 完整的请求/响应日志记录（带敏感信息脱敏）
#     3. 自动处理相对路径
#     4. 统一的时间格式
#     5. 更友好的日志结构
#     """
#
#     def __init__(self, base_url="", log_module="default"):
#         super().__init__()
#         self.base_url = base_url  # 设置基础URL
#         self.log_module = log_module  # 日志模块标识
#
#     def request(self, method, url, *args, **kwargs):
#         # 处理相对路径URL，自动拼接BaseURL
#         if not url.startswith(("http://", "https://")):
#             url = self.base_url + url
#
#         # 记录请求开始时间
#         start_time = datetime.datetime.now()
#
#         # 调用父类方法发送请求
#         response = super().request(method, url, *args, **kwargs)
#
#         # 计算请求耗时
#         elapsed_time = datetime.datetime.now() - start_time
#
#         # 记录请求和响应信息
#         self._log_request(method, url, kwargs, start_time)
#         self._log_response(response, elapsed_time)
#
#         return response
#
#     def _log_request(self, method, url, kwargs, start_time):
#         """记录请求信息（带脱敏处理）"""
#         # 格式化请求时间
#         request_time = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#
#         # 记录请求行
#         logger.info(f"[{self.log_module}] {request_time} 发送请求 >>>> 方法={method} URL={url}")
#
#         # 记录请求头（脱敏处理）
#         headers = self._sanitize_data(kwargs.get("headers", {}))
#         logger.info(f"[{self.log_module}] {request_time} 发送请求 >>>> 请求头={headers}")
#
#         # 记录请求体（处理不同类型的请求体并脱敏）
#         body = kwargs.get("data") or kwargs.get("json")
#         if body:
#             # 处理JSON格式请求体
#             if isinstance(body, (dict, list)):
#                 sanitized_body = self._sanitize_data(body)
#                 body_str = json.dumps(sanitized_body, ensure_ascii=False, default=str)
#             else:
#                 # 非JSON格式，尝试转换为字符串
#                 body_str = str(body)
#
#             # 限制大请求体的日志长度
#             logger.info(
#                 f"[{self.log_module}] {request_time} 发送请求 >>>> 请求体={body_str[:5000]}{'...' if len(body_str) > 5000 else ''}")
#
#     def _log_response(self, response, elapsed_time):
#         """记录响应信息"""
#         # 格式化响应时间
#         response_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#
#         # 记录响应状态码和耗时
#         logger.info(
#             f"[{self.log_module}] {response_time} 接收响应 <<<< 状态码={response.status_code} 耗时={elapsed_time.total_seconds() * 1000:.2f}ms")
#
#         # 记录响应头
#         logger.info(f"[{self.log_module}] {response_time} 接收响应 <<<< 响应头={dict(response.headers)}")
#
#         # 记录响应体（尝试以文本形式记录，失败则以二进制长度记录）
#         try:
#             content = response.text
#
#             # 尝试解析JSON响应并脱敏
#             try:
#                 json_content = json.loads(content)
#                 sanitized_content = self._sanitize_data(json_content)
#                 content_str = json.dumps(sanitized_content, ensure_ascii=False, default=str)
#             except (json.JSONDecodeError, TypeError):
#                 content_str = content
#
#             logger.info(
#                 f"[{self.log_module}] {response_time} 接收响应 <<<< 响应体={content_str[:5000]}{'...' if len(content_str) > 5000 else ''}")
#         except UnicodeDecodeError:
#             logger.info(
#                 f"[{self.log_module}] {response_time} 接收响应 <<<< 响应体=[二进制数据，长度={len(response.content)}]")
#
#     def _sanitize_data(self, data):
#         """递归脱敏敏感字段"""
#         if isinstance(data, dict):
#             sanitized = {}
#             for key, value in data.items():
#                 if key.lower() in SENSITIVE_FIELDS:
#                     # 对敏感字段进行脱敏处理
#                     sanitized[key] = "[SENSITIVE]"
#                 else:
#                     # 递归处理嵌套结构
#                     sanitized[key] = self._sanitize_data(value)
#             return sanitized
#         elif isinstance(data, list):
#             return [self._sanitize_data(item) for item in data]
#         else:
#             return data
