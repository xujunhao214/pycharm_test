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


# 获取策略账号数据
@allure.title("获取策略账号数据")
def test_get_traderList(session):
    global traderList_ids, id_value
    with allure.step("1. 获取列表数据"):
        data_list = session.get('/mascontrol/cloudTrader/traderList')
        json_data = data_list.json()

    with allure.step("2. 获取全部策略账号ID"):
        # traderList_ids = JsonPathUtils.extract("$.data[10].id")
        # 1. 提取单个 id 值（取第一个匹配项）
        id_list = JsonPathUtils.extract(
            data=json_data,  # API 响应数据
            expr="$.data[*].id",  # JSONPath 表达式
            default=None,  # 未匹配到时的默认值
            multi_match=True  # 返回所有id数据
        )

        print("id 列表:", id_list)


# 新增云策略-已挂靠账号
@allure.title("新增云策略-已挂靠账号")
def test_create_cloudTrader(session):
    with allure.step("1. 选择一个策略账号,新增云策略"):
        data = {
            "cloudId": "74",
            "sourceType": 0,
            "remark": "测试",
            "runningStatus": 0,
            "traderId": id_value,
            "managerIp": "",
            "managerAccount": "",
            "managerPassword": "",
            "account": "",
            "platform": "",
            "templateId": ""
        }
        session.post('/mascontrol/cloudTrader', json=data)
    with allure.step("2. 判断是否添加成功"):
        msg = JsonPathUtils.extract("$.msg")
        print(msg)
