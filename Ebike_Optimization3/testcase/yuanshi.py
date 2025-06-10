import allure
from jsonpath_ng import parse
import requests


# 工具类/关键字驱动类/基类
class ApiKey:
    @allure.step("发送get请求")
    def get(self, url, headers=None, params=None, **kwargs):
        return requests.get(url=url, headers=headers, params=params, **kwargs)

    @allure.step("发送post请求")
    def post(self, url, headers, data=None, json=None, **kwargs):
        return requests.post(url=url, headers=headers, data=data, json=json, **kwargs)

    @allure.step("获取返回结果字典值")
    def get_text(self, response, key):
        """
        :param response: 响应报文，默认为json格式
        :param key: jsonpath的表达式
        :return: 匹配的第一个值
        """
        dict_data = json.loads(response)
        jsonpath_expr = parse(key)
        matches = [match.value for match in jsonpath_expr.find(dict_data)]

        if not matches:
            raise ValueError(f"未找到匹配项: {key}")

        return matches[0]


import hashlib
import json


def sign(app_key: str, authorization: str, platform: str, timestamp: str, body: object, secret: str):
    signContent = "AppKey" + app_key + "Authorization" + authorization + "Platform" + platform + "Timestamp" + timestamp
    # 如果body非空空，则将body json序列化并拼接到后面
    if body is not None:
        signContent = signContent + json.dumps(body)
    # 将secret拼接到signContent后面
    signContent = signContent + secret
    # 将signContent全部转为小写
    signContent = signContent.lower()
    print(signContent)
    # 用MD5对signContent进行处理
    md5 = hashlib.md5()
    md5.update(signContent.encode('utf-8'))
    return md5.hexdigest()


import time

app_key = "apiFox"
platform = "apiFox"
secret = "53c8eae1c4e4ecd5adb66a6b8b47a45f"
# 获取当前时间戳（转换为毫秒级）
timestamp = str(int(time.time() * 1000))
# print(timestamp)

# 获取今日开始结束时间的时间戳
from dateutil import parser
import datetime

now = datetime.datetime.now()
time_day = now.strftime('%Y-%m-%d')
print(time_day)

date_str = str(time_day) + " 00:00:00"
print(date_str)
dt = parser.parse(date_str)
timestamp_start = round(dt.timestamp()) * 1000
print("时间戳：", timestamp_start)

date_str2 = str(time_day) + " 23:59:59"
dt2 = parser.parse(date_str2)
timestamp_end = round(dt2.timestamp()) * 1000
print("时间戳：", timestamp_end)

"""
门店后台：https://api-c.ebk365.com:26887/b/shop/auth/login
"""
SHOP_URL = "https://api-c.ebk365.com:26887/b"
SHOP_name = "13616510214"
SHOP_password = "1ef70db0a7669ce2f89e78fb2eaab0f9"

import time
import allure
import pytest
import os
from Ebike_Optimization3.VAR.VAR import *
from Ebike_Optimization3.api_keyword.api_key import ApiKey
from allure import severity, severity_level
from Ebike_Optimization3.api_keyword.sign import sign
from Ebike_Optimization3.VAR.Customer import *


@allure.epic("客服后台-全部订单-查询校验")
@allure.title("登录")
def test_auth_login():
    global token_auth, ak
    ak = ApiKey()
    body = {
        "userName": USERNAME,
        "password": PASSWD
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, body, secret)

    headers = {
        "Authorization": TOKEN_WEIXIU,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 客服管理后台登录"):
        url = PROJCET_URL + "/support/auth/login"
        r1 = ak.post(url=url, json=body, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取token"):
        token_auth = ak.get_text(r1.text, "$.data.token")
        time.sleep(3)


@allure.epic("客服后台-全部订单-查询校验")
@allure.title("全部订单")
def test_order_list():
    global reOrderId, shopName, maintainerId
    body = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "maintainerId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, body, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 全部订单的全部列表数据展示"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=body, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取订单号"):
        reOrderId = ak.get_text(r1.text, "$.data.orderList[0].orderId")
    with allure.step("4. 获取店铺名称"):
        shopName = ak.get_text(r1.text, "$.data.orderList[0].shopName")
    with allure.step("4. 获取维修工ID"):
        maintainerId = ak.get_text(r1.text, "$.data.orderList[0].maintainerId")
        time.sleep(3)


import os
import pytest

if __name__ == '__main__':
    # 执行pytest并生成Allure结果
    pytest.main([
        '-v',
        __file__,  # 执行当前文件
        '--alluredir', 'report/results',
        '--clean-alluredir'
    ])

    # 生成Allure报告
    os.system('allure generate report/results -o report/report-allure --clean')
