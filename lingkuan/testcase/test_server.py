import json
import logging
import time
import allure
import pytest
from lingkuan.commons.jsonpath_utils import JsonPathUtils
from lingkuan.VAR.VAR import *

JsonPathUtils = JsonPathUtils()


# @allure.title("品种管理-登录")
# @pytest.mark.dependency(name="login")
# def test_login(session, logged_session):
#     global access_token
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

@pytest.mark.dependency(name="create_server")
@allure.title("服务器管理-新增服务器")
def test_create_server(session, logged_session):
    data = {
        "serverName": SERVERNAME
    }
    with allure.step("1. 请求新增服务器数据接口"):
        session.post('/mascontrol/speed/addServer', json=data)
    with allure.step("2. 判断是否新增成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(2)


@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-查询服务器列表")
def test_list_server(session, logged_session):
    params = {
        "page": "1",
        "limit": "50",
        "brokerName": "",
        "serverName": SERVERNAME,
        "serverNode": "",
        "order": "",
        "asc": "false",
    }
    with allure.step("1. 根据服务器名称，查询服务器"):
        session.get('/mascontrol/speed/listTestServer', params=params)
    with allure.step("2. 获取查询服务器信息"):
        server_id = session.extract_jsonpath("$.data.list[0].id")
        logging.info(f"服务器id：{server_id}")
        time.sleep(2)


@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-手动添加服务器节点")
def test_addservernode(session, logged_session):
    data = {
        "serverName": SERVERNAME,
        "platformType": None,
        "serverNodeList": [SERVERNODE]
    }
    with allure.step("1. 手动输入节点数据，进行添加"):
        session.post('/mascontrol/speed/addServerNode', json=data)
    with allure.step("2. 判断是否新增成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(2)


@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-节点搜索")
def test_nodesearch(session, logged_session):
    global servername_search
    params = {
        "serverName": SERVERNAME_SEARCH,
        "exact": "0",
    }
    with allure.step("1. 节点搜索"):
        session.get('/mascontrol/speed/nodeSearch', params=params)
    with allure.step("2. 提取节点数据"):
        servername_search = session.extract_jsonpath("$.data[0].brokers[0].access[0].nodeName")
        logging.info(f"提取的节点数据：{servername_search}")
        time.sleep(2)


@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-添加服务器节点")
def test_addservernode2(session, logged_session):
    data = {
        "serverName": SERVERNAME,
        "platformType": None,
        "serverNodeList": [SERVERNODE, servername_search]
    }
    with allure.step("1. 输入模糊的节点数据，进行查询，然后添加"):
        session.post('/mascontrol/speed/addServerNode', json=data)
    with allure.step("2. 判断是否新增成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)


@pytest.mark.dependency(names="test_list_servernode")
@allure.title("服务器管理-节点数据列表")
def test_list_servernode(session, logged_session):
    global serverNode_query
    params = {
        "name": SERVERNAME,
    }
    with allure.step("1. 节点数据列表"):
        session.get('/mascontrol/speed/listServerAndNode', params=params)
    with allure.step("2. 提取节点数据"):
        serverNode_query = session.extract_jsonpath("$.data[0].serverNode")
        logging.info(f"提取的节点数据：{serverNode_query}")
        time.sleep(2)


@pytest.mark.dependency(depends=["test_list_servernode"])
@allure.title("服务器管理-删除服务器节点")
def test_delete_servernode(session, logged_session):
    data = {
        "serverName": SERVERNAME,
        "serverNodeList": [
            serverNode_query
        ]
    }
    with allure.step("1. 删除服务器节点"):
        session.delete('/mascontrol/speed/deleteServerNode', json=data)
    with allure.step("2. 判断是否删除成功"):
        msg = session.extract_jsonpath("$.data")
        logging.info(f"断言：预期：删除成功 实际：{msg}")
        assert "删除成功" == msg
        time.sleep(2)


@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-进行测速")
def test_measureServer(session, logged_session):
    data = {
        "servers": [
            SERVERNAME
        ]
    }
    with allure.step("1. 对服务器进行测速"):
        session.post('/mascontrol/speed/measureServer', json=data)
    with allure.step("2. 判断是否测速成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(2)


@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-节点列表数据")
def test_listServerAndNode(session, logged_session):
    global serverNode_id, serverNode_serverid, serverNode_testId, serverNode_serverNode, serverNode_speed, serverNode_vpsId, serverNode_vpsName
    params = {
        "name": SERVERNAME
    }
    with allure.step("1. 请求节点列表接口"):
        session.get('/mascontrol/speed/listServerAndNode', params=params)
    with allure.step("2. 获取数据"):
        serverNode_id = session.extract_jsonpath("$.data[1].id")
        logging.info(f"serverNode_id：{serverNode_id}")

        serverNode_serverid = session.extract_jsonpath("$.data[1].serverId")
        logging.info(f"serverNode_serverid：{serverNode_serverid}")

        serverNode_testId = session.extract_jsonpath("serverNode_testId")
        logging.info(f"serverNode_testId：{serverNode_testId}")

        serverNode_serverNode = session.extract_jsonpath("$.data[1].serverNode")
        logging.info(f"serverNode_serverNode：{serverNode_serverNode}")

        serverNode_speed = session.extract_jsonpath("$.data[1].speed")
        logging.info(f"serverNode_speed：{serverNode_speed}")

        serverNode_vpsId = session.extract_jsonpath("$.data[1].vpsId")
        logging.info(f"serverNode_vpsId：{serverNode_vpsId}")

        serverNode_vpsName = session.extract_jsonpath("$.data[1].vpsName")
        logging.info(f"serverNode_vpsName：{serverNode_vpsName}")


@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-编辑默认节点")
def test_updateServerNode(session, logged_session):
    data = [{
        "id": serverNode_id,
        "serverId": serverNode_serverid,
        "serverName": SERVERNAME,
        "platformType": "MT4",
        "testId": serverNode_testId,
        "serverNode": serverNode_serverNode,
        "speed": serverNode_speed,
        "version": 0,
        "deleted": 0,
        "creator": 10000,
        "createTime": DATETIME_NOW,
        "updater": 10000,
        "testUpdateTime": DATETIME_NOW,
        "vpsId": serverNode_vpsId,
        "vpsName": serverNode_vpsName,
        "serverUpdateTime": None,
        "isDefaultServer": 0,
        "brokerName": None
    }]
    with allure.step("1. 编辑默认节点"):
        session.put('/mascontrol/speed/updateServerNode', json=data)
    with allure.step("2. 判断修改成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(2)

@pytest.mark.dependency(depends=["create_server"])
@allure.title("服务器管理-删除服务器")
def test_delete_server(session, logged_session):
    data = {
        "serverName": SERVERNAME
    }
    with allure.step("1. 删除服务器"):
        session.delete('/mascontrol/speed/deleteServer', json=data)
    with allure.step("2. 判断是否删除成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(2)
