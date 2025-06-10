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


@allure.epic("客服后台-订单常规操作")
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


@allure.epic("客服后台-订单常规操作")
@allure.title("创建订单")
def test_order_create():
    global orderId_q
    data = Customer
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
    with allure.step("1. 创建订单"):
        url = PROJCET_URL + "/support/order/order-create"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取订单ID"):
        orderId_q = ak.get_text(r1.text, "$.data.reOrderId")
        time.sleep(3)


@allure.epic("客服后台-订单常规操作")
@allure.title("取消订单")
def test_cancel_order():
    data = {
        "reOrderId": orderId_q,
        "cancelReason": "取消订单-测试数据"
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
    with allure.step("1. 全部订单-订单列表-取消订单"):
        url = PROJCET_URL + "/support/order/cancel-order"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-订单常规操作")
@allure.title("订单详情")
def test_order_detail():
    data = {
        "reOrderId": orderId_q
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
    with allure.step("1. 进入订单详情界面，检查取消备注信息是否正确"):
        url = PROJCET_URL + "/support/order/order-detail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.repairOrderInfoVO.cancelReason")
        assert "取消订单-测试数据" == results
        time.sleep(3)


@allure.epic("客服后台-订单常规操作")
@allure.title("客服加标签")
def test_order_mark():
    data = {
        "reOrderId": orderId_q,
        "marks": [
            "测试加签数据"
        ]
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
    with allure.step("1. 客服添加标签"):
        url = PROJCET_URL + "/support/order/order-mark"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-订单常规操作")
@allure.title("全部订单")
def test_order_list():
    global reOrderId
    data = {
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
    with allure.step("1. 全部订单的订单列表"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 校验加签数据是否正确"):
        results2 = ak.get_text(r1.text, "$.data.orderList[0].marks[0]")
        assert "测试加签数据" == results2
    with allure.step("4. 获取订单id"):
        reOrderId = ak.get_text(r1.text, "$.data.orderList[0].orderId")
        time.sleep(3)


@allure.epic("客服后台-订单常规操作")
@allure.title("编辑订单")
def test_order_update():
    data = {
        "orderId": reOrderId,
        "faultName": "链条掉落",
        "phone": "136165102587",
        "brandId": 3,
        "remark": "测试修改订单备注",
        "longitude": 113.94705,
        "latitude": 22.530902,
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "town": "粤海街道",
        "otherAddress": "创业1期留学生创业大厦-修改数据",
        "address": "广东省深圳市南山区粤海街道"
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
    with allure.step("1. 进入订单编辑界面，编辑手机号、异常原因、地址信息"):
        url = PROJCET_URL + "/support/order/order-update"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-订单常规操作")
@allure.title("查看修改记录")
def test_order_record():
    data = {
        "orderId": reOrderId,
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
    with allure.step("1. 进入订单编辑界面，编辑手机号、异常原因、地址信息"):
        url = PROJCET_URL + "/support/order/order-record"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验：异常原因"):
        faultName = ak.get_text(r1.text, "$.data.list[0].newValue.faultName")
        assert "链条掉落" == faultName
    with allure.step("3. 结果校验：地址信息"):
        otherAddress = ak.get_text(r1.text, "$.data.list[0].newValue.otherAddress")
        assert "创业1期留学生创业大厦-修改数据" == otherAddress
    with allure.step("4. 结果校验：手机号"):
        phone = ak.get_text(r1.text, "$.data.list[0].newValue.phone")
        assert "136165102587" == phone
        time.sleep(3)


@allure.epic("客服后台-订单常规操作")
@allure.title("订单详情-校验修改订单备注信息")
def test_order_detail2():
    data = {
        "reOrderId": reOrderId
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
    with allure.step("1. 进入订单详情界面，检查取消备注信息是否正确"):
        url = PROJCET_URL + "/support/order/order-detail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        description = ak.get_text(r1.text, "$.data.repairOrderInfoVO.description")
        assert "测试修改订单备注" == description
        time.sleep(3)
