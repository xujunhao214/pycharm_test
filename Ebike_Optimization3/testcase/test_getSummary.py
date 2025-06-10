#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import allure
import pytest
import os
from Ebike_Optimization3.VAR.VAR import *
from Ebike_Optimization3.api_keyword.api_key import ApiKey
from Ebike_Optimization3.api_keyword.sign import sign


@allure.epic("维修工-今日订单统计校验")
@allure.title("维修工-订单统计")
def test_getSummary():
    global ak, finishedOrderCount, normalOrderCount, trailerOrderCount
    ak = ApiKey()
    data = {
        "range": "DAY"
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
    with allure.step("1.维修工今日订单统计界面"):
        url = PROJCET_URL_WORKER + "/order/getSummary"
        r1 = ak.post(url=url, json=data, headers=headers)
        results = ak.get_text(r1.text, "$.msg")
    with allure.step("2.结果校验"):
        assert "OK" == results
    with allure.step("3.获取今日完成订单总量"):
        finishedOrderCount = ak.get_text(r1.text, "$.data.statistics.finishedOrderCount")
    with allure.step("4.获取今日普通订单数量"):
        normalOrderCount = ak.get_text(r1.text, "$.data.statistics.finishedOrderTypeStatistics.normalOrderCount")
    with allure.step("5.获取今日拖车订单数量"):
        trailerOrderCount = ak.get_text(r1.text, "$.data.statistics.finishedOrderTypeStatistics.trailerOrderCount")
        time.sleep(3)


@allure.epic("维修工-今日订单统计校验")
@allure.title("客服后台-登录")
def test_auth_login():
    global token_auth
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


@allure.epic("维修工-今日订单统计校验")
@allure.title("全部订单-订单查询-今日全部订单")
def test_order_list():
    data = {
        "shopName": "",
        "status": 6,
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [timestamp_start, timestamp_end],
        "startTime": timestamp_start,
        "endTime": timestamp_end,
        "maintainerId": "6",
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
    with allure.step("1. 今日完成订单数量"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.total")
        assert results == finishedOrderCount
        time.sleep(3)


@allure.epic("维修工-今日订单统计校验")
@allure.title("全部订单-订单查询-今日拖车订单")
def test_order_list2():
    data = {
        "shopName": "",
        "status": 6,
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [timestamp_start, timestamp_end],
        "startTime": timestamp_start,
        "endTime": timestamp_end,
        "isTrailer": 1,
        "maintainerId": "6",
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
    with allure.step("1. 今日拖车订单数量"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.total")
        assert results == trailerOrderCount
        time.sleep(3)


@allure.epic("维修工-今日订单统计校验")
@allure.title("全部订单-订单查询-今日普通订单")
def test_order_list3():
    data = {
        "shopName": "",
        "status": 6,
        "faultName": "",
        "phone": "",
        "orderId": "",
        "time": [timestamp_start, timestamp_end],
        "startTime": timestamp_start,
        "endTime": timestamp_end,
        "isTrailer": 0,
        "maintainerId": "6",
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
    with allure.step("1. 今日普通订单数量"):
        url = PROJCET_URL + "/support/order/order-list"
        r1 = ak.post(url=url, json=data, headers=headers)
    with allure.step("2. 结果校验"):
        results = ak.get_text(r1.text, "$.data.total")
        assert results == normalOrderCount
        time.sleep(3)
