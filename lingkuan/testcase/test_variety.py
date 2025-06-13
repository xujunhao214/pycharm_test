import json
import logging
import allure
import pytest
from lingkuan.commons.jsonpath_utils import JsonPathUtils
from lingkuan.VAR.VAR import *

JsonPathUtils = JsonPathUtils()


# @allure.title("品种管理-登录")
# @pytest.mark.dependency(name="login")
# def test_login(session,logged_session):
#     data = {
#         "username": USERNAME,
#         "password": PASSWORD,
#     }
#     headers = {
#         "Authorization": "${token}",
#         "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
#     }
#
#     with allure.step("1. 登录操作"):
#         session.post('/sys/auth/login', json=data, headers=headers)
#
#     with allure.step("2. 登录成功，提取access_token"):
#         access_token = session.extract_jsonpath("$.data.access_token")
#         print(f"access Token: {access_token}")
#         logging.info(f"access Token: {access_token}")
#         session.headers.update({
#             "Authorization": f"{access_token}",
#             "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
#         })


@allure.title("品种管理-添加品种")
def test_create_variety(session, logged_session):
    # 1. 读取CSV文件
    csv_path = "./Files/品种匹配导出模板.csv"
    with open(csv_path, 'rb') as f:
        csv_file = f.read()

    # 2. 构造请求参数（文件上传使用files参数）
    files = {
        "file": ("品种匹配导出模板.csv", csv_file, "text/csv")
    }
    data = {
        "templateName": "测试"
    }
    with allure.step("1. 添加品种"):
        session.post('/mascontrol/variety/addTemplate', files=files, data=data)
    with allure.step("2. 判断是否添加成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg


@allure.title("品种管理-获取新加品种的ID")
def test_get_variety_id(session, logged_session):
    global variety_id
    with allure.step("1. 品种标题头部信息"):
        session.get('/mascontrol/variety/templateName')
    with allure.step("2. 获取新加品种的ID"):
        variety_id = session.extract_jsonpath("$.data[-1].templateId")
        logging.info(f"新品种ID：{variety_id}")


@allure.title("品种管理-删除新添加的品种")
def test_delete_variety(session):
    data = [variety_id]
    with allure.step("1. 删除新添加的品种"):
        session.delete('/mascontrol/variety/deleteTemplate', json=data)
    with allure.step("2. 判断是否删除成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
