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
from Ebike_Optimization3.VAR.Worker import *


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("客服后台-登录")
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


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("客服后台-创建订单")
def test_order_create():
    global reorderId
    timestamp = str(int(time.time() * 1000))
    data = Customer
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
        reorderId = ak.get_text(r1.text, "$.data.reOrderId")
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("客服后台-全部订单列表-校验订单是否是普通订单")
def test_order_list2():
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
    with allure.step("1. 全部订单列表"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 校验订单类型是否是普通单"):
        results = ak.get_text(r1.text, "$.data.orderList[0].orderType")
        assert results == 0
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("客服后台-修改预约时间")
def test_updateReverseTime_kf():
    timestamp = str(int(time.time() * 1000))
    data = {
        "orderId": reorderId,
        "faultName": "链条掉落",
        "phone": "13207258183",
        "backUpTel": "143124",
        "brandId": 37,
        "remark": "",
        "longitude": 113.94705,
        "latitude": 22.530902,
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "town": "粤海街道",
        "otherAddress": "创业1期留学生创业大厦",
        "isReverseOverTime": 1,
        "isContactOverTime": 1,
        "isArriveOverTime": 1,
        "reserveTime": timestamp
    }
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
    with allure.step("1. 修改预约时间"):
        url = PROJCET_URL + "/support/order/order-update"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("客服后台-全部订单列表-校验订单是否是预约单")
def test_order_list3():
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
    with allure.step("1. 全部订单列表"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 校验订单类型是否是预约单"):
        results = ak.get_text(r1.text, "$.data.orderList[0].orderType")
        assert results == 1
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-首页")
def test_head():
    data = {

    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)
    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1.维修工首页"):
        url = PROJCET_URL_WORKER + "/home/head"
        r1 = ak.post(url=url, json=data, headers=headers)
        results = ak.get_text(r1.text, "$.msg")
    with allure.step("2.结果校验"):
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-订单列表")
def test_getNewOrderList():
    global maintainOrderId
    data = {

    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)
    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 维修工接单列表"):
        url = PROJCET_URL_WORKER + "/order/getNewOrderList"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取新的订单id"):
        maintainOrderId = ak.get_text(r1.text, "$.data.orderList[0].maintainOrderId")
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-订单详情")
def test_getOrderDetail():
    data = {
        "maintainOrderId": maintainOrderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)
    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 订单详情"):
        url = PROJCET_URL_WORKER + "/order/getOrderDetail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-接单")
def test_confirmOrder():
    data = {
        "maintainOrderId": maintainOrderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)
    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 点击接单"):
        url = PROJCET_URL_WORKER + "/order/confirmOrder"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-修改预约时间")
def test_updateReverseTime():
    timestamp = str(int(time.time() * 1000))
    data = {
        "reOrderId": reorderId,
        "newReverseTime": timestamp_end,
        "updateReason": "测试预约订单"
    }
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)
    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }
    with allure.step("1. 点击修改预约时间"):
        url = PROJCET_URL_WORKER + "/order/updateReverseTime"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-订单详情")
def test_getOrderDetail2():
    global reverseTime
    data = {
        "maintainOrderId": maintainOrderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)
    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 订单详情"):
        url = PROJCET_URL_WORKER + "/order/getOrderDetail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        reverseTime = ak.get_text(r1.text, "$.data.reverseTime")
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("客服后台-订单列表-校验预约时间")
def test_order_list():
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
    with allure.step("1. 查看全部订单列表"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 校验预约时间是否正确"):
        reserveTime = ak.get_text(r1.text, "$.data.orderList[0].reserveTime")
        assert reverseTime == reserveTime
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-已到达")
def test_arrive():
    data = {
        "lng": LAN,
        "lat": LAT,
        "maintainOrderId": maintainOrderId,
        "repairOrderId": reorderId
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 点击已到达"):
        url = PROJCET_URL_WORKER + "/order/arrive"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("客服后台-校验普通单转为预约单")
@allure.title("维修工-完成订单")
def test_finishorder():
    data = {
        "maintainOrderId": maintainOrderId,
        "note": "测试使用"
    }
    timestamp = str(int(time.time() * 1000))
    signStr = sign(app_key, TOKEN_WEIXIU, platform, timestamp, data, secret)

    headers = {
        "AppKey": app_key,
        "Authorization": TOKEN_WEIXIU,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 滑动完成订单"):
        url = PROJCET_URL_WORKER + "/order/finishOrder"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)
