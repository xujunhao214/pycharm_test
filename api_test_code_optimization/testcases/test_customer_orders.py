import allure
import pytest
import os
from api_test_code_optimization.common.logging_config import get_logger
from api_test_code_optimization.common.api_key import ApiKey
from api_test_code_optimization.common.sign_utils import generate_sign
from api_test_code_optimization.common.date_utils import get_current_timestamp, get_today_start_end_timestamp
from api_test_code_optimization.common.yaml_handler import YamlHandler

# 获取配置
config = YamlHandler("config.yaml").read_yaml()

# 获取日志记录器
logger = get_logger(__name__)

# 全局变量
token_auth = None
ak = None
reOrderId = None
shopName = None
maintainerId = None


@allure.epic("客服后台-全部订单-查询校验")
@allure.title("登录")
def test_auth_login():
    global token_auth, ak

    # 初始化API工具类
    ak = ApiKey(logger)

    # 准备请求数据
    body = {
        "userName": config["USERNAME"],
        "password": config["PASSWD"]
    }

    timestamp = get_current_timestamp()
    sign_str = generate_sign(
        config["app_key"],
        config["TOKEN_WEIXIU"],
        config["platform"],
        timestamp,
        body,
        config["secret"]
    )

    headers = {
        "Authorization": config["TOKEN_WEIXIU"],
        "AppKey": config["app_key"],
        "Platform": config["platform"],
        "Timestamp": timestamp,
        "Sign": sign_str,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 客服管理后台登录"):
        url = config["PROJCET_URL"] + "/support/auth/login"
        r1 = ak.post(url=url, json=body, headers=headers)

    with allure.step("2. 结果校验"):
        results = ak.get_value(r1, "$.msg")
        assert "OK" == results

    with allure.step("3. 获取token"):
        token_auth = ak.get_value(r1, "$.data.token")
        logger.info(f"获取到token: {token_auth}")


@allure.epic("客服后台-全部订单-查询校验")
@allure.title("全部订单")
def test_order_list():
    global reOrderId, shopName, maintainerId

    # 获取今日时间范围
    start_time, end_time = get_today_start_end_timestamp()

    body = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": start_time,
        "endTime": end_time,
        "maintainerId": "",
        "page": 1,
        "limit": 20
    }

    timestamp = get_current_timestamp()
    sign_str = generate_sign(
        config["app_key"],
        token_auth,
        config["platform"],
        timestamp,
        body,
        config["secret"]
    )

    headers = {
        "Authorization": token_auth,
        "AppKey": config["app_key"],
        "Platform": config["platform"],
        "Timestamp": timestamp,
        "Sign": sign_str,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 全部订单的全部列表数据展示"):
        url = config["PROJCET_URL"] + "/support/order/order-list"
        r1 = ak.post(url=url, json=body, headers=headers)

    with allure.step("2. 结果校验"):
        results = ak.get_value(r1, "$.msg")
        assert "OK" == results

    with allure.step("3. 获取订单号"):
        reOrderId = ak.get_value(r1, "$.data.orderList[0].orderId")
        logger.info(f"获取到订单号: {reOrderId}")

    with allure.step("4. 获取店铺名称"):
        shopName = ak.get_value(r1, "$.data.orderList[0].shopName")
        logger.info(f"获取到店铺名称: {shopName}")

    with allure.step("5. 获取维修工ID"):
        maintainerId = ak.get_value(r1, "$.data.orderList[0].maintainerId")
        logger.info(f"获取到维修工ID: {maintainerId}")
