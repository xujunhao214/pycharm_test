import json
import logging
import allure
import pytest
from lingkuan.commons.jsonpath_utils import JsonPathUtils

JsonPathUtils = JsonPathUtils()


# 参数化
@pytest.mark.parametrize(
    "data, res_msg",
    [
        # 正确的用户名和密码
        ({"username": "admin",
          "password": "04739db02172e04f63f5278211184deec745bad9d797882b343e7201898d8da1d9fced282f6b271d3815a5057482e62c6f6b88dacb642ba05632bd2ee348101c76cb1f86b70f91695fd1cff11fce76246f044ace477cdbfa1e3e1521b19b023b14c7165e82c5"},
         "success"),
    ]
)
@allure.title("登录")
def test_login(session, data, res_msg):
    headers = {
        "Authorization": "${token}",
        "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
    }

    with allure.step("1. 登录操作"):
        session.post('/sys/auth/login', json=data, headers=headers)

    with allure.step("2. 登录成功，提取access_token"):
        if res_msg == "success":
            access_token = session.extract_jsonpath("$.data.access_token")
            print(f"access Token: {access_token}")
            logging.info(f"access Token: {access_token}")
            session.headers.update({
                "Authorization": f"{access_token}",
                "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
            })


# 参数化
@pytest.mark.parametrize(
    "platformList, res_msg",
    [
        # 错误的节点
        (["1234567"], "该服务器节点为空"),
        # 正确的服务器节点
        (["AdvancedMarkets-Demo"], "success"),

    ]
)
@allure.title("新增列表数据")
@pytest.mark.dependency(name="create_platform")
def test_create_platform(session, platformList, res_msg):
    data = {
        "brokerName": "测试",
        "platformType": "MT4",
        "platformList": platformList,
        "remark": "测试数据",
        "logo": "https://java-copytrade-new.oss-cn-beijing.aliyuncs.com/test/20250613/yanshi_51459.png",
        "maxLots": "1.00"
    }

    with allure.step("1. 新增列表数据"):
        session.post("/mascontrol/platform", json=data)
    with allure.step("2. 校验是否新增成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert msg == res_msg, f"是否一致：预期：success 实际：{msg} "

@allure.title("获取列表数据")
@pytest.mark.dependency(depends=["create_platform"])
def test_platfor_list():
    pass


@allure.title("编辑列表数据")
@pytest.mark.dependency(depends=["create_platform"])
def test_update_platform(session, platformList, res_msg):
    data = {
        "id": 2534,
        "brokerName": "测试编辑",
        "platformType": "MT4",
        "server": "AdvancedMarkets-Demo",
        "serverNode": "185.97.160.58:443",
        "remark": "测试数据编辑",
        "version": 0,
        "deleted": 0,
        "creator": "10000",
        "createTime": "2025-06-13 14:18:41",
        "updater": "null",
        "updateTime": "2025-06-13 14:18:41",
        "platformList": ["AdvancedMarkets-Demo"],
        "logo": "https://java-copytrade-new.oss-cn-beijing.aliyuncs.com/test/20250613/yanshi_51459.png",
        "maxLots": "2.00"
    }

    with allure.step("1. 编辑列表数据"):
        session.put("/mascontrol/platform", json=data)
    with allure.step("2. 校验编辑是否提交成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert msg == res_msg, f"是否一致：预期：success 实际：{msg} "
