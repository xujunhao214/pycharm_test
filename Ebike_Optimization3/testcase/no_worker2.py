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

"""
该逻辑去掉，目前没有不接单就转派的逻辑，都是进入订单就直接接单
"""


@allure.epic("订单主流程-没有接单就转派")
@allure.title("微信小程序-创建订单")
def test_creat_order():
    global reorderId, ak
    ak = ApiKey()
    data = {
        "faultName": "链条掉落",
        "brandId": 8,
        "phone": "13207258888",
        "longitude": 113.946163,
        "latitude": 22.530835,
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "town": "粤海街道",
        "otherAddress": "科苑南路3172号留学生创业大厦"
    }
    signStr = sign(app_key, TOKEN_WeiXin, platform, timestamp, data, secret)

    headers = {
        "Authorization": TOKEN_WeiXin,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1.创建订单"):
        url = PROJCET_URL_Weixin + "/order/create-order"
        r1 = ak.post(url=url, json=data, headers=headers)
        results = ak.get_text(r1.text, "$.msg")
    with allure.step("2.结果校验"):
        assert "OK" == results
    with allure.step("3.获取订单id"):
        reorderId = ak.get_text(r1.text, "$.data.reOrderId")
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-首页")
def test_head():
    data = {

    }
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
    with allure.step("1.维修工首页"):
        url = PROJCET_URL_WORKER + "/home/head"
        r1 = ak.post(url=url, json=data, headers=headers)
        results = ak.get_text(r1.text, "$.msg")
    with allure.step("2.结果校验"):
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-首页订单列表")
def test_getNewOrderList():
    global maintainOrderId
    data = {

    }
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
    with allure.step("1. 维修工接单列表"):
        url = PROJCET_URL_WORKER + "/order/getNewOrderList"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取新的订单id"):
        maintainOrderId = ak.get_text(r1.text, "$.data.orderList[0].maintainOrderId")
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-订单详情")
def test_getOrderDetail():
    data = {
        "maintainOrderId": maintainOrderId
    }
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
    with allure.step("1. 订单详情"):
        url = PROJCET_URL_WORKER + "/order/getOrderDetail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-转派")
def test_resendOrder():
    data = {
        "maintainOrderId": maintainOrderId,
        "reasonDesc": "有事忙不过来",
        "isTrailer": 0
    }
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
    with allure.step("1. 转派订单"):
        url = PROJCET_URL_WORKER + "/order/resendOrder"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("客服后台-登录")
def test_auth_login():
    global token_auth
    data = {
        "userName": USERNAME,
        "password": PASSWD
    }
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


@allure.epic("订单主流程-没有接单就转派")
@allure.title("客服后台-全部订单列表")
def test_order_list():
    data = {
        "shopName": "",
        "status": 8,
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
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("客服后台-转派给维修工")
def test_order_designate():
    data = {
        "isTrailer": 0,
        "groupId": 1,
        "shopId": "18",
        "maintainerId": "6",
        "reOrderId": reorderId,
        "shopName": "徐俊豪的店铺",
        "rejectReason": "有事忙不过来"
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
    with allure.step("1. 转派给维修工"):
        url = PROJCET_URL + "/support/order/order-designate"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-首页")
def test_head2():
    data = {

    }
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
    with allure.step("1.维修工首页"):
        url = PROJCET_URL_WORKER + "/home/head"
        r1 = ak.post(url=url, json=data, headers=headers)
        results = ak.get_text(r1.text, "$.msg")
    with allure.step("2.结果校验"):
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-首页订单列表")
def test_getNewOrderList2():
    global maintainOrderId
    data = {

    }
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
    with allure.step("1. 维修工接单列表"):
        url = PROJCET_URL_WORKER + "/order/getNewOrderList"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
    with allure.step("3. 获取新的订单id"):
        maintainOrderId = ak.get_text(r1.text, "$.data.orderList[0].maintainOrderId")
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-订单详情")
def test_getOrderDetail2():
    data = {
        "maintainOrderId": maintainOrderId
    }
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
    with allure.step("1. 订单详情"):
        url = PROJCET_URL_WORKER + "/order/getOrderDetail"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-接单")
def test_confirmOrder():
    data = {
        "maintainOrderId": maintainOrderId
    }
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
    with allure.step("1. 点击接单"):
        url = PROJCET_URL_WORKER + "/order/confirmOrder"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-已到达")
def test_arrive():
    data = {
        "lng": 113.94602373161979,
        "lat": 22.530563651766531,
        "maintainOrderId": maintainOrderId,
        "repairOrderId": reorderId
    }
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

    with allure.step("1. 点击已到达"):
        url = PROJCET_URL_WORKER + "/order/arrive"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("维修工-完成订单")
def test_finishorder():
    data = {
        "maintainOrderId": maintainOrderId,
        "note": "测试使用"
    }

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

    with allure.step("1. 滑动完成订单"):
        url = PROJCET_URL_WORKER + "/order/finishOrder"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)


@allure.epic("订单主流程-没有接单就转派")
@allure.title("微信小程序-订单评价")
def test_evaluate_order():
    data = {
        "reOrderId": reorderId,
        "maintainerId": "140",
        "labels": ["服务好", "响应快"],
        "resSpeedScore": 4,
        "serAttitudeScore": 5,
        "serQualityScore": 4
    }

    signStr = sign(app_key, TOKEN_WeiXin, platform, timestamp, data, secret)

    headers = {
        "Authorization": TOKEN_WeiXin,
        "AppKey": app_key,
        "Platform": platform,
        "Timestamp": timestamp,   
        "Sign": signStr,
        "Content-Type": "application/json",
        "city": "0755"
    }

    with allure.step("1. 进行评价"):
        url = PROJCET_URL_Weixin + "/order/evaluate-order"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.msg")
        assert "OK" == results
        time.sleep(3)
