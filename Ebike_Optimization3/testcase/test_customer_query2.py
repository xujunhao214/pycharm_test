#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import allure
import pytest
import os
from Ebike_Optimization3.VAR.VAR import *
from Ebike_Optimization3.api_keyword.api_key import ApiKey
from allure import severity, severity_level
from Ebike_Optimization3.api_keyword.sign import sign
from Ebike_Optimization3.VAR.Customer import *


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("登录")
def test_auth_login():
    global token_auth, ak
    ak = ApiKey()
    data = {
        "userName": USERNAME,
        "password": PASSWD
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

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
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取token"):
        token_auth = ak.get_text(r1.text, "$.data.token")
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单")
def test_order_list():
    global reOrderId, shopName, maintainerId
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 拖车订单的全部列表数据展示"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
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


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("存在的用户电话查询")
def test_maintainerPhone():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "addressKeyword": "",
        "phone": "13207258183",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入存在的用户电话，点击查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.orderList[0].peopleTel")
        assert "13207258183" == results
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("不存在的用户电话查询")
def test_maintainerPhone_no():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "addressKeyword": "",
        "phone": "123456543",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入不存在的用户电话，点击查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验，判断值是否为空"):
        results = ak.get_text(r1.text, "$.data.orderList")
        assert results is None
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("查询已经完结的订单")
def test_status():
    data = {
        "shopName": "",
        "status": 6,
        "faultName": "",
        "addressKeyword": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 选择订单完结状态，点击查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.orderList[0].status")
        assert results == 6
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-存在的订单号查询")
def test_query_reOrderId():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": reOrderId,
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入存在的订单号，点击查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        reOrderId_check = ak.get_text(r1.text, "$.data.orderList[0].orderId")
        assert reOrderId_check == reOrderId
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-不存在的订单号查询")
def test_query_noreOrderId():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "123456712345678",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入不存在的订单号，点击查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验，判断值是否为空"):
        results = ak.get_text(r1.text, "$.data.orderList")
        assert results is None
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-维修工查询")
def test_query_maintainerId():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": maintainerId,
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 选择维修工"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        maintainerId_check = ak.get_text(r1.text, "$.data.orderList[0].maintainerId")
        assert maintainerId_check == maintainerId
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-故障类型列表")
def test_faultName():
    global faultName
    data = {

    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 故障类型列表"):
        url = PROJCET_URL + "/support/order/fault-type-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 提取故障类型"):
        faultName = ak.get_text(r1.text, "$.data[1]")
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-获取电动车品牌ID")
def test_brandId():
    global brandId
    data = {

    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 电动车品牌列表"):
        url = PROJCET_URL + "/support/order/brand-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 提取电动车品牌ID"):
        brandId = ak.get_text(r1.text, "$.data.brands[2].id")
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-获取建单人ID")
def test_fault_type_list():
    global operationId
    data = {

    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 电动车品牌列表"):
        url = PROJCET_URL + "/support/order/support-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 提取建单人ID"):
        operationId = ak.get_text(r1.text, "$.data.supportList[1].supportId")
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-故障类型查询")
def test_query_faultName():
    data = {
        "shopName": "",
        "status": "",
        "faultName": faultName,
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 选择一个故障类型，进行查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.orderList[0].faultName")
        assert results == faultName
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-建单人查询")
def test_query_operationId():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": operationId,
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)

    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 选择一个建单人，进行查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-获取订单ID")
def test_order_list2():
    global reOrderId2
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": brandId,
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入存在的订单号"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 提取订单ID"):
        reOrderId2 = ak.get_text(r1.text, "$.data.orderList[0].orderId")
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("订单详情-校验品牌")
def test_order_detail():
    global maintainOrderId
    data = {
        "reOrderId": reOrderId2
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 进入订单详情界面"):
        url = PROJCET_URL + "/support/order/order-detail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 校验品牌是否正确"):
        results = ak.get_text(r1.text, "$.data.repairOrderInfoVO.brandId")
        assert results == brandId
    with allure.step("3. 获取维修单号"):
        maintainOrderId = ak.get_text(r1.text, "$.data.maintainOrderInfoVO.maintainOrderId")
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-存在的维修单号查询")
def test_maintainOrderId():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": maintainOrderId,
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入存在的维修单号，进行查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-不存在的维修单号查询")
def test_maintainOrderId_no():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "maintainerId": "12345678954321",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入不存在的维修单号，进行查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验，判断值是否为空"):
        results = ak.get_text(r1.text, "$.data.orderList")
        assert results is None
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-地址查询")
def test_otherAddress():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "addressKeyword": OTHERADRESS,
        "phone": "",
        "orderId": "",
        "time": [
            1710569241835,
            1713247641835
        ],
        "startTime": 1710569241835,
        "endTime": 1713247641835,
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入地址，进行查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.orderList[0].otherAddress")
        assert OTHERADRESS == results
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("拖车订单-不存在的地址查询")
def test_otherAddress_no():
    data = {
        "shopName": "",
        "status": "",
        "faultName": "",
        "addressKeyword": "测试地址",
        "phone": "",
        "orderId": "",
        "time": [
            timestamp_start,
            timestamp_end
        ],
        "startTime": timestamp_start,
        "endTime": timestamp_end,
        "isTrailer": 1,
        "maintainerId": "",
        "maintainOrderId": "",
        "brandId": "",
        "operationId": "",
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 输入不存在的地址，进行查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验，判断值是否为空"):
        results = ak.get_text(r1.text, "$.data.orderList")
        assert results is None
        time.sleep(3)


@allure.epic("客服后台-拖车订单-查询校验")
@allure.title("订单类型查询")
def test_publishOrigin():
    data = {
        "time": [],
        "startTime": "",
        "endTime": "",
        "isTrailer": 1,
        "publishOrigin": 1,
        "page": 1,
        "limit": 20
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, token_auth, platform, timestamp, data, secret)
    headers = {
        "Authorization": token_auth,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 选择一个订单类型，进行查询"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.orderList[0].publishOrigin")
        assert results == 1
        time.sleep(3)
