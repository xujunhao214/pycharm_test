import allure
import requests
from jsonpath_ng import parse
import json
import time
from datetime import datetime, timedelta


class ApiKey:
    def __init__(self, logger):
        self.session = requests.Session()  # 使用会话管理，自动处理cookies
        self.logger = logger

    @allure.step("发送GET请求")
    def get(self, url, headers=None, params=None, **kwargs):
        try:
            self.logger.info(f"GET请求: {url}")
            self.logger.debug(f"请求头: {headers}")
            self.logger.debug(f"请求参数: {params}")

            start_time = time.time()
            response = self.session.get(url=url, headers=headers, params=params, **kwargs)
            end_time = time.time()

            self.logger.info(f"响应状态码: {response.status_code}")
            self.logger.info(f"响应时间: {round((end_time - start_time) * 1000, 2)}ms")

            try:
                self.logger.debug(f"响应内容: {response.json()}")
            except:
                self.logger.debug(f"响应内容: {response.text}")

            response.raise_for_status()  # 自动检查HTTP状态码
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求异常: {str(e)}")
            allure.attach(str(e), "请求异常", allure.attachment_type.TEXT)
            raise

    @allure.step("发送POST请求")
    def post(self, url, headers=None, data=None, json=None, **kwargs):
        try:
            self.logger.info(f"POST请求: {url}")
            self.logger.debug(f"请求头: {headers}")
            if data:
                self.logger.debug(f"请求表单数据: {data}")
            if json:
                self.logger.debug(f"请求JSON数据: {json}")

            start_time = time.time()
            response = self.session.post(url=url, headers=headers, data=data, json=json, **kwargs)
            end_time = time.time()

            self.logger.info(f"响应状态码: {response.status_code}")
            self.logger.info(f"响应时间: {round((end_time - start_time) * 1000, 2)}ms")

            try:
                self.logger.debug(f"响应内容: {response.json()}")
            except:
                self.logger.debug(f"响应内容: {response.text}")

            response.raise_for_status()  # 自动检查HTTP状态码
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求异常: {str(e)}")
            allure.attach(str(e), "请求异常", allure.attachment_type.TEXT)
            raise

    @allure.step("获取返回结果中的值")
    def get_value(self, response, jsonpath_expr):
        try:
            if isinstance(response, requests.Response):
                response_data = response.json()
            else:
                try:
                    response_data = json.loads(response)
                except:
                    self.logger.error(f"响应内容不是有效的JSON格式: {response}")
                    raise ValueError("响应内容不是有效的JSON格式")

            self.logger.debug(f"使用JSONPath表达式 '{jsonpath_expr}' 提取值")
            expr = parse(jsonpath_expr)
            matches = [match.value for match in expr.find(response_data)]

            if not matches:
                error_msg = f"未找到匹配项: {jsonpath_expr}"
                self.logger.warning(error_msg)
                raise ValueError(error_msg)

            self.logger.debug(f"提取到的值: {matches[0]}")
            return matches[0]
        except Exception as e:
            self.logger.error(f"提取值失败: {str(e)}")
            raise
